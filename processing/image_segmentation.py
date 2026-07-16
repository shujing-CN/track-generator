import colorsys
from collections import deque
from PIL import Image, ImageChops
from .skeleton_processing import thin, trace_outer_contour, longest_skeleton_path
from .path_ordering import order_mask_path, PathOrderingError
from .skeleton_processing import prune_to_cycle

SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp")

def _distance(a, b):
    ah = colorsys.rgb_to_hsv(*(v/255 for v in a[:3])); bh = colorsys.rgb_to_hsv(*(v/255 for v in b[:3]))
    dh = min(abs(ah[0]-bh[0]), 1-abs(ah[0]-bh[0])) * 2
    return ((dh*1.5)**2 + (ah[1]-bh[1])**2 + (ah[2]-bh[2])**2) ** .5

def segment_by_color(image, target_color, tolerance=.25):
    if not .01 <= tolerance <= 1.5: raise ValueError("color tolerance must be between 0.01 and 1.5")
    rgba = image.convert("RGBA"); px = rgba.load(); w, h = rgba.size
    return [[px[x,y][3] > 10 and _distance(px[x,y], target_color) <= tolerance for x in range(w)] for y in range(h)]

def _dominant_background_color(image):
    """Estimate the canvas colour without assuming that it is pure white."""
    rgba=image.convert("RGBA")
    sample=rgba.copy(); sample.thumbnail((160,160))
    opaque=Image.new("RGB",sample.size,(255,255,255))
    opaque.paste(sample.convert("RGB"),mask=sample.getchannel("A"))
    colors=opaque.quantize(colors=16).convert("RGB").getcolors(opaque.width*opaque.height) or []
    if not colors: return (255,255,255)
    return max(colors,key=lambda item:item[0])[1]

def _otsu_threshold(histogram):
    total=sum(histogram)
    if total<=0: return 0
    weighted=sum(index*count for index,count in enumerate(histogram))
    background_weight=0; background_sum=0.0; best_variance=-1.0; best=0
    for index,count in enumerate(histogram):
        background_weight+=count
        if background_weight>=total: break
        background_sum+=index*count
        foreground_weight=total-background_weight
        mean_background=background_sum/background_weight
        mean_foreground=(weighted-background_sum)/foreground_weight
        variance=background_weight*foreground_weight*(mean_background-mean_foreground)**2
        if variance>best_variance: best_variance=variance; best=index
    return best

def segment_foreground_auto(image):
    """Segment a line by contrast, not by one exact sampled colour."""
    rgba=image.convert("RGBA"); alpha=rgba.getchannel("A")
    transparent=sum(alpha.histogram()[:11])
    alpha_mask=alpha.point([0 if value<=10 else 255 for value in range(256)])
    if transparent>=rgba.width*rgba.height*.20:
        binary=alpha_mask
    else:
        rgb=rgba.convert("RGB"); background=_dominant_background_color(rgba)
        diff=ImageChops.difference(rgb,Image.new("RGB",rgb.size,background))
        red,green,blue=diff.split()
        contrast=ImageChops.lighter(red,ImageChops.lighter(green,blue))
        threshold=max(8,min(96,_otsu_threshold(contrast.histogram())))
        binary=contrast.point([0 if value<=threshold else 255 for value in range(256)])
        binary=ImageChops.multiply(binary,alpha_mask)
    data=list(binary.getdata()); width,height=binary.size
    return [[bool(value) for value in data[y*width:(y+1)*width]] for y in range(height)]

def auto_target_color(image):
    rgb = image.convert("RGB"); rgb.thumbnail((128,128))
    colors = rgb.quantize(colors=8).convert("RGB").getcolors(rgb.width*rgb.height) or []
    colors.sort(reverse=True)
    if len(colors) < 2: raise ValueError("no target line found")
    background = colors[0][1]
    candidates = [(count*_distance(color, background), color) for count, color in colors[1:]]
    if not candidates or max(candidates)[0] <= 0: raise ValueError("no target line found")
    return max(candidates)[1]

def _component_bounds(mask):
    points=[(x,y) for y,row in enumerate(mask) for x,value in enumerate(row) if value]
    if not points: return None
    xs=[point[0] for point in points]; ys=[point[1] for point in points]
    return min(xs),min(ys),max(xs),max(ys)

