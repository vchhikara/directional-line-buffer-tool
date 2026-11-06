"""Real PyQGIS integration tests. Requires QGIS Python and Qt headless/GUI setup.

Run with QGIS's Python, e.g. `QT_QPA_PLATFORM=offscreen python3 -m unittest
...`. Passing mock tests is NOT a substitute for these real integration tests.
"""

import importlib.util
import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
HAS_QGIS = importlib.util.find_spec('qgis') is not None


@unittest.skipUnless(HAS_QGIS, 'Real QGIS Python bindings unavailable')
class RealQgisIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from qgis.core import QgsApplication
        cls.app = QgsApplication([], True)
        cls.app.initQgis()

    @classmethod
    def tearDownClass(cls):
        cls.app.exitQgis()

    def test_geometry_orientation_and_area(self):
        from qgis.core import QgsGeometry, QgsPointXY, Qgis
        line = QgsGeometry.fromPolylineXY([QgsPointXY(0, 0), QgsPointXY(10, 0)])
        left = line.singleSidedBuffer(2, 12, Qgis.BufferSide.Left, Qgis.JoinStyle.Miter, 5.0)
        right = line.singleSidedBuffer(2, 12, Qgis.BufferSide.Right, Qgis.JoinStyle.Miter, 5.0)
        self.assertTrue(left.isGeosValid())
        self.assertTrue(right.isGeosValid())
        self.assertAlmostEqual(left.area(), 20, delta=0.001)
        self.assertAlmostEqual(right.area(), 20, delta=0.001)
        self.assertGreater(left.boundingBox().yMinimum(), -0.001)
        self.assertLess(right.boundingBox().yMaximum(), 0.001)
        self.assertTrue(line.buffer(2, 12).isGeosValid())

    def test_reversed_direction_swaps_side(self):
        from qgis.core import QgsGeometry, QgsPointXY, Qgis
        line = QgsGeometry.fromPolylineXY([QgsPointXY(10, 0), QgsPointXY(0, 0)])
        left = line.singleSidedBuffer(2, 12, Qgis.BufferSide.Left, Qgis.JoinStyle.Miter, 5.0)
        self.assertLess(left.boundingBox().yMaximum(), 0.001)

    def test_actual_plugin_ui_lifecycle_and_memory_output(self):
        from qgis.PyQt.QtWidgets import QMainWindow
        from qgis.core import QgsProject, QgsCoordinateReferenceSystem
        from qgis.gui import QgsMapCanvas
        from Directional_line_buffer_Tool import classFactory
        from Directional_line_buffer_Tool.map_tool import DirectionalBufferMapTool

        project = QgsProject.instance()
        previous_crs = project.crs()
        project.setCrs(QgsCoordinateReferenceSystem('EPSG:32643'))
        window = QMainWindow()
        canvas = QgsMapCanvas()
        canvas.setDestinationCrs(project.crs())

        class I:
            def __init__(self):
                self.actions = []
                self.toolbar = []

            def mapCanvas(self):
                return canvas

            def mainWindow(self):
                return window

            def activeLayer(self):
                return None

            def addPluginToMenu(self, _name, action):
                self.actions.append(action)

            def removePluginMenu(self, _name, action):
                self.actions.remove(action)

            def addToolBarIcon(self, action):
                self.toolbar.append(action)

            def removeToolBarIcon(self, action):
                self.toolbar.remove(action)

        iface = I()
        try:
            plugin = classFactory(iface)
            plugin.initGui()
            self.assertEqual(len(iface.actions), 2)
            plugin.initGui()
            self.assertEqual(len(iface.actions), 2)
            tool = DirectionalBufferMapTool(iface, 2, 'left')
            canvas.setMapTool(tool)
            layer = tool.temp_layer()
            self.assertTrue(layer.isValid())
            self.assertEqual(len(layer.fields()), 2)
            self.assertIs(tool.temp_layer(), layer)
            plugin.map_tool = tool
            plugin.unload()
            self.assertEqual(iface.actions, [])
            self.assertEqual(iface.toolbar, [])
            self.assertNotEqual(canvas.mapTool(), tool)
            # Separate reload, same QGIS process.
            plugin2 = classFactory(iface)
            plugin2.initGui()
            self.assertEqual(len(iface.actions), 2)
            plugin2.unload()
            project.removeMapLayer(layer.id())
        finally:
            project.setCrs(previous_crs)
            canvas.close()
            window.close()


if __name__ == '__main__':
    unittest.main()
