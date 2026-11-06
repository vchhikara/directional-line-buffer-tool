"""Canvas digitizing, GEOS buffering and controlled layer output."""

from qgis.PyQt.QtCore import QVariant, Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsCoordinateTransform, QgsFeature, QgsField, QgsGeometry, QgsMessageLog,
    QgsPointXY, QgsProject, QgsVectorDataProvider, QgsVectorLayer,
    QgsWkbTypes, Qgis, edit,
)
from qgis.gui import QgsMapTool, QgsRubberBand

from .validation import normalized_points, validate_parameters

MITER_JOIN = Qgis.JoinStyle.Miter
LEFT_SIDE = Qgis.BufferSide.Left
RIGHT_SIDE = Qgis.BufferSide.Right


class BufferWriteError(Exception):
    """Operation rejected without evidence of a committed write."""


class UncertainWriteError(BufferWriteError):
    """Commit may have partly reached a provider; do not silently duplicate."""


class _AddRejected(BufferWriteError):
    """Layer addFeature rejected the candidate feature."""


class DirectionalBufferMapTool(QgsMapTool):
    TEMP_LAYER_NAME = 'Directional buffer'
    TEMP_LAYER_MARKER = 'directional_line_buffer/owned_memory_output'
    FIELDS = (
        ('distance_m', QVariant.Double, 'double', 12, 3),
        ('side', QVariant.String, 'string', 16, 0),
    )

    def __init__(self, iface, distance, side, preferred_layer=None):
        validate_parameters(distance, side)
        super().__init__(iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.distance = distance
        self.side = side
        self.preferred_layer = preferred_layer
        self.source_crs = QgsProject.instance().crs()
        self.points = []
        self.cursor_point = None
        self._disposed = False

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

    def _crs_unchanged(self):
        if (QgsProject.instance().crs() == self.source_crs
                and self.canvas.mapSettings().destinationCrs() == self.source_crs):
            return True
        self.warn('Project or canvas CRS changed. Drawing cancelled to protect buffer coordinates.')
        self.reset_drawing()
        if self.canvas.mapTool() is self:
            self.canvas.unsetMapTool(self)
        return False

    def canvasPressEvent(self, event):
        if self._disposed or not self._crs_unchanged():
            return
        point = QgsPointXY(self.toMapCoordinates(event.pos()))
        if event.button() == Qt.LeftButton:
            if not self.points or point != self.points[-1]:
                self.points.append(point)
            self.cursor_point = point
            self.refresh_preview()
        elif event.button() == Qt.RightButton:
            self.finish()

    def canvasMoveEvent(self, event):
        if self._disposed or not self._crs_unchanged():
            return
        point = QgsPointXY(self.toMapCoordinates(event.pos()))
        if point == self.cursor_point:
            return
        self.cursor_point = point
        if self.points:
            self.refresh_preview(include_cursor=True)

    def canvasDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and not self._disposed and self._crs_unchanged():
            point = QgsPointXY(self.toMapCoordinates(event.pos()))
            if not self.points or point != self.points[-1]:
                self.points.append(point)
            self.finish()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.finish()
        else:
            super().keyPressEvent(event)

    def _line_points(self, include_cursor=False):
        points = list(self.points)
        if include_cursor and self.cursor_point is not None:
            if not points or self.cursor_point != points[-1]:
                points.append(self.cursor_point)
        return points

    def refresh_preview(self, include_cursor=False):
        if self._disposed:
            return
        points = self._line_points(include_cursor)
        self.center_band.reset(QgsWkbTypes.LineGeometry)
        self.buffer_band.reset(QgsWkbTypes.PolygonGeometry)
        if len(points) < 2:
            if points:
                self.center_band.addPoint(points[0], True)
            return
        try:
            clean = normalized_points(points)
            line = QgsGeometry.fromPolylineXY(clean)
            self.center_band.setToGeometry(line, None)
            polygon = self.make_buffer(line)
            if polygon is not None and not polygon.isEmpty():
                self.buffer_band.setToGeometry(polygon, None)
        except (ValueError, RuntimeError) as exc:
            # Preview failures are recoverable; finalization provides warnings.
            self._log('Preview unavailable: {}'.format(exc))

    def make_buffer(self, line):
        if self.side == 'both':
            return line.buffer(self.distance, 12)
        side = LEFT_SIDE if self.side == 'left' else RIGHT_SIDE
        return line.singleSidedBuffer(self.distance, 12, side, MITER_JOIN, 5.0)

    def finish(self):
        if self._disposed or not self._crs_unchanged():
            return
        try:
            clean = normalized_points(self.points)
        except ValueError as exc:
            self.warn(str(exc))
            return
        try:
            line = QgsGeometry.fromPolylineXY(clean)
            if line.isEmpty() or line.length() <= 0:
                self.warn('The digitized line must have a positive length.')
                return
            polygon = self.make_buffer(line)
            if polygon is None or polygon.isNull() or polygon.isEmpty() or not polygon.isGeosValid():
                self.warn('No valid buffer could be created. Simplify sharp bends or adjust the line.')
                return
        except (ValueError, RuntimeError) as exc:
            self.warn('Buffer geometry error: {}'.format(exc))
            self._log('Buffer geometry error: {}'.format(exc))
            return
        if self.create_output(polygon):
            self.reset_drawing()
            self.canvas.refresh()

    def create_output(self, polygon):
        try:
            target = self.target_layer()
        except (BufferWriteError, ValueError, RuntimeError) as exc:
            self._log('Output layer unavailable: {}'.format(exc))
            self.warn('Could not prepare an output layer: {}'.format(exc))
            return False
        try:
            feature = self.build_feature(polygon, target)
            if self.add_feature(target, feature):
                return True
            error = 'The selected layer rejected this polygon.'
        except UncertainWriteError as exc:
            self._log('Output commit uncertain: {}'.format(exc))
            self.warn('The layer commit failed and may be partial. No fallback copy was made. Review the layer and its commit errors: {}'.format(exc))
            return False
        except (BufferWriteError, ValueError, RuntimeError) as exc:
            error = str(exc)
            self._log('Output failure: {}'.format(error))

        # Only use the fallback for failures which are safe to retry elsewhere.
        try:
            fallback = self.temp_layer()
            if target is not fallback:
                self.warn('Could not write to "{}": {} Saving to temporary output.'.format(target.name(), error))
                if self.add_feature(fallback, self.build_feature(polygon, fallback)):
                    return True
            else:
                self.warn('Temporary output could not accept the polygon: {}'.format(error))
        except (BufferWriteError, ValueError, RuntimeError) as exc:
            self._log('Temporary output failure: {}'.format(exc))
            self.warn('Temporary output failed: {}'.format(exc))
        return False

    def target_layer(self):
        layer = self.preferred_layer
        try:
            if (isinstance(layer, QgsVectorLayer)
                    and QgsProject.instance().mapLayer(layer.id()) is not None
                    and layer.isValid()
                    and layer.geometryType() == QgsWkbTypes.PolygonGeometry
                    and layer.crs().isValid()
                    and not layer.readOnly()
                    and layer.dataProvider() is not None
                    and layer.dataProvider().capabilities() & QgsVectorDataProvider.AddFeatures):
                return layer
        except RuntimeError:
            # The original layer can be removed and destroyed while drawing.
            pass
        return self.temp_layer()

    def build_feature(self, polygon, layer):
        feature = QgsFeature(layer.fields())
        feature.setGeometry(self.prepare_geometry(polygon, layer))
        field_names = {field.name() for field in layer.fields()}
        if 'distance_m' in field_names:
            feature['distance_m'] = float(self.distance)
        if 'side' in field_names:
            feature['side'] = self.side
        return feature

    def prepare_geometry(self, polygon, layer):
        if not layer.crs().isValid():
            raise BufferWriteError('Output layer has an invalid CRS.')
        geometry = QgsGeometry(polygon)
        if layer.crs() != self.source_crs:
            try:
                geometry.transform(QgsCoordinateTransform(
                    self.source_crs, layer.crs(), QgsProject.instance(),
                ))
            except Exception as exc:
                # Transformation occurs before any output write; fallback is safe.
                raise BufferWriteError('Could not transform polygon into destination CRS: {}'.format(exc)) from exc
        if geometry.isNull() or geometry.isEmpty() or not geometry.isGeosValid():
            raise BufferWriteError('Transformed output geometry is empty or invalid.')
        if (QgsWkbTypes.isMultiType(layer.wkbType())
                and not QgsWkbTypes.isMultiType(geometry.wkbType())):
            geometry.convertToMultiType()
        return geometry

    def add_feature(self, layer, feature):
        if layer.isEditable():
            # This path never commits existing user edits; create one undo entry.
            try:
                layer.beginEditCommand('Add directional buffer')
                try:
                    if not layer.addFeature(feature):
                        raise _AddRejected('Layer rejected the feature.')
                    layer.endEditCommand()
                except _AddRejected as exc:
                    layer.destroyEditCommand()
                    self._log(str(exc))
                    return False
                except Exception:
                    layer.destroyEditCommand()
                    raise
            except Exception as exc:
                raise UncertainWriteError('Editing-buffer write failed: {}'.format(exc)) from exc
        else:
            try:
                with edit(layer):
                    if not layer.addFeature(feature):
                        raise _AddRejected('Layer rejected the feature.')
            except _AddRejected as exc:
                self._log(str(exc))
                return False
            except Exception as exc:
                # A failure during commit may have partially written to disk.
                raise UncertainWriteError('Edit transaction failed: {}'.format(exc)) from exc
        layer.updateExtents()
        layer.triggerRepaint()
        return True

    def temp_layer(self):
        project = QgsProject.instance()
        for layer in project.mapLayers().values():
            if (isinstance(layer, QgsVectorLayer)
                    and layer.customProperty(self.TEMP_LAYER_MARKER, False)
                    and layer.isValid() and layer.providerType() == 'memory'
                    and layer.geometryType() == QgsWkbTypes.PolygonGeometry
                    and layer.crs() == self.source_crs):
                self.ensure_fields(layer)
                return layer
        layer = QgsVectorLayer('Polygon', self.TEMP_LAYER_NAME, 'memory')
        if not layer.isValid():
            raise BufferWriteError('Unable to create memory polygon layer.')
        layer.setCrs(self.source_crs)
        self.ensure_fields(layer)
        layer.setCustomProperty(self.TEMP_LAYER_MARKER, True)
        project.addMapLayer(layer)
        return layer

    def ensure_fields(self, layer):
        # Invoke only on confirmed plugin-owned memory layers or brand-new ones.
        existing = {field.name() for field in layer.fields()}
        missing = [
            QgsField(name, field_type, type_name, length, precision)
            for name, field_type, type_name, length, precision in self.FIELDS
            if name not in existing
        ]
        if missing:
            if not layer.dataProvider().addAttributes(missing):
                raise BufferWriteError('Unable to add attributes to memory output.')
            layer.updateFields()
        required = {name for name, *_ in self.FIELDS}
        if not required.issubset({field.name() for field in layer.fields()}):
            raise BufferWriteError('Memory output attributes are incomplete.')
        return layer

    def _log(self, message):
        QgsMessageLog.logMessage(message, 'Directional Line Buffer', Qgis.Warning)

    def warn(self, message):
        self.iface.messageBar().pushWarning('Directional Line Buffer', message)

    def reset_drawing(self):
        self.points.clear()
        self.cursor_point = None
        if self.center_band is not None:
            self.center_band.reset(QgsWkbTypes.LineGeometry)
        if self.buffer_band is not None:
            self.buffer_band.reset(QgsWkbTypes.PolygonGeometry)

    def cancel(self):
        had_points = bool(self.points)
        self.reset_drawing()
        self.canvas.refresh()
        if not had_points and self.canvas.mapTool() is self:
            self.canvas.unsetMapTool(self)

    def deactivate(self):
        super().deactivate()
        self.reset_drawing()
        self.canvas.refresh()

    def dispose(self):
        """Remove map scene objects on restart/unload; safe to call repeatedly."""
        if self._disposed:
            return
        self._disposed = True
        if self.canvas.mapTool() is self:
            self.canvas.unsetMapTool(self)
        self.reset_drawing()
        for name in ('center_band', 'buffer_band'):
            band = getattr(self, name)
            if band is not None:
                band.hide()
                self.canvas.scene().removeItem(band)
                band.deleteLater()
                setattr(self, name, None)
        self.deleteLater()
