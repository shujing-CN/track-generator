import colorsys
from collections import deque
from PIL import Image
from .skeleton_processing import thin, trace_outer_contour
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

def auto_target_color(image):
    rgb = image.convert("RGB"); rgb.thumbnail((128,128))
    colors = rgb.quantize(colors=8).convert("RGB").getcolors(rgb.width*rgb.height) or []
    colors.sort(reverse=True)
    if len(colors) < 2: raise ValueError("no target line found")
    background = colors[0][1]
    candidates = [(count*_distance(color, background), color) for count, color in colors[1:]]
    if not candidates or max(candidates)[0] <= 0: raise ValueError("no target line found")
    return max(candidates)[1]

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

def extract_ordered_path(image, target_color=None, tolerance=.25):
    color=target_color or auto_target_color(image)
    mask=None; last_error=None
    attempts=[]; value=float(tolerance)
    while value<=min(1.0,float(tolerance)+.45)+1e-9:
        attempts.append(round(value,4)); candidate=segment_by_color(image,color,value)
        parts=connected_components(candidate); foreground=sum(len(part) for part in parts)
        dominant=bool(parts) and (len(parts)==1 or len(parts[1])<len(parts[0])*.20)
        not_background=foreground<image.width*image.height*.35
        if dominant and not_background:
            mask=[[p for p in row] for row in candidate]; break
        try: mask=largest_component(candidate); break
        except ValueError as exc: last_error=exc
        value+=.10
    if mask is None: raise last_error or ValueError("no target line found")
    mask=largest_component(mask)
    skeleton=thin(mask)
    try: points,closed=order_mask_path(skeleton)
    except PathOrderingError as exc:
        if "branched" not in str(exc): raise
        cycle=prune_to_cycle(skeleton)
        try: points,closed=order_mask_path(cycle)
        except PathOrderingError:
            if sum(map(sum,cycle))<12: raise exc
            points=trace_outer_contour(mask); closed=True
    return points,closed,mask,color

def mask_preview(image, mask):
    base=image.convert("RGBA"); overlay=Image.new("RGBA",base.size,(0,0,0,0)); px=overlay.load()
    for y,row in enumerate(mask):
        for x,v in enumerate(row):
            if v: px[x,y]=(255,40,40,150)
    return Image.alpha_composite(base,overlay)
