import math


class PathProcessingError(ValueError):
    pass


def _valid_point(value):
    try:
        if value is None or len(value) < 2:
            return None
        x, y = float(value[0]), float(value[1])
        return (x, y) if math.isfinite(x) and math.isfinite(y) else None
    except (TypeError, ValueError, OverflowError):
        return None


def clean_points(points, min_distance=0.0):
    if min_distance < 0:
        raise PathProcessingError("最小点间距不能为负数")
    result = []
    for raw in points or []:
        point = _valid_point(raw)
        if point is None:
            continue
        if result and math.dist(result[-1], point) <= max(min_distance, 1e-12):
            continue
        result.append(point)
    return result


def smooth_points(points, strength=0.3, closed=False):
    points = list(points)
    if not 0 <= strength <= 1:
        raise PathProcessingError("平滑程度必须位于 0 到 1 之间")
    if len(points) < 3 or strength == 0:
        return points
    passes = max(1, int(round(strength * 5)))
    current = points
    for _ in range(passes):
        updated = []
        for i, point in enumerate(current):
            if not closed and i in (0, len(current) - 1):
                updated.append(point)
                continue
            prev = current[(i - 1) % len(current)]
            nxt = current[(i + 1) % len(current)]
            weight = min(0.45, strength * 0.45)
            updated.append(((1 - 2 * weight) * point[0] + weight * (prev[0] + nxt[0]),
                            (1 - 2 * weight) * point[1] + weight * (prev[1] + nxt[1])))
        current = updated
    return current


def _segments(points, closed):
    count = len(points) if closed else len(points) - 1
    return [(points[i], points[(i + 1) % len(points)]) for i in range(count)]


def resample_points(points, spacing, closed=False):
    points = list(points)
    if spacing <= 0:
        raise PathProcessingError("采样间距必须大于 0")
    if len(points) < 2:
        return points
    segments = _segments(points, closed)
    lengths = [math.dist(a, b) for a, b in segments]
    total = sum(lengths)
    if total <= 1e-9:
        return points[:1]
    sample_count = max(3 if closed else 2, int(round(total / spacing)))
    distances = [i * total / sample_count for i in range(sample_count)] if closed else [i * total / (sample_count - 1) for i in range(sample_count)]
    result, seg_index, consumed = [], 0, 0.0
    for target in distances:
        while seg_index < len(segments) - 1 and consumed + lengths[seg_index] < target:
            consumed += lengths[seg_index]
            seg_index += 1
        a, b = segments[seg_index]
        length = lengths[seg_index]
        t = 0.0 if length <= 1e-12 else (target - consumed) / length
        result.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return result


def process_path(points, min_distance=1.0, smoothing=0.3, spacing=2.0, closed=False):
    cleaned = clean_points(points, min_distance)
    if len(cleaned) < 2:
        raise PathProcessingError("路径至少需要两个有效且不同的点")
    smoothed = smooth_points(cleaned, smoothing, closed)
    sampled = resample_points(smoothed, spacing, closed)
    if len(sampled) < (3 if closed else 2):
        raise PathProcessingError("路径过短，无法生成有效赛道")
    return sampled
