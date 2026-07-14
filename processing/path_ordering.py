NEIGHBORS = [(x, y) for y in (-1, 0, 1) for x in (-1, 0, 1) if x or y]

class PathOrderingError(ValueError): pass

def order_mask_path(mask):
    pixels = {(x, y) for y, row in enumerate(mask) for x, v in enumerate(row) if v}
    if len(pixels) < 2: raise PathOrderingError("path is too short")
    graph = {}
    for p in pixels:
        adjacent=set()
        for dx,dy in NEIGHBORS:
            q=(p[0]+dx,p[1]+dy)
            if q not in pixels: continue
            # A diagonal is redundant when an orthogonal pixel already joins
            # the corner; keeping both creates degree-3 triangles in a valid line.
            if dx and dy and ((p[0]+dx,p[1]) in pixels or (p[0],p[1]+dy) in pixels): continue
            adjacent.add(q)
        graph[p]=adjacent
    seen, stack = set(), [next(iter(pixels))]
    while stack:
        p = stack.pop()
        if p not in seen: seen.add(p); stack.extend(graph[p] - seen)
    if seen != pixels: raise PathOrderingError("multiple disconnected regions")
    degrees = {p: len(v) for p, v in graph.items()}
    if any(v > 2 for v in degrees.values()): raise PathOrderingError("branched path")
    endpoints = sorted(p for p, v in degrees.items() if v == 1)
    closed = not endpoints and all(v == 2 for v in degrees.values())
    if not closed and len(endpoints) != 2: raise PathOrderingError("broken or unordered path")
    current, previous, ordered = (min(pixels) if closed else endpoints[0]), None, []
    while current is not None and current not in ordered:
        ordered.append(current)
        choices = sorted(graph[current] - ({previous} if previous else set()))
        nxt = next((p for p in choices if p not in ordered), None)
        previous, current = current, nxt
    if len(ordered) != len(pixels): raise PathOrderingError("could not order complete path")
    return ordered, closed
