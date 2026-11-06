"""Contract tests using a deliberately minimal FAKE QGIS/Qt API.

These do NOT establish real QGIS compatibility. See test_qgis_runtime.py.
"""

from contextlib import contextmanager
import importlib
import sys
import types
import unittest
from unittest.mock import patch


class Signal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def disconnect(self, callback):
        self.callbacks.remove(callback)


class Action:
    def __init__(self, *args):
        self.triggered = Signal()
        self.deleted = False

    def setObjectName(self, *_):
        pass

    def setToolTip(self, *_):
        pass

    def setStatusTip(self, *_):
        pass

    def deleteLater(self):
        self.deleted = True


class CRS:
    def __init__(self, name='EPSG:32643', meters=True):
        self.name, self.meters = name, meters

    def __eq__(self, other):
        return isinstance(other, CRS) and self.name == other.name

    def isValid(self):
        return bool(self.name)

    def isGeographic(self):
        return not self.meters

    def mapUnits(self):
        return 0 if self.meters else 1


class Project:
    current = None

    def __init__(self):
        self.crs_value = CRS()
        self.layers = {}
        Project.current = self

    @staticmethod
    def instance():
        return Project.current

    def crs(self):
        return self.crs_value

    def mapLayers(self):
        return self.layers

    def mapLayer(self, layer_id):
        return self.layers.get(layer_id)

    def addMapLayer(self, layer):
        self.layers[layer.id()] = layer


class FakePoint:
    def __init__(self, point, y=None):
        self._x, self._y = (point.x(), point.y()) if y is None and hasattr(point, 'x') else (point, y)

    def x(self):
        return self._x

    def y(self):
        return self._y

    def __eq__(self, other):
        return hasattr(other, 'x') and self.x() == other.x() and self.y() == other.y()


class FakeField:
    def __init__(self, name, *_):
        self._name = name

    def name(self):
        return self._name


class FakeGeom:
    last_buffer = None

    def __init__(self, data=None):
        self.data = data.data if isinstance(data, FakeGeom) else data
        self.type = 'polygon' if isinstance(data, FakeGeom) else 'line'

    @staticmethod
    def fromPolylineXY(points):
        return FakeGeom(points)

    def buffer(self, distance, segments):
        FakeGeom.last_buffer = ('both', distance, segments)
        return FakeGeom(self)

    def singleSidedBuffer(self, distance, segments, side, join, miter):
        FakeGeom.last_buffer = (side, distance, segments, join, miter)
        return FakeGeom(self)

    def isEmpty(self):
        return not self.data

    def isNull(self):
        return False

    def isGeosValid(self):
        return True

    def length(self):
        return 10

    def wkbType(self):
        return 3

    def convertToMultiType(self):
        self.type = 'multi'

    def transform(self, *_):
        pass


class FakeFeature:
    def __init__(self, fields):
        self.geometry = None
        self.values = {}
        self._fields = fields

    def setGeometry(self, geom):
        self.geometry = geom

    def __setitem__(self, key, value):
        self.values[key] = value


class FakeLayer:
    counter = 0

    def __init__(self, description='Polygon', name='destination', provider='memory'):
        FakeLayer.counter += 1
        self.layer_id = str(FakeLayer.counter)
        self.layer_name = name
        self._provider = provider
        self._crs = Project.instance().crs()
        self._fields = []
        self._properties = {}
        self._editable = False
        self._fail_add = False
        self._fail_commit = False
        self.features = []
        self.commands = []

    def id(self):
        return self.layer_id

    def name(self):
        return self.layer_name

    def isValid(self):
        return True

    def geometryType(self):
        return 2

    def readOnly(self):
        return False

    def crs(self):
        return self._crs

    def setCrs(self, crs):
        self._crs = crs

    def providerType(self):
        return self._provider

    def customProperty(self, key, default=None):
        return self._properties.get(key, default)

    def setCustomProperty(self, key, value):
        self._properties[key] = value

    def dataProvider(self):
        return self

    def capabilities(self):
        return 1

    def addAttributes(self, fields):
        self._fields.extend(fields)
        return True

    def updateFields(self):
        pass

    def fields(self):
        return self._fields

    def wkbType(self):
        return 3

    def isEditable(self):
        return self._editable

    def beginEditCommand(self, text):
        self.commands.append(('begin', text))

    def endEditCommand(self):
        self.commands.append(('end',))

    def destroyEditCommand(self):
        self.commands.append(('destroy',))

    def addFeature(self, feature):
        if self._fail_add:
            return False
        self.features.append(feature)
        return True

    def updateExtents(self):
        pass

    def triggerRepaint(self):
        pass


@contextmanager
def fake_edit(layer):
    layer._editable = True
    try:
        yield
        if layer._fail_commit:
            raise RuntimeError('simulated COMMIT failure')
    finally:
        layer._editable = False


class FakeScene:
    def __init__(self):
        self.removed = []

    def removeItem(self, item):
        self.removed.append(item)


