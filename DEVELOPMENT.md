# Development and release

## Source layout

`Directional_line_buffer_Tool/` is the direct-install plugin directory, containing `__init__.py` (`classFactory`), `directional_line_buffer.py` (UI actions/lifecycle), `buffer_dialog.py` (parameters), `map_tool.py` (canvas/geometry/output), `validation.py` (dependency-free validation), metadata, icon, help, README, changelog and license. `tests/` contains Python-only, fake-QGIS contract and separately skipped real-QGIS integration tests. `scripts/` validates metadata/structure and creates deterministic release ZIPs. `docs/` holds audit references.

The `mainPlugin.py` name in the QGIS cookbook is an example, not an enforced filename. `resources.qrc`/`resources.py`, `.ui` and translations are unnecessary for this Python-built Qt dialog and filesystem-loaded PNG. A Processing provider is not registered.

## Environment

This plugin declares `qgisMinimumVersion=3.30` as in the original metadata, and `qgisMaximumVersion=4.99`. The author tested the plugin in QGIS 4. The code still uses some Qt 5 style calls, so check the Qt 6 report on the plugin repository after each upload. All QGIS runtime APIs must be verified against the actual target version. Use QGIS's packaged Python and bundled PyQt rather than installing PyQt separately. No third-party Python runtime dependency is declared. For the optional native integration suite, install the QGIS Python bindings, QGIS GUI libraries and a working Qt graphical/offscreen environment (e.g. `xvfb-run`).

## Dependency-free checks and packaging

Run from the source project root:

```bash
python3 scripts/validate_plugin.py Directional_line_buffer_Tool
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/package_plugin.py --source Directional_line_buffer_Tool --output dist/QGIS_PLUGIN_UPGRADED.zip
python3 scripts/validate_plugin.py Directional_line_buffer_Tool --zip dist/QGIS_PLUGIN_UPGRADED.zip
```

The mock API tests verify dispatch and control flow, **not QGIS implementation behavior**. Real QGIS tests are explicitly skipped when bindings are missing. No fake test result establishes runtime compatibility.

## Real QGIS tests

From a shell configured for the chosen QGIS installation, with this project root on `PYTHONPATH` and an appropriate graphical environment:

```bash
export QT_QPA_PLATFORM=offscreen
python3 -m unittest discover -s tests -p 'test_qgis_runtime.py' -v
```

On Linux, `xvfb-run -a python3 ...` can be used for QGIS/Qt headless GUI testing. If `qgis` imports fail, use the interpreter/`PYTHONPATH` from the QGIS installation, and set `QGIS_PREFIX_PATH` if that distribution needs it. Run an interactive end-to-end check using the **exact packaged ZIP** and a temporary project, before publishing.

### Manual release checklist

1. Install ZIP into a clean QGIS profile and enable the plugin; check icon/help/toolbar/menu.
2. Create a local projected meter CRS project and writable polygon destination.
3. Draw eastward left/right and reversed east/west paths; verify saved polygon positions, areas and units.
4. Test both-side buffers, corner joins, sharp bends, self-intersections, repeated coordinates, and Escape/Enter/double-click/right-click.
5. Test a missing/read-only/invalid destination, a writable layer in a different CRS, constrained attributes, and an already-editable layer (undo, save/discard).
6. Change project CRS midway through a line; ensure no feature is saved under the wrong CRS.
7. Create an unrelated polygon layer named `Directional buffer`; verify its schema is untouched.
8. Start, cancel, exit, restart, unload and reload; inspect for duplicated actions, stuck tools and lingering canvas bands.
9. Close/reopen project after saving results to a permanent format. Check warnings and Logs Messages.
10. Test on each claimed QGIS/OS combination; record exact versions. Do not claim untested platform compatibility.

## Release discipline

- Metadata version was changed to `0.3.1` because safety and behavior fixes modify the distributable from `0.3.0`. Keep this synchronized with `CHANGELOG.md` and the release filename/tag if published.
- Retain author/repository/tracker/homepage values supplied in the original ZIP until the owner verifies them.
- Confirm license compatibility and that the source repository is public, browsable and corresponds to this ZIP.
- Review official rules at https://plugins.qgis.org/docs/publish and https://plugins.qgis.org/docs/approval.
- No publishing action is performed by the build. `qgis-plugin-ci` is **not** adopted because this project only needs local reproducible ZIP packaging, and repository tokens/translation automation are not configured. It can be reconsidered if multi-version deployment becomes necessary.
