import unittest
try:
    from shapely.geometry import LineString
except Exception:
    LineString = None

class GeometrySimplifyTest(unittest.TestCase):
    def test_simplify_non_empty(self):
        if LineString is None:
            self.skipTest('shapely not installed')
        ls = LineString([(0,0),(0.0005,0.0005),(0.001,0.001)])
        simplified = ls.simplify(0.002, preserve_topology=False)
        self.assertTrue(len(simplified.coords) >= 2)

if __name__ == '__main__':
    unittest.main()
