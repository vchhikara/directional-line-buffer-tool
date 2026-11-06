"""Independent GEOS/Shapely reference expectations, NOT QGIS integration tests.

Optional Shapely is a dev-only test dependency and is never imported by plugin.
"""

import unittest

try:
    from shapely.geometry import LineString
except ImportError:
    LineString = None


@unittest.skipUnless(LineString is not None, 'Optional Shapely reference library unavailable')
class GeosReferenceTests(unittest.TestCase):
    def test_left_north_for_eastward_line(self):
        line = LineString([(0, 0), (10, 0)])
        poly = line.buffer(2, single_sided=True, join_style=2, mitre_limit=5.0)
        self.assertTrue(poly.is_valid)
        self.assertEqual(poly.bounds, (0.0, 0.0, 10.0, 2.0))
        self.assertAlmostEqual(poly.area, 20)

    def test_right_south_for_eastward_line(self):
        line = LineString([(0, 0), (10, 0)])
        poly = line.buffer(-2, single_sided=True, join_style=2, mitre_limit=5.0)
        self.assertTrue(poly.is_valid)
        self.assertEqual(poly.bounds, (0.0, -2.0, 10.0, 0.0))
        self.assertAlmostEqual(poly.area, 20)

    def test_reversing_vertex_order_swaps_left(self):
        poly = LineString([(10, 0), (0, 0)]).buffer(2, single_sided=True)
        self.assertEqual(poly.bounds, (0.0, -2.0, 10.0, 0.0))

    def test_two_sided_area_approximation(self):
        poly = LineString([(0, 0), (10, 0)]).buffer(2, quad_segs=12)
        # Area is rectangle (40 m²) plus two semicircles (4π m²),
        # with a small approximation deficit from segmented arcs.
        self.assertGreater(poly.area, 52.4)
        self.assertLess(poly.area, 52.6)
        self.assertTrue(poly.is_valid)

    def test_corner_offset_is_valid(self):
        poly = LineString([(0, 0), (10, 0), (10, 10)]).buffer(
            2, single_sided=True, join_style=2, mitre_limit=5.0,
        )
        self.assertTrue(poly.is_valid)
        self.assertGreater(poly.area, 0)


if __name__ == '__main__':
    unittest.main()
