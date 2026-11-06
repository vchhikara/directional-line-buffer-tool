import math
import unittest

from Directional_line_buffer_Tool.validation import normalized_points, validate_parameters


class Point:
    def __init__(self, x, y):
        self._x, self._y = x, y

    def x(self):
        return self._x

    def y(self):
        return self._y


class ValidationTests(unittest.TestCase):
    def test_valid_sides(self):
        for side in ('left', 'right', 'both'):
            with self.subTest(side=side):
                validate_parameters(1.5, side)

    def test_positive_distances(self):
        for distance in (0.01, 10, 1_000_000):
            with self.subTest(distance=distance):
                validate_parameters(distance, 'left')

    def test_invalid_distances(self):
        for distance in (0, -1, float('nan'), float('inf'), -float('inf'), None, '10', True):
            with self.subTest(distance=repr(distance)):
                with self.assertRaises(ValueError):
                    validate_parameters(distance, 'both')

    def test_invalid_sides(self):
        for side in ('center', '', None, 'LEFT'):
            with self.subTest(side=repr(side)):
                with self.assertRaises(ValueError):
                    validate_parameters(10, side)

    def test_two_distinct_points_accepted(self):
        self.assertEqual(len(normalized_points([Point(0, 0), Point(0, 1)])), 2)

    def test_duplicate_first_click_rejected(self):
        with self.assertRaises(ValueError):
            normalized_points([Point(1, 2), Point(1, 2)])

    def test_adjacent_duplicate_removed(self):
        points = [Point(0, 0), Point(0, 0), Point(1, 0), Point(1, 0), Point(2, 0)]
        cleaned = normalized_points(points)
        self.assertEqual(len(cleaned), 3)
        self.assertIs(cleaned[0], points[0])
        self.assertIs(cleaned[1], points[2])

    def test_preserves_direction(self):
        pts = [Point(4, 3), Point(2, 3), Point(0, 3)]
        cleaned = normalized_points(pts)
        self.assertEqual([(p.x(), p.y()) for p in cleaned], [(4, 3), (2, 3), (0, 3)])

    def test_closed_nontrivial_path_allowed(self):
        cleaned = normalized_points([Point(0, 0), Point(10, 0), Point(0, 0)])
        self.assertEqual(len(cleaned), 3)

    def test_empty_and_single_input_rejected(self):
        for points in ([], [Point(0, 0)]):
            with self.assertRaises(ValueError):
                normalized_points(points)

    def test_nonfinite_coordinates_rejected(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.assertRaises(ValueError):
                normalized_points([Point(0, 0), Point(value, 1)])

    def test_bad_point_object_rejected(self):
        with self.assertRaises(ValueError):
            normalized_points([Point(0, 0), (1, 2)])


if __name__ == '__main__':
    unittest.main()
