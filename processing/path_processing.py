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


def chaikin_smooth(points, rounds=3, closed=False):
    """Corner cutting that preserves open endpoints and smooths closed loops."""
    points = list(points)
    if rounds < 0:
        raise PathProcessingError("Chaikin 平滑轮数不能为负数")
    if len(points) < 3 or rounds == 0:
        return points
    current = points
    for _ in range(rounds):
        updated = [] if closed else [current[0]]
        count = len(current) if closed else len(current) - 1
        for i in range(count):
            a, b = current[i], current[(i + 1) % len(current)]
            updated.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            updated.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        if not closed:
            updated.append(current[-1])
        current = updated
    return current


def smooth_points(points, strength=0.3, closed=False):
    points = list(points)
    if not 0 <= strength <= 1:
        raise PathProcessingError("平滑程度必须位于 0 到 1 之间")
    if len(points) < 3 or strength == 0:
        return points
    rounds = max(2, min(4, int(round(2 + strength * 2))))
    return chaikin_smooth(points, rounds, closed)


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
    if not closed and result:
        result[0] = points[0]
        result[-1] = points[-1]
    return result


def remove_short_backtracks(points, max_segment, closed=False):
    """Remove tiny A-B-C reversals caused by skeleton/contour pixel artifacts."""
    result=list(points)
    if len(result)<3: return result
    for _ in range(len(result)):
        removed=False
        indices=range(len(result)) if closed else range(1,len(result)-1)
        for i in list(indices):
            a,b,c=result[(i-1)%len(result)],result[i],result[(i+1)%len(result)]
            u=(b[0]-a[0],b[1]-a[1]); v=(c[0]-b[0],c[1]-b[1]); lu=math.hypot(*u); lv=math.hypot(*v)
            if min(lu,lv)<=1e-12: result.pop(i); removed=True; break
            cosine=max(-1,min(1,(u[0]*v[0]+u[1]*v[1])/(lu*lv)))
            angle=math.degrees(math.acos(cosine))
            if angle>=165 and min(lu,lv)<=max_segment:
                result.pop(i); removed=True; break
        if not removed or len(result)<3: break
    return result


def process_path(points, min_distance=1.0, smoothing=0.3, spacing=2.0, closed=False):
    cleaned = clean_points(points, min_distance)
    cleaned = remove_short_backtracks(cleaned, max(spacing*2.0,min_distance*4.0), closed)
    if len(cleaned) < 2:
        raise PathProcessingError("路径至少需要两个有效且不同的点")
    # Sampling before smoothing makes mouse/image point density irrelevant.
    sampled_once = resample_points(cleaned, spacing, closed)
    smoothed = smooth_points(sampled_once, smoothing, closed)
    smoothed = clean_points(smoothed, 1e-9)
    sampled = resample_points(smoothed, spacing, closed)
    if len(sampled) < (3 if closed else 2):
        raise PathProcessingError("路径过短，无法生成有效赛道")
    return sampled
