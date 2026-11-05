# Directional Line Buffer

Draw a line on the QGIS map canvas and create a polygon buffer on its left, right, or both sides. The polygon appears as you draw and is saved when you finish the line.

## Requirements

- QGIS 3.30 to 3.99, as declared in the plugin metadata. Compatibility across every QGIS 3 release has not been established.
- A valid projected project CRS with meter units. Choose a projection suited to your location and the accuracy you need.
- The map canvas CRS must match the project CRS.

QGIS supplies the required Python and Qt libraries. No additional packages or network connection are needed at runtime.

## Install

1. Open **Plugins > Manage and Install Plugins** in QGIS.
2. Select **Install from ZIP** and choose the plugin ZIP. The ZIP must contain one top-level `Directional_line_buffer_Tool/` folder.
3. Enable **Directional Line Buffer** if necessary. Open it from the Plugins menu or the toolbar.

The plugin is marked experimental in its metadata. If it does not appear, check whether experimental plugins are enabled in Plugin Manager.

For development, copy or link the plugin folder into the active QGIS profile's Python `plugins` directory, then restart QGIS or reload the plugin.

## Draw a buffer

1. Set the project to a suitable projected CRS with meter units.
2. To write into an existing polygon layer, select that layer before opening the tool. Otherwise, the plugin will use a temporary layer.
3. Open **Directional Line Buffer**. Enter a distance and choose **Both sides**, **Left side**, or **Right side**. The default distance is 10.000 m; the minimum is 0.010 m.
4. Left-click to place line vertices. Move the pointer to preview the buffer.
5. Right-click, double-click, or press **Enter** to finish the line.
6. Draw another line, or press **Escape** on a clear canvas to exit. Press **Escape** while drawing to discard the unfinished line.

Left and right follow the direction in which you draw. For a line drawn east, left is north and right is south. Reversing the line reverses those sides.

The destination is selected when you open the tool and stays fixed while you draw. If the project or canvas CRS changes during digitizing, the tool cancels the drawing.

## Output and saving

A selected polygon layer must be in the project, have a valid CRS, be writable, and support adding features. The plugin transforms the polygon to the layer CRS when needed. It fills `distance_m` and `side` if those fields already exist; it does not add fields to an existing destination layer.

If the destination is already being edited, the new polygon is a separate undoable edit. Otherwise, the plugin starts an edit operation and commits it immediately.

When no suitable layer is selected, the plugin creates a temporary memory layer named `Directional buffer`, with `distance_m` and `side` fields. It reuses only a matching plugin-owned memory layer. **Save temporary results to a permanent GIS format before closing the project**, or they will be lost.

If a write fails safely, the plugin warns you and tries the temporary layer. If a commit may have partially written data, it makes no fallback copy. Check the destination and the QGIS Log Messages panel before retrying to avoid duplicates.

## Troubleshooting

| Message or symptom | What to check |
| --- | --- |
| Projected meter-based CRS required | Choose a projected project CRS with meter units. Geographic latitude/longitude coordinates are not accepted. |
| Project or canvas CRS changed | Restart the tool after setting the project and canvas CRS. The unfinished drawing is discarded. |
| Invalid or empty buffer | Draw at least two distinct points. For sharp bends, loops, or crossings, try a simpler line. |
| Output goes to a temporary layer | Check that the selected polygon layer is writable, remains in the project, has a valid CRS, and accepts the feature and its attributes. |
| Commit may be partial | Review the target layer and its commit errors before retrying. |
| Output is missing after restart | Save temporary memory layers to a permanent format before closing QGIS. |

Offline help is available under **Plugins > Directional Line Buffer > Directional Line Buffer Help**.

## Geometry and limitations

Buffers use planar distances in the project CRS; they are not geodesic. Meter units alone do not guarantee ground-distance accuracy.

Single-sided buffers use QGIS/GEOS miter joins with 12 segments and a miter limit of 5. Both-sided buffers use the standard round-buffer operation with 12 segments. Invalid or empty results are rejected.

The tool digitizes new single-part centerlines. It does not buffer existing multiline features. Output may be multipart. Layers with mandatory fields, triggers, geometry constraints, or Z/M requirements can reject a feature. Preview is recalculated as the pointer moves and may slow down for long lines.

## License

Copyright (c) Vipul Chhikara. Licensed under GPL-3.0-or-later; see [LICENSE](LICENSE).
