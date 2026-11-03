# Directional Line Buffer

Copyright (c) Vipul Chhikara. Licensed under the GNU General Public License,
version 3 or (at your option) any later version; see `LICENSE`.

QGIS plugin for drawing left, right or both-side line buffers in projected,
meter-based projects.

## Installation for development

Copy or link the `Directional_line_buffer_Tool` folder into the QGIS Python
plugins directory, then enable **Directional Line Buffer** from the QGIS Plugin
Manager. Requires QGIS 3.30 or newer.

## Current behavior

- Requires a projected QGIS project CRS with meter units.
- Opens a distance and side dialog when the tool starts.
- Digitizes a multi-vertex line on the map canvas.
- Previews a left, right, or both-side buffer while drawing.
- Finishes with double-click, Enter, or right-click, and stays active so the
  next buffer can be drawn without reopening the dialog.
- Cancels the current line with Escape; pressing Escape again when nothing is
  being drawn exits the tool.

## Where finished polygons are saved

- If the active layer in the Layers panel is an editable polygon vector layer,
  every finished buffer is written into that layer, in its own CRS and geometry
  type (single or multi polygon), and committed to its data source.
- If the active layer is missing, not a vector polygon layer, or read-only, the
  buffer goes into a temporary memory layer named `Directional buffer`.
- If writing to the active layer fails, a warning is shown and the polygon is
  saved to the temporary layer instead so no work is lost.
- `distance_m` and `side` attributes are filled in whenever the target layer
  already has fields with those names. Fields are never added to your layer.

## Known limitations

- The temporary `Directional buffer` layer is a memory layer, so it is lost
  when the project closes unless it is saved to a permanent format.
- Very sharp bends can still produce self-intersecting offset geometry, in which
  case the polygon is rejected with a warning instead of being added.
- The project CRS must use meters; other projected units are intentionally
  rejected.
