from qgis.PyQt.QtCore import QVariant, Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsCoordinateTransform, QgsFeature, QgsField, QgsGeometry, Qgis,
    QgsPointXY, QgsProject, QgsVectorDataProvider, QgsVectorLayer,
    QgsWkbTypes, edit,
)
from qgis.gui import QgsMapTool, QgsRubberBand

MITER_JOIN = Qgis.JoinStyle.Miter
LEFT_SIDE = Qgis.BufferSide.Left
RIGHT_SIDE = Qgis.BufferSide.Right


class DirectionalBufferMapTool(QgsMapTool):
    TEMP_LAYER_NAME = 'Directional buffer'
    FIELDS = (
        ('distance_m', QVariant.Double, 'double', 12, 3),
        ('side', QVariant.String, 'string', 16, 0),
    )

    def __init__(self, iface, distance, side, previous_tool=None):
        super().__init__(iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.distance = distance
        self.side = side
        self.previous_tool = previous_tool
        self.points = []
        self.cursor_point = None

        self.center_band = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.center_band.setColor(QColor(110, 110, 110, 190))
        self.center_band.setWidth(2)
        self.center_band.setLineStyle(Qt.DotLine)

        self.buffer_band = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.buffer_band.setColor(QColor(36, 130, 170, 220))
        self.buffer_band.setFillColor(QColor(100, 190, 220, 55))
        self.buffer_band.setWidth(2)
        self.buffer_band.setLineStyle(Qt.DotLine)

        self.setCursor(Qt.CrossCursor)

    def canvasPressEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        if event.button() == Qt.LeftButton:
            self.points.append(QgsPointXY(point))
            self.cursor_point = QgsPointXY(point)
            self.refresh_preview()
        elif event.button() == Qt.RightButton:
            self.finish()

    def canvasMoveEvent(self, event):
        self.cursor_point = QgsPointXY(self.toMapCoordinates(event.pos()))
        if self.points:
            self.refresh_preview(include_cursor=True)

    def canvasDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            point = QgsPointXY(self.toMapCoordinates(event.pos()))
            if not self.points or point != self.points[-1]:
                self.points.append(point)
            self.finish()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.finish()

    def _line_points(self, include_cursor=False):
        pts = list(self.points)
        if include_cursor and self.cursor_point and (not pts or self.cursor_point != pts[-1]):
            pts.append(self.cursor_point)
        return pts

    def refresh_preview(self, include_cursor=False):
        pts = self._line_points(include_cursor)
        self.center_band.reset(QgsWkbTypes.LineGeometry)
        self.buffer_band.reset(QgsWkbTypes.PolygonGeometry)
        if len(pts) < 2:
            if pts:
                self.center_band.addPoint(pts[0], False)
                self.center_band.addPoint(pts[0], True)
            return
        line = QgsGeometry.fromPolylineXY(pts)
        self.center_band.setToGeometry(line, None)
        polygon = self.make_buffer(line)
        if polygon and not polygon.isEmpty():
            self.buffer_band.setToGeometry(polygon, None)

    def make_buffer(self, line):
        if self.side == 'both':
            return line.buffer(self.distance, 12)
        side = LEFT_SIDE if self.side == 'left' else RIGHT_SIDE
        return line.singleSidedBuffer(self.distance, 12, side, MITER_JOIN, 5.0)

    def finish(self):
        if len(self.points) < 2:
            return
        line = QgsGeometry.fromPolylineXY(self.points)
        polygon = self.make_buffer(line)
        if polygon.isEmpty() or not polygon.isGeosValid():
            self.warn('The buffer geometry could not be created. Try a different line.')
            return
        if self.create_output(polygon) is None:
            return
        self.reset_drawing()
        self.canvas.refresh()

    def create_output(self, polygon):
        target = self.target_layer()
        if self.add_feature(target, self.build_feature(polygon, target)):
            return True
        temp = self.temp_layer()
        if target is not temp:
            self.warn(
                'Could not write to "{}". Saving to the temporary buffer layer instead.'.format(
                    target.name()
                )
            )
            if self.add_feature(temp, self.build_feature(polygon, temp)):
                return True
        self.warn('The buffer polygon could not be written to the output layer.')
        return None

    def target_layer(self):
        layer = self.iface.activeLayer()
        if (
            isinstance(layer, QgsVectorLayer)
            and layer.isValid()
            and layer.geometryType() == QgsWkbTypes.PolygonGeometry
            and not layer.readOnly()
            and layer.dataProvider() is not None
            and layer.dataProvider().capabilities() & QgsVectorDataProvider.AddFeatures
        ):
            return layer
        return self.temp_layer()

    def build_feature(self, polygon, layer):
        feature = QgsFeature(layer.fields())
        feature.setGeometry(self.prepare_geometry(polygon, layer))
        names = {field.name() for field in layer.fields()}
        if 'distance_m' in names:
            feature['distance_m'] = float(self.distance)
        if 'side' in names:
            feature['side'] = str(self.side)
        return feature

    def prepare_geometry(self, polygon, layer):
        geometry = QgsGeometry(polygon)
        project_crs = QgsProject.instance().crs()
        if layer.crs().isValid() and layer.crs() != project_crs:
            transform = QgsCoordinateTransform(
                project_crs, layer.crs(), QgsProject.instance()
            )
            geometry.transform(transform)
        if QgsWkbTypes.isMultiType(layer.wkbType()) and not QgsWkbTypes.isMultiType(geometry.wkbType()):
            geometry.convertToMultiType()
        return geometry

    def add_feature(self, layer, feature):
        try:
            if layer.isEditable():
                added = layer.addFeature(feature)
            else:
                with edit(layer):
                    added = layer.addFeature(feature)
        except Exception:
            return False
        if added:
            layer.updateExtents()
            layer.triggerRepaint()
        return bool(added)

    def temp_layer(self):
        crs = QgsProject.instance().crs()
        for layer in QgsProject.instance().mapLayers().values():
            if (
                layer.name() == self.TEMP_LAYER_NAME
                and layer.isValid()
                and layer.geometryType() == QgsWkbTypes.PolygonGeometry
                and layer.crs() == crs
            ):
                return self.ensure_fields(layer)
        layer = QgsVectorLayer('Polygon?crs=' + crs.authid(), self.TEMP_LAYER_NAME, 'memory')
        self.ensure_fields(layer)
        QgsProject.instance().addMapLayer(layer)
        return layer

    def ensure_fields(self, layer):
        existing = {field.name() for field in layer.fields()}
        missing = [
            QgsField(name, field_type, type_name, length, precision)
            for name, field_type, type_name, length, precision in self.FIELDS
            if name not in existing
        ]
        if missing:
            layer.dataProvider().addAttributes(missing)
            layer.updateFields()
        return layer

    def warn(self, message):
        self.iface.messageBar().pushWarning('Directional Line Buffer', message)

    def reset_drawing(self):
        self.points = []
        self.cursor_point = None
        self.center_band.reset(QgsWkbTypes.LineGeometry)
        self.buffer_band.reset(QgsWkbTypes.PolygonGeometry)

    def cancel(self):
        had_points = bool(self.points)
        self.reset_drawing()
        self.canvas.refresh()
        if not had_points:
            self.canvas.unsetMapTool(self)

    def deactivate(self):
        super().deactivate()
        self.reset_drawing()
        self.canvas.refresh()
