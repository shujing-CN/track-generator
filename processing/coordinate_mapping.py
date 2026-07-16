def map_points_to_world(points, source_width, source_height, map_width, map_length, margin=0.05, fit_to_points=False):
    if any(float(v) <= 0 for v in (source_width, source_height, map_width, map_length)):
        raise ValueError("dimensions must be positive")
    if not 0 <= margin < 0.5:
        raise ValueError("margin must be in [0, 0.5)")
    if not points:
        return []
    if fit_to_points:
        xs=[float(point[0]) for point in points]; ys=[float(point[1]) for point in points]
        min_x,max_x=min(xs),max(xs); min_y,max_y=min(ys),max(ys)
        span_x=max_x-min_x; span_y=max_y-min_y
        if span_x<=1e-9 and span_y<=1e-9:
            return [(0.0,0.0) for _ in points]
        available_width=map_width*(1-2*margin)
        available_length=map_length*(1-2*margin)
        scales=[]
        if span_x>1e-9: scales.append(available_width/span_x)
        if span_y>1e-9: scales.append(available_length/span_y)
        scale=min(scales)
        center_x=(min_x+max_x)/2.0; center_y=(min_y+max_y)/2.0
        return [((float(x)-center_x)*scale,(center_y-float(y))*scale) for x,y in points]
    scale = min(map_width * (1 - 2 * margin) / source_width,
                map_length * (1 - 2 * margin) / source_height)
    width, length = source_width * scale, source_height * scale
    return [(-width / 2 + x * scale, length / 2 - y * scale) for x, y in points]
