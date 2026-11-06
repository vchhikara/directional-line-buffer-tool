"""QGIS-independent validation for digitized buffer inputs."""

import math

VALID_SIDES = frozenset(('left', 'right', 'both'))


def validate_parameters(distance, side):
    """Reject invalid distances and unknown direction codes."""
    if isinstance(distance, bool) or not isinstance(distance, (int, float)):
        raise ValueError('Buffer distance must be a number in meters.')
    if not math.isfinite(distance) or distance <= 0:
        raise ValueError('Buffer distance must be finite and greater than zero.')
    if side not in VALID_SIDES:
        raise ValueError('Buffer side must be left, right, or both.')


def normalized_points(points):
    """Drop consecutive duplicates and require two distinct finite vertices.

    Points are native ``QgsPointXY`` objects when called by QGIS. Objects with
    ``x()`` and ``y()`` methods are accepted for independent tests.
    """
    result = []
    last_xy = None
    for point in points:
        try:
            xy = (float(point.x()), float(point.y()))
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError('Digitized coordinates are not valid points.') from exc
        if not all(math.isfinite(value) for value in xy):
            raise ValueError('Digitized points must have finite coordinates.')
        if xy != last_xy:
            result.append(point)
            last_xy = xy
    if len(result) < 2:
        raise ValueError('Draw at least two different points before finishing.')
    return result
