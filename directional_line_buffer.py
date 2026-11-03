import os

from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsProject

from .buffer_dialog import BufferDialog
from .map_tool import DirectionalBufferMapTool

ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.svg')


class DirectionalLineBuffer:
    """QGIS plugin entry point."""

    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.map_tool = None
        self.previous_tool = None

    def tr(self, message):
        return QCoreApplication.translate('DirectionalLineBuffer', message)

    def initGui(self):
        self.action = QAction(
            QIcon(ICON_PATH),
            self.tr('Directional Line Buffer'),
            self.iface.mainWindow(),
        )
        self.action.setObjectName('directionalLineBufferAction')
        self.action.setToolTip(self.tr('Draw a left, right or both-side line buffer'))
        self.action.setStatusTip(self.tr('Digitize a line and create a directional buffer polygon'))
        self.action.triggered.connect(self.start)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.tr('&Directional Line Buffer'), self.action)

    def unload(self):
        if self.action:
            self.iface.removePluginMenu(self.tr('&Directional Line Buffer'), self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None
        if self.map_tool:
            canvas = self.iface.mapCanvas()
            if canvas.mapTool() is self.map_tool:
                canvas.unsetMapTool(self.map_tool)
            self.map_tool.deactivate()
            self.map_tool = None

    def start(self):
        crs = QgsProject.instance().crs()
        if not crs.isValid() or crs.isGeographic() or crs.mapUnits() != 0:
            QMessageBox.warning(
                self.iface.mainWindow(),
                self.tr('Projected meter-based CRS required'),
                self.tr('Set the QGIS project to a projected CRS whose map units are meters before using this tool.'),
            )
            return

        dialog = BufferDialog(self.iface.mainWindow())
        if dialog.exec_() != dialog.Accepted:
            return

        if self.map_tool:
            self.map_tool.deactivate()
        self.previous_tool = self.iface.mapCanvas().mapTool()
        self.map_tool = DirectionalBufferMapTool(
            self.iface,
            dialog.distance_meters(),
            dialog.side(),
            self.previous_tool,
        )
        self.iface.mapCanvas().setMapTool(self.map_tool)
