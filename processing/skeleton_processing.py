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
