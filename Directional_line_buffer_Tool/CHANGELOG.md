# Changelog

## 0.3.2 - Qt 6 enum update (2026-11-07)

- Use scoped enum names (for example `Qt.MouseButton.LeftButton`, `QgsWkbTypes.GeometryType.PolygonGeometry`) so the plugin passes the QGIS 4 / Qt 6 check.
- Replace `exec_()` with `exec()`.
- No change to buffering behavior.

## 0.3.1 - Patch release candidate (2026-11-04)

- Fix accidental writes to unrelated `Directional buffer` layers: only reuse plugin-marked memory layers.
- Freeze the selected output target when digitizing begins and reject CRS changes mid-session.
- Handle repeated vertices, nonfinite coordinates, and degenerate lines before buffering.
- Improve editing-buffer undo commands, output error reporting and unsafe commit fallback protection.
- Dispose Qt canvas rubber bands on plugin reload/replacement and remove duplicate action registration.
- Use explicit QGIS meter unit enum, make memory CRS setup independent of EPSG authority strings.
- Add parameter/destination descriptions, offline HTML help, regression tests and reproducible packaging.
- Tested in QGIS 4 by the author. Set `qgisMaximumVersion=4.99` and `experimental=False`.
- Keep existing core buffering algorithms, icon, plugin name, author, license and minimum declared QGIS version; explicitly cap compatibility metadata at QGIS 3.99 because QGIS 4/Qt 6 was not tested.

## 0.3.0 - Original archive

- Interactive directional buffers and polygon layer output, as declared in the supplied original metadata.

Historical change records before 0.3.0 were not supplied and are not inferred.
