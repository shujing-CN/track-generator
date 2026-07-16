def thin(mask):
    image = [[1 if v else 0 for v in row] for row in mask]
    if not image: return image
    h, w = len(image), len(image[0])
    if any(len(row) != w for row in image): raise ValueError("mask must be rectangular")
    changed = True
    while changed:
        changed = False
        for phase in (0, 1):
            remove = []
            for y in range(1, h - 1):
                for x in range(1, w - 1):
                    if not image[y][x]: continue
                    p = [image[y-1][x], image[y-1][x+1], image[y][x+1], image[y+1][x+1], image[y+1][x], image[y+1][x-1], image[y][x-1], image[y-1][x-1]]
                    transitions = sum(not p[i] and p[(i + 1) % 8] for i in range(8))
                    if not (2 <= sum(p) <= 6 and transitions == 1): continue
                    ok = (not p[0]*p[2]*p[4] and not p[2]*p[4]*p[6]) if phase == 0 else (not p[0]*p[2]*p[6] and not p[0]*p[4]*p[6])
                    if ok: remove.append((x, y))
            for x, y in remove: image[y][x] = 0
            changed |= bool(remove)
    return [[bool(v) for v in row] for row in image]

def prune_to_cycle(mask):
    """Return the 2-core of a skeleton, removing anti-alias spur branches."""
    pixels={(x,y) for y,row in enumerate(mask) for x,value in enumerate(row) if value}
    def neighbors(point):
        x,y=point; result=set()
        for dx,dy in ((0,-1),(1,0),(0,1),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)):
            q=(x+dx,y+dy)
            if q not in pixels: continue
            if dx and dy and ((x+dx,y) in pixels or (x,y+dy) in pixels): continue
            result.add(q)
        return result
    changed=True
    while changed and pixels:
        remove={p for p in pixels if len(neighbors(p))<=1}
        changed=bool(remove); pixels-=remove
    h=len(mask); w=len(mask[0]) if h else 0
    return [[(x,y) in pixels for x in range(w)] for y in range(h)]

def longest_skeleton_path(mask):
    """Return the longest useful center path in a possibly branched skeleton.

    Uneven-width hand drawn or image-derived strokes often create small side
    branches after thinning.  For track generation we only need the intended
    main shape, so this extracts the graph diameter instead of rejecting the
    whole path as branched.
    """
    pixels={(x,y) for y,row in enumerate(mask) for x,value in enumerate(row) if value}
    if len(pixels)<2: raise ValueError("path is too short")
    def neighbors(point):
        x,y=point; result=set()
        for dx,dy in ((0,-1),(1,0),(0,1),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)):
            q=(x+dx,y+dy)
            if q not in pixels: continue
            if dx and dy and ((x+dx,y) in pixels or (x,y+dy) in pixels): continue
            result.add(q)
        return result
    graph={p:neighbors(p) for p in pixels}
    def bfs(start):
        queue=[start]; parent={start:None}; distance={start:0}
        for point in queue:
            for nxt in sorted(graph[point]):
                if nxt in parent: continue
                parent[nxt]=point; distance[nxt]=distance[point]+1; queue.append(nxt)
        farthest=max(distance,key=lambda p:(distance[p],-p[1],-p[0]))
        return farthest,parent,distance
    endpoints=[p for p,adjacent in graph.items() if len(adjacent)<=1]
    starts=endpoints or list(pixels)
    best_path=[]
    for start in starts:
        far,parent,distance=bfs(start)
        path=[]; current=far
        while current is not None:
            path.append(current); current=parent[current]
        if len(path)>len(best_path): best_path=path
    if len(best_path)<2: raise ValueError("could not extract a main path")
    return list(reversed(best_path))

def trace_outer_contour(mask):
    """Moore-neighbor tracing of a connected mask's outer boundary."""
    pixels={(x,y) for y,row in enumerate(mask) for x,value in enumerate(row) if value}
    if not pixels: raise ValueError("掩膜中没有可追踪区域")
    start=min(pixels,key=lambda p:(p[1],p[0])); current=start; back=(start[0]-1,start[1])
    directions=[(-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)]
    contour=[]; first_next=None; limit=max(100,len(pixels)*4)
    for _ in range(limit):
        contour.append(current)
        relative=(back[0]-current[0],back[1]-current[1])
        try: begin=directions.index(relative)
        except ValueError: begin=7
        found=None
        for step in range(1,9):
            index=(begin+step)%8; dx,dy=directions[index]; candidate=(current[0]+dx,current[1]+dy)
            if candidate in pixels:
                prev_index=(index-1)%8; pdx,pdy=directions[prev_index]
                new_back=(current[0]+pdx,current[1]+pdy); found=(candidate,new_back); break
        if found is None: break
        nxt,new_back=found
        if first_next is None: first_next=nxt
        elif current==start and nxt==first_next: contour.pop(); break
        back,current=new_back,nxt
    if len(contour)<3: raise ValueError("目标线外轮廓过短")
    return contour
