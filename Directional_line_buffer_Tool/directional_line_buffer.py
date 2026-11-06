"""QGIS plugin action, lifecycle and dialog integration."""

import os

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import (
    QgsProject, QgsUnitTypes, QgsVectorDataProvider, QgsVectorLayer, QgsWkbTypes,
)

from .buffer_dialog import BufferDialog
from .map_tool import DirectionalBufferMapTool

ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.png')


class DirectionalLineBuffer:
    """Plugin root object expected by QGIS ``classFactory``."""

    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.help_action = None
        self.map_tool = None
        self.menu = self.tr('&Directional Line Buffer')

    def tr(self, message):
        return QCoreApplication.translate('DirectionalLineBuffer', message)

    def initGui(self):
        if self.action is not None:  # Guard against accidental duplicate calls.
            return
        self.action = QAction(
            QIcon(ICON_PATH), self.tr('Directional Line Buffer'),
            self.iface.mainWindow(),
        )
        self.action.setObjectName('directionalLineBufferAction')
        self.action.setToolTip(self.tr('Draw a left, right or both-side line buffer'))
        self.action.setStatusTip(self.tr('Digitize a line and create a directional buffer polygon'))
        self.action.triggered.connect(self.start)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.menu, self.action)

        self.help_action = QAction(self.tr('Directional Line Buffer Help'), self.iface.mainWindow())
        self.help_action.setObjectName('directionalLineBufferHelpAction')
        self.help_action.triggered.connect(self.show_help)
        self.iface.addPluginToMenu(self.menu, self.help_action)

    def show_help(self):
        from qgis.utils import showPluginHelp
        showPluginHelp(packageName=__package__)

    def unload(self):
        if self.map_tool is not None:
            self.map_tool.dispose()
            self.map_tool = None
        if self.help_action is not None:
            self.iface.removePluginMenu(self.menu, self.help_action)
            self.help_action.triggered.disconnect(self.show_help)
            self.help_action.deleteLater()
            self.help_action = None
        if self.action is not None:
            self.iface.removePluginMenu(self.menu, self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action.triggered.disconnect(self.start)
            self.action.deleteLater()
            self.action = None

    @staticmethod
    def _is_meter_project():
        crs = QgsProject.instance().crs()
        return (crs.isValid() and not crs.isGeographic()
                and crs.mapUnits() == QgsUnitTypes.DistanceUnit.DistanceMeters)

    def _destination_description(self, layer):
        try:
            ready = (isinstance(layer, QgsVectorLayer) and layer.isValid()
                     and QgsProject.instance().mapLayer(layer.id()) is not None
                     and layer.geometryType() == QgsWkbTypes.GeometryType.PolygonGeometry
                     and layer.crs().isValid() and not layer.readOnly()
                     and layer.dataProvider() is not None
                     and bool(layer.dataProvider().capabilities() & QgsVectorDataProvider.Capability.AddFeatures))
        except RuntimeError:
            ready = False
        if ready:
            return self.tr('Output: selected polygon layer "{}" (temporary fallback if needed).').format(
                layer.name()
            )
        return self.tr('Output: a temporary memory polygon layer (save it before closing QGIS).')

    def start(self):
        if not self._is_meter_project():
            QMessageBox.warning(
                self.iface.mainWindow(),
                self.tr('Projected meter-based CRS required'),
                self.tr('Set the QGIS project to a projected CRS whose map units are meters before using this tool.'),
            )
            return
        project_crs = QgsProject.instance().crs()
        canvas_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if canvas_crs != project_crs:
            QMessageBox.warning(
                self.iface.mainWindow(), self.tr('Map CRS mismatch'),
                self.tr('The map canvas and project use different CRSs. Match them before digitizing.'),
            )
            return

        intended_layer = self.iface.activeLayer()
        dialog = BufferDialog(
            self.iface.mainWindow(), self._destination_description(intended_layer),
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        # Recheck after a potentially long-lived modal dialog.
        if not self._is_meter_project() or self.iface.mapCanvas().mapSettings().destinationCrs() != project_crs:
            QMessageBox.warning(
                self.iface.mainWindow(), self.tr('CRS changed'),
                self.tr('The CRS changed while the dialog was open. Restart the tool.'),
            )
            return
        new_tool = DirectionalBufferMapTool(
            self.iface, dialog.distance_meters(), dialog.side(), intended_layer,
        )
        self.iface.mapCanvas().setMapTool(new_tool)
        old_tool = self.map_tool
        self.map_tool = new_tool
        if old_tool is not None:
            old_tool.dispose()
