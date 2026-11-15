# Directional Line Buffer

Draw a road centerline in QGIS and create a left, right or both-sided buffer with a live preview. Choose round or flat ends.

## Requirements and installation

Use a projected project CRS in meters, with the canvas CRS matching the project. Install the ZIP through **Plugins > Manage and Install Plugins > Install from ZIP**, then enable the plugin. Use a projection appropriate to the area; distances are planar.

## How to use

1. Select a writable polygon layer for output, or leave no suitable polygon layer selected to create a temporary memory layer.
2. Open the plugin, choose the distance, side and road-end style, and press **OK**. The settings window can be minimized while you draw.
3. Left-click to place points. Move the pointer to preview the buffer. Press **Backspace** to remove the last point.
4. Right-click and choose **Finish digitizing** to save the buffer or **Clear digitizing** to discard the line. Enter and double-click also finish the line.
5. Continue drawing. Escape clears an unfinished line; on an empty canvas it exits the map tool. Press OK in the settings window to reactivate it. Closing the window ends the tool.

Left and right follow the direction in which you draw. To change settings, adjust them and press OK; an unfinished line is cleared. The output layer is chosen when the window opens.

## Saving and troubleshooting

Save temporary memory layers to a permanent GIS format before closing the project. An existing editable layer receives an undoable edit; otherwise the plugin commits the addition immediately. If a commit may have partially written data, inspect the destination and QGIS log before retrying. Required fields, constraints or incompatible geometry can prevent a destination from accepting an output.

The plugin displays What's New for each new version; open it again from the plugin menu. Offline instructions are available through the plugin's Help menu.

Copyright (c) Vipul Chhikara. GPL-3.0-or-later; see [LICENSE](LICENSE).

This package targets QGIS 4.0 through 4.99. The updated features have not yet been tested in a QGIS 4 runtime.