def _mask_matches_color(image, mask, target_color, tolerance):
    """Return True when a clicked colour plausibly belongs to an auto mask."""
    rgba=image.convert("RGBA"); pixels=rgba.load()
    coordinates=[(x,y) for y,row in enumerate(mask) for x,value in enumerate(row) if value]
    if not coordinates: return False
    step=max(1,len(coordinates)//512)
    distances=sorted(_distance(pixels[x,y],target_color) for x,y in coordinates[::step])
    representative=distances[max(0,int(len(distances)*.20)-1)]
    return representative<=max(.14,float(tolerance)*2.0)

def _manual_color_mask(image, target_color, tolerance):
    """Choose the most complete plausible component across wider tolerances."""
    best=None; best_score=-1
    value=max(.08,float(tolerance)); limit=min(1.0,value+.55)
    while value<=limit+1e-9:
        candidate=segment_by_color(image,target_color,value)
        try: component=largest_component(candidate)
        except ValueError:
            value+=.08; continue
        foreground=sum(map(sum,component))
        if foreground>=image.width*image.height*.40:
            value+=.08; continue
        bounds=_component_bounds(component)
        if bounds:
            span=(bounds[2]-bounds[0]+1)+(bounds[3]-bounds[1]+1)
            score=span*span+foreground
            if score>best_score: best,best_score=component,score
        value+=.08
    return best

def connected_components(mask):
    pixels = {(x,y) for y,row in enumerate(mask) for x,v in enumerate(row) if v}; parts=[]
    while pixels:
        start=pixels.pop(); part={start}; queue=deque([start])
        while queue:
            x,y=queue.popleft()
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)):
                q=(x+dx,y+dy)
                if q in pixels: pixels.remove(q); part.add(q); queue.append(q)
        parts.append(part)
    return sorted(parts,key=len,reverse=True)

def largest_component(mask):
    parts=connected_components(mask)
    if not parts: raise ValueError("no target line found")
    h,w=len(mask),len(mask[0])
    # Anti-aliased outlines and soft shadows often form secondary fragments.
    # Reject only when another region is comparable to the main line.
    if len(parts)>1 and len(parts[1]) >= max(3, len(parts[0])*.60):
        def bounds(part):
            xs=[p[0] for p in part]; ys=[p[1] for p in part]; return min(xs),min(ys),max(xs),max(ys)
        a,b=bounds(parts[0]),bounds(parts[1]); padding=max(3,int(min(w,h)*.08))
        halo=(b[0]>=a[0]-padding and b[1]>=a[1]-padding and b[2]<=a[2]+padding and b[3]<=a[3]+padding)
        if not halo: raise ValueError("multiple disconnected regions")
    return [[(x,y) in parts[0] for x in range(w)] for y in range(h)]

def mask_has_enclosed_hole(mask):
    h=len(mask); w=len(mask[0]) if h else 0
    if h<3 or w<3: return False
    outside=set(); queue=deque()
    for x in range(w):
        for y in (0,h-1):
            if not mask[y][x] and (x,y) not in outside:
                outside.add((x,y)); queue.append((x,y))
    for y in range(h):
        for x in (0,w-1):
            if not mask[y][x] and (x,y) not in outside:
                outside.add((x,y)); queue.append((x,y))
    while queue:
        x,y=queue.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            q=(x+dx,y+dy)
            if 0<=q[0]<w and 0<=q[1]<h and not mask[q[1]][q[0]] and q not in outside:
                outside.add(q); queue.append(q)
    for y in range(1,h-1):
        for x in range(1,w-1):
            if not mask[y][x] and (x,y) not in outside:
                return True
    return False

def extract_ordered_path(image, target_color=None, tolerance=.25):
    color=target_color or auto_target_color(image)
    automatic=largest_component(segment_foreground_auto(image))
    if target_color is None or _mask_matches_color(image,automatic,target_color,tolerance):
        mask=automatic
    else:
        mask=_manual_color_mask(image,target_color,tolerance)
        if mask is None:
            mask=automatic
    foreground=sum(map(sum,mask))
    if foreground<12: raise ValueError("未检测到足够长的赛道线条")
    if foreground>=image.width*image.height*.45: raise ValueError("前景覆盖过大，请使用背景更干净的赛道图片")
    skeleton=thin(mask)
    try: points,closed=order_mask_path(skeleton)
    except PathOrderingError as exc:
        cycle=prune_to_cycle(skeleton)
        try:
            points,closed=order_mask_path(cycle)
        except PathOrderingError:
            if mask_has_enclosed_hole(mask):
                points=trace_outer_contour(mask); closed=True
            else:
                try:
                    points=longest_skeleton_path(skeleton); closed=False
                except ValueError:
                    if sum(map(sum,cycle))<12 and "branched" not in str(exc): raise exc
                    points=trace_outer_contour(mask); closed=True
    return points,closed,mask,color

def mask_preview(image, mask):
    base=image.convert("RGBA"); overlay=Image.new("RGBA",base.size,(0,0,0,0)); px=overlay.load()
    for y,row in enumerate(mask):
        for x,v in enumerate(row):
            if v: px[x,y]=(255,40,40,150)
    return Image.alpha_composite(base,overlay)