class FakeCanvas:
    def __init__(self):
        self.current_tool = None
        self._scene = FakeScene()
        self.crs = Project.instance().crs()
        self.refresh_count = 0

    def mapSettings(self):
        return self

    def destinationCrs(self):
        return self.crs

    def mapTool(self):
        return self.current_tool

    def setMapTool(self, tool):
        if self.current_tool is not None:
            self.current_tool.deactivate()
        self.current_tool = tool

    def unsetMapTool(self, tool):
        if self.current_tool is tool:
            self.current_tool.deactivate()
            self.current_tool = None

    def scene(self):
        return self._scene

    def refresh(self):
        self.refresh_count += 1


class FakeMapTool:
    def __init__(self, canvas):
        self.canvas = canvas
        self.deleted = False

    def deactivate(self):
        pass

    def setCursor(self, *_):
        pass

    def toMapCoordinates(self, pos):
        return pos

    def deleteLater(self):
        self.deleted = True

    def keyPressEvent(self, _):
        pass


class FakeBand:
    def __init__(self, canvas, *_):
        self.canvas = canvas
        self.deleted = False
        self.reset_count = 0

    def setColor(self, *_):
        pass

    def setFillColor(self, *_):
        pass

    def setWidth(self, *_):
        pass

    def setLineStyle(self, *_):
        pass

    def reset(self, *_):
        self.reset_count += 1

    def setToGeometry(self, *_):
        pass

    def addPoint(self, *_):
        pass

    def hide(self):
        pass

    def deleteLater(self):
        self.deleted = True


class FakeMessageBar:
    def __init__(self):
        self.warnings = []

    def pushWarning(self, title, message):
        self.warnings.append(message)


class FakeIface:
    def __init__(self):
        self.canvas = FakeCanvas()
        self.layer = None
        self.menu_actions = []
        self.toolbar_actions = []
        self.messages = FakeMessageBar()

    def mapCanvas(self):
        return self.canvas

    def activeLayer(self):
        return self.layer

    def mainWindow(self):
        return object()

    def addToolBarIcon(self, action):
        self.toolbar_actions.append(action)

    def removeToolBarIcon(self, action):
        self.toolbar_actions.remove(action)

    def addPluginToMenu(self, menu, action):
        self.menu_actions.append(action)

    def removePluginMenu(self, menu, action):
        self.menu_actions.remove(action)

    def messageBar(self):
        return self.messages


class MockQgisContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        modules = {name: types.ModuleType(name) for name in (
            'qgis', 'qgis.PyQt', 'qgis.PyQt.QtCore', 'qgis.PyQt.QtGui',
            'qgis.PyQt.QtWidgets', 'qgis.core', 'qgis.gui', 'qgis.utils',
        )}
        core, qcore = modules['qgis.core'], modules['qgis.PyQt.QtCore']
        widgets = modules['qgis.PyQt.QtWidgets']
        qcore.Qt = types.SimpleNamespace(
            LeftButton=1, RightButton=2, Key_Escape=3, Key_Return=4,
            Key_Enter=5, DotLine=6, CrossCursor=7,
        )
        qcore.QVariant = types.SimpleNamespace(Double=float, String=str)
        qcore.QCoreApplication = types.SimpleNamespace(translate=lambda _key, text: text)
        modules['qgis.PyQt.QtGui'].QColor = lambda *args: args
        modules['qgis.PyQt.QtGui'].QIcon = lambda *args: args
        widgets.QAction = Action
        widgets.QMessageBox = types.SimpleNamespace(warning=lambda *args: None)
        for name in ('QDialog', 'QVBoxLayout', 'QFormLayout', 'QDoubleSpinBox',
                     'QComboBox', 'QDialogButtonBox', 'QLabel'):
            setattr(widgets, name, type(name, (), {}))
        core.Qgis = types.SimpleNamespace(
            JoinStyle=types.SimpleNamespace(Miter=7),
            BufferSide=types.SimpleNamespace(Left='LEFT', Right='RIGHT'),
            Warning=2,
        )
        for name, obj in (
            ('QgsProject', Project), ('QgsFeature', FakeFeature),
            ('QgsGeometry', FakeGeom), ('QgsPointXY', FakePoint),
            ('QgsField', FakeField), ('QgsVectorLayer', FakeLayer),
            ('QgsVectorDataProvider', types.SimpleNamespace(AddFeatures=1)),
            ('QgsCoordinateTransform', lambda *args: args),
            ('QgsMessageLog', types.SimpleNamespace(logMessage=lambda *args: None)),
            ('QgsUnitTypes', types.SimpleNamespace(DistanceMeters=0)),
            ('QgsWkbTypes', types.SimpleNamespace(
                LineGeometry=1, PolygonGeometry=2, isMultiType=lambda v: v == 6,
            )), ('edit', fake_edit),
        ):
            setattr(core, name, obj)
        modules['qgis.gui'].QgsMapTool = FakeMapTool
        modules['qgis.gui'].QgsRubberBand = FakeBand
        modules['qgis.utils'].showPluginHelp = lambda **kwargs: kwargs
        cls.patch_modules = patch.dict(sys.modules, modules)
        cls.patch_modules.start()
        cls.module = importlib.import_module('Directional_line_buffer_Tool.map_tool')
        cls.plugin_module = importlib.import_module('Directional_line_buffer_Tool.directional_line_buffer')

    @classmethod
    def tearDownClass(cls):
        for name in ('Directional_line_buffer_Tool.map_tool',
                     'Directional_line_buffer_Tool.buffer_dialog',
                     'Directional_line_buffer_Tool.directional_line_buffer'):
            sys.modules.pop(name, None)
        cls.patch_modules.stop()

    def setUp(self):
        Project()
        self.iface = FakeIface()
        self.tool = self.module.DirectionalBufferMapTool(self.iface, 10, 'left')

    def tearDown(self):
        self.tool.dispose()

    def test_left_side_api_dispatch(self):
        self.tool.make_buffer(FakeGeom([1, 2]))
        self.assertEqual(FakeGeom.last_buffer[0], 'LEFT')
        self.assertEqual(FakeGeom.last_buffer[3:], (7, 5.0))

    def test_right_side_api_dispatch(self):
        self.tool.side = 'right'
        self.tool.make_buffer(FakeGeom([1, 2]))
        self.assertEqual(FakeGeom.last_buffer[0], 'RIGHT')

    def test_both_side_api_dispatch(self):
        self.tool.side = 'both'
        self.tool.make_buffer(FakeGeom([1, 2]))
        self.assertEqual(FakeGeom.last_buffer, ('both', 10, 12))

    def test_memory_layer_not_confused_with_same_named_user_layer(self):
        foreign = FakeLayer(name='Directional buffer', provider='ogr')
        Project.instance().addMapLayer(foreign)
        temp = self.tool.temp_layer()
        self.assertIsNot(temp, foreign)
        self.assertEqual(foreign.fields(), [])
        self.assertEqual(len(temp.fields()), 2)
        self.assertIs(self.tool.temp_layer(), temp)

    def test_freeze_destination_at_start(self):
        original = FakeLayer(name='intended')
        other = FakeLayer(name='new active')
        Project.instance().addMapLayer(original)
        Project.instance().addMapLayer(other)
        self.tool.preferred_layer = original
        self.iface.layer = other
        self.assertIs(self.tool.target_layer(), original)

    def test_removed_layer_reverts_to_temporary(self):
        original = FakeLayer()
        Project.instance().addMapLayer(original)
        self.tool.preferred_layer = original
        Project.instance().layers.pop(original.id())
        self.assertIsNot(self.tool.target_layer(), original)

    def test_existing_edit_buffer_uses_undo_command(self):
        layer = FakeLayer()
        layer._editable = True
        feature = FakeFeature([])
        self.assertTrue(self.tool.add_feature(layer, feature))
        self.assertEqual(layer.commands, [('begin', 'Add directional buffer'), ('end',)])

    def test_existing_edit_buffer_add_failure_rolled_back(self):
        layer = FakeLayer()
        layer._editable = True
        layer._fail_add = True
        self.assertFalse(self.tool.add_feature(layer, FakeFeature([])))
        self.assertEqual(layer.commands[-1], ('destroy',))

    def test_commit_failure_is_not_automatically_retried(self):
        layer = FakeLayer()
        Project.instance().addMapLayer(layer)
        self.tool.preferred_layer = layer
        layer._fail_commit = True
        polygon = FakeGeom([FakePoint(0, 0), FakePoint(10, 0)])
        self.assertFalse(self.tool.create_output(polygon))
        self.assertEqual(len(Project.instance().layers), 1)
        self.assertTrue(any('may be partial' in text for text in self.iface.messages.warnings))

    def test_crs_change_aborts(self):
        self.iface.canvas.setMapTool(self.tool)
        self.tool.points = [FakePoint(0, 0), FakePoint(10, 0)]
        Project.instance().crs_value = CRS('EPSG:3857')
        self.assertFalse(self.tool._crs_unchanged())
        self.assertIsNone(self.iface.canvas.mapTool())
        self.assertEqual(len(self.tool.points), 0)

    def test_dispose_removes_both_canvas_items_once(self):
        self.iface.canvas.setMapTool(self.tool)
        self.tool.dispose()
        self.tool.dispose()
        self.assertEqual(len(self.iface.canvas.scene().removed), 2)
        self.assertTrue(self.tool.deleted)

    def test_plugin_action_registration_idempotent(self):
        plugin = self.plugin_module.DirectionalLineBuffer(self.iface)
        plugin.initGui()
        plugin.initGui()
        self.assertEqual(len(self.iface.menu_actions), 2)
        self.assertEqual(len(self.iface.toolbar_actions), 1)
        plugin.unload()
        plugin.unload()
        self.assertEqual(self.iface.menu_actions, [])
        self.assertEqual(self.iface.toolbar_actions, [])

    def test_plugin_factory_class(self):
        entry = importlib.import_module('Directional_line_buffer_Tool')
        instance = entry.classFactory(self.iface)
        self.assertIsInstance(instance, self.plugin_module.DirectionalLineBuffer)


if __name__ == '__main__':
    unittest.main()
