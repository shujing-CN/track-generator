import math


EPSILON = 1e-8


class TrackGeometryError(ValueError):
    pass


def _clean(points):
    result = []
    for point in points or []:
        try:
            value = (float(point[0]), float(point[1]))
        except (TypeError, ValueError, IndexError):
            continue
        if all(math.isfinite(v) for v in value):
            if not result or math.dist(result[-1], value) > EPSILON:
                result.append(value)
    return result


def _orientation(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _segments_intersect(a, b, c, d):
    return (_orientation(a, b, c) * _orientation(a, b, d) < -EPSILON and
            _orientation(c, d, a) * _orientation(c, d, b) < -EPSILON)


def self_intersection_indices(points, closed=False):
    count = len(points) if closed else len(points) - 1
    bad = []
    for i in range(count):
        a, b = points[i], points[(i + 1) % len(points)]
        for j in range(i + 1, count):
            if j == i + 1 or (closed and i == 0 and j == count - 1):
                continue
            c, d = points[j], points[(j + 1) % len(points)]
            if _segments_intersect(a, b, c, d):
                bad.append((i, j))
    return bad


def _turn_degrees(a, b, c):
    incoming = (b[0] - a[0], b[1] - a[1])
    outgoing = (c[0] - b[0], c[1] - b[1])
    li, lo = math.hypot(*incoming), math.hypot(*outgoing)
    if min(li, lo) <= EPSILON:
        return 180.0
    cosine = max(-1.0, min(1.0, (incoming[0] * outgoing[0] + incoming[1] * outgoing[1]) / (li * lo)))
    return math.degrees(math.acos(cosine))


def extreme_turn_indices(points, closed=False, threshold=170.0):
    result = []
    for i in range(len(points)):
        if not closed and i in (0, len(points) - 1):
            continue
        if _turn_degrees(points[(i - 1) % len(points)], points[i], points[(i + 1) % len(points)]) >= threshold:
            result.append(i)
    return result


def sharp_turn_indices(points, width, closed=False):
    result = []
    for i in range(len(points)):
        if not closed and i in (0, len(points) - 1):
            continue
        angle = _turn_degrees(points[(i - 1) % len(points)], points[i], points[(i + 1) % len(points)])
        if angle > 100:
            adjacent = min(math.dist(points[(i - 1) % len(points)], points[i]),
                           math.dist(points[i], points[(i + 1) % len(points)]))
            radius = adjacent / max(2 * math.sin(math.radians(angle / 2)), EPSILON)
            if width / 2 > radius * 0.9:
                result.append(i)
    return result


def _local_half_widths(points, width, closed):
    half = width / 2.0
    values = []
    for i in range(len(points)):
        if not closed and i in (0, len(points) - 1):
            values.append(half)
            continue
        prev, point, nxt = points[(i - 1) % len(points)], points[i], points[(i + 1) % len(points)]
        angle = _turn_degrees(prev, point, nxt)
        if angle <= 45:
            values.append(half)
            continue
        adjacent = min(math.dist(prev, point), math.dist(point, nxt))
        radius = adjacent / max(2 * math.sin(math.radians(angle / 2)), EPSILON)
        values.append(max(width * 0.1, min(half, radius * 0.8)))
    return values


def _face_area(vertices, face):
    area = 0.0
    for i, index in enumerate(face):
        x1, y1, _ = vertices[index]
        x2, y2, _ = vertices[face[(i + 1) % len(face)]]
        area += x1 * y2 - x2 * y1
    return area / 2.0


def mesh_quality_issues(vertices, faces, surface_face_count, closed=False):
    issues = []
    signs = []
    for index, face in enumerate(faces[:surface_face_count]):
        area = _face_area(vertices, face)
        if abs(area) <= EPSILON:
            issues.append("surface face {} has zero area".format(index + 1))
        else:
            signs.append(1 if area > 0 else -1)
    if signs and any(sign != signs[0] for sign in signs[1:]):
        issues.append("surface has flipped local faces")
    point_count = surface_face_count if closed else surface_face_count + 1
    for side, name in ((0, "left boundary"), (1, "right boundary")):
        boundary = [(vertices[2*i+side][0], vertices[2*i+side][1]) for i in range(point_count)]
        if self_intersection_indices(boundary, closed):
            issues.append("{} crosses itself".format(name))
    for i in range(surface_face_count):
        j = (i + 1) % point_count
        if _segments_intersect(vertices[2*i], vertices[2*j], vertices[2*i+1], vertices[2*j+1]):
            issues.append("surface face {} has crossing side edges".format(i + 1))
    return issues


def build_track_mesh_data(points, width, height=.1, thickness=0.0, closed=False):
    points = _clean(points)
    if width <= 0:
        raise TrackGeometryError("track width must be positive")
    if len(points) < (3 if closed else 2):
        raise TrackGeometryError("path is too short to build a road mesh")
    crossings = self_intersection_indices(points, closed)
    if crossings:
        raise TrackGeometryError("path self-intersects at segments {} and {}".format(crossings[0][0] + 1, crossings[0][1] + 1))
    folds = extreme_turn_indices(points, closed)
    if folds:
        raise TrackGeometryError("path has an extreme fold near sample {}".format(folds[0] + 1))

    half_widths = _local_half_widths(points, width, closed)
    pairs = []
    for i, point in enumerate(points):
        if closed:
            prev, nxt = points[(i - 1) % len(points)], points[(i + 1) % len(points)]
        elif i == 0:
            prev, nxt = point, points[1]
        elif i == len(points) - 1:
            prev, nxt = points[-2], point
        else:
            prev, nxt = points[i - 1], points[i + 1]
        dx, dy = nxt[0] - prev[0], nxt[1] - prev[1]
        length = math.hypot(dx, dy)
        if length <= EPSILON:
            raise TrackGeometryError("path contains a zero-length tangent")
        nx, ny = -dy / length, dx / length
        half = half_widths[i]
        pairs.append(((point[0] + nx * half, point[1] + ny * half, height),
                      (point[0] - nx * half, point[1] - ny * half, height)))

    vertices = [vertex for pair in pairs for vertex in pair]
    faces = []
    count = len(points) if closed else len(points) - 1
    for i in range(count):
        j = (i + 1) % len(points)
        faces.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    issues = mesh_quality_issues(vertices, faces, count, closed)
    if issues:
        raise TrackGeometryError("road mesh quality check failed: {}".format("; ".join(issues)))

    if thickness > 0:
        top_count = len(vertices)
        vertices += [(x, y, z - thickness) for x, y, z in vertices]
        faces += [tuple(top_count + i for i in reversed(face)) for face in faces[:count]]
        for i in range(count):
            j = (i + 1) % len(points)
            faces.extend([(2*i, 2*i+top_count, 2*j+top_count, 2*j),
                          (2*i+1, 2*j+1, 2*j+1+top_count, 2*i+1+top_count)])
        if not closed:
            last = 2 * len(points) - 2
            faces.extend([(0, 1, 1+top_count, top_count),
                          (last, last+top_count, last+1+top_count, last+1)])
    return vertices, faces


def build_track_with_recovery(points, width, height=.1, thickness=0.0, closed=False, retries=8):
    from processing.path_processing import chaikin_smooth, resample_points
    current = _clean(points)
    lengths = [math.dist(current[i], current[(i+1) % len(current)]) for i in range(len(current) if closed else len(current)-1)]
    spacing = max(EPSILON * 10, sum(lengths) / max(1, len(lengths)))
    effective_width = width
    for attempt in range(retries + 1):
        try:
            vertices, faces = build_track_mesh_data(current, effective_width, height, thickness, closed)
            return current, vertices, faces
        except TrackGeometryError:
            if attempt >= retries:
                raise
            current = resample_points(chaikin_smooth(current, 1, closed), spacing, closed)
            effective_width *= 0.6
    raise TrackGeometryError("road mesh recovery failed")


def _active_curb_segments(points, closed):
    count = len(points) if closed else len(points) - 1
    turns = []
    for i in range(len(points)):
        if not closed and i in (0, len(points) - 1):
            turns.append(False)
            continue
        angle = _turn_degrees(points[(i - 1) % len(points)], points[i], points[(i + 1) % len(points)])
        turns.append(angle >= 3.0)
    active = [turns[i] or turns[(i + 1) % len(points)] for i in range(count)]
    return [value or (i > 0 and active[i - 1]) or (i + 1 < count and active[i + 1]) for i, value in enumerate(active)]


def _add_prism(vertices, faces, top, thickness):
    bottom = [(x, y, z - thickness) for x, y, z in top]
    base = len(vertices)
    vertices.extend(top + bottom)
    faces.extend([(base, base+1, base+2, base+3), (base+7, base+6, base+5, base+4),
                  (base, base+4, base+5, base+1), (base+1, base+5, base+6, base+2),
                  (base+2, base+6, base+7, base+3), (base+3, base+7, base+4, base)])


def build_turn_curb_meshes(points, track_width, curb_width=None, height=.12, closed=False, thickness=.12):
    points = _clean(points)
    if len(points) < (3 if closed else 4):
        return (([], []), ([], []))
    road_vertices, _ = build_track_mesh_data(points, track_width, height, 0.0, closed)
    return build_turn_curbs_from_track_mesh(points, road_vertices, curb_width or max(track_width * .12, .25), height, closed, thickness)


def build_turn_curbs_from_track_mesh(points, track_vertices, curb_width=None, height=.13, closed=False, thickness=.18):
    points = _clean(points)
    if len(points) < (3 if closed else 4):
        return (([], []), ([], []))
    curb_width = curb_width if curb_width is not None else .5
    red_vertices, red_faces, white_vertices, white_faces = [], [], [], []
    count = len(points) if closed else len(points) - 1
    active = _active_curb_segments(points, closed)
    stripe = 0
    for i in range(count):
        if not active[i]:
            continue
        j = (i + 1) % len(points)
        vertices, faces = (red_vertices, red_faces) if stripe % 2 == 0 else (white_vertices, white_faces)
        for side_index in (0, 1):
            p0, p1 = points[i], points[j]
            edge0 = track_vertices[2*i + side_index]
            edge1 = track_vertices[2*j + side_index]
            out0 = (edge0[0] - p0[0], edge0[1] - p0[1])
            out1 = (edge1[0] - p1[0], edge1[1] - p1[1])
            len0, len1 = math.hypot(*out0), math.hypot(*out1)
            if min(len0, len1) <= EPSILON:
                continue
            outer0 = (edge0[0] + out0[0] / len0 * curb_width, edge0[1] + out0[1] / len0 * curb_width, height)
            outer1 = (edge1[0] + out1[0] / len1 * curb_width, edge1[1] + out1[1] / len1 * curb_width, height)
            top = [(edge0[0], edge0[1], height), (edge1[0], edge1[1], height), outer1, outer0]
            _add_prism(vertices, faces, top, thickness)
        stripe += 1
    return ((red_vertices, red_faces), (white_vertices, white_faces))
