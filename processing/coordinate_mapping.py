def map_points_to_world(points, source_width, source_height, map_width, map_length, margin=0.05):
    if any(float(v) <= 0 for v in (source_width, source_height, map_width, map_length)):
        raise ValueError("dimensions must be positive")
    if not 0 <= margin < 0.5:
        raise ValueError("margin must be in [0, 0.5)")
    if not points:
        return []
    scale = min(map_width * (1 - 2 * margin) / source_width,
                map_length * (1 - 2 * margin) / source_height)
    width, length = source_width * scale, source_height * scale
    return [(-width / 2 + x * scale, length / 2 - y * scale) for x, y in points]
