# QGIS Plugin Upgrade Report

**Plugin:** Directional Line Buffer  
**Original:** `0.3.0` from the exact supplied ZIP  
**Candidate:** `0.3.1` (patch release candidate, not published)  
**Date:** 2026-11-04

## Implementation result

This is a source-level repair, not a replacement plugin. The original **left/right/both** GEOS-backed buffering operation remains intact: a both-side buffer calls `QgsGeometry.buffer(distance, 12)`, and a single-sided buffer calls `QgsGeometry.singleSidedBuffer(distance, 12, side, Qgis.JoinStyle.Miter, 5.0)`. The canvas digitizing workflow, toolbar and Plugins-menu entry, familiar default distance of 10 meters, repeat operation, Escape cancellation, output to a compatible selected polygon layer and temporary-memory fallback are preserved.

A deliberate behavior change protects user data: **destination layer is frozen when the dialog starts**, instead of re-reading the active selection at the moment of finalization. A noneditable destination is still written and committed automatically; the dialog now discloses the intended destination. An uncertain commit outcome is now *not* automatically duplicated into temporary output.

## File-level change manifest

| File | Changes and reason | Findings |
|---|---|---|
| `Directional_line_buffer_Tool/__init__.py` | **Unchanged**, existing `classFactory(iface)` retained | Correct original design |
| `Directional_line_buffer_Tool/directional_line_buffer.py` | Idempotent action registration/removal, old tool disposal, explicit meter enum, project/canvas CRS consistency, target freeze, destination hint, local help action | DLB-002, 005, 006, 007, 012 |
| `Directional_line_buffer_Tool/buffer_dialog.py` | Label wrapping, native widget parenting, destination disclosure and translation-ready strings; same 0.01 to 100,000,000 meter range and side choices | DLB-006, 014 |
| `Directional_line_buffer_Tool/map_tool.py` | Deduplicate clicked coordinates, validate geometry before save, detect CRS changes, protect output target, checked plugin-owned temp layer and fields, source/destination transformations, undo commands, cautious transaction handling, map-band disposal and logging | DLB-001 through 010 |
| `Directional_line_buffer_Tool/validation.py` | **New**, no-QGIS-required parameter and vertex validation, including finite coordinates and positive distance | DLB-004, 011 |
| `Directional_line_buffer_Tool/metadata.txt` | Bump from 0.3.0 to 0.3.1; `qgisMaximumVersion=3.99`, explicit changelog; preserve owner-supplied name, links, author, icon, minimum version, experimental flag | DLB-013, 016 |
| `Directional_line_buffer_Tool/index-en.html` | **New** offline help for usage, output and failure recovery | DLB-012 |
| `Directional_line_buffer_Tool/README.md` | Accurate requirements, startup, user workflows, output transaction semantics, known risks and troubleshooting | DLB-012 |
| `Directional_line_buffer_Tool/CHANGELOG.md` | **New**, patch-only verified change history without fabricated prior releases | DLB-013 |
| `Directional_line_buffer_Tool/LICENSE` | **Unchanged**, original GPLv3 full license text | Preserved |
| `Directional_line_buffer_Tool/icon.png` | **Unchanged**, original 1254px RGBA artwork | Preserved |
| `DEVELOPMENT.md` | **New**, environment, testing, build, native QGIS smoke test and release procedure | DLB-011, 013 |
| `tests/test_validation.py` | **New**, pure unit tests for numeric parameters and point normalization | DLB-004 |
| `tests/test_mock_qgis.py` | **New**, explicitly mocked QGIS/Qt API tests for behavior and lifecycle | DLB-001 through 010 |
| `tests/test_geos_reference.py` | **New**, optional Shapely/GEOS independent reference for orientation and area, not a QGIS implementation test | GIS reference |
| `tests/test_qgis_runtime.py` | **New**, runnable native PyQGIS geometry and lifecycle tests; skipped without QGIS | Runtime validation backlog |
| `tests/test_package.py` | **New**, metadata, offline help and ZIP safety assertions | Packaging |
| `scripts/validate_plugin.py` | **New**, stdlib AST/metadata/icon/ZIP validator with cache/path-traversal checks | Release integrity |
| `scripts/package_plugin.py` | **New**, explicit runtime file allowlist, stable ZIP timestamps and ownership flags | Reproducible artifact |
| `.github/workflows/validate.yml` | **New**, Python 3.10/3.12 syntax, mock/unit/static tests and deterministic ZIP build on GitHub Actions; not executed on GitHub | CI preparedness |
| `docs/guide_compliance.md` | **New**, corrected required/optional guide interpretation and official source links | Compliance record |
| `docs/PRECHANGE_AUDIT.md` | **New**, immutable pre-change findings baseline | Audit traceability |

## Engineering choices and trade-offs

- **Small native design retained.** No new external runtime dependency, Processing algorithm, translation stubs or Qt-generated resource files were added.
- **Data operations remain opt-in through selecting an active layer.** The tool displays the destination before drawing. The active layer no longer changes the output target midway through a line. Users should still use temporary output if they do not intend automatic writes.
- **Commit failures are treated cautiously.** QGIS editing APIs can report failures at a partial commit stage. The plugin logs the failure and does not retry to a different layer if the outcome is uncertain. This may require manual recovery, but avoids silently duplicating a potentially persisted feature.
- **No automatic geometry repair.** Invalid GEOS buffers are rejected rather than restructured or simplified silently.
- **No QGIS 4 claim.** QGIS 4 uses Qt 6 and needs separate migration testing; candidate metadata caps at QGIS 3.99.
- **No speed-up claimed.** Expensive live GEOS preview is retained because there is no representative runtime performance dataset.
- **Release ownership maintained.** The user-supplied author, contact, website and GitHub fields remain unchanged, even though the source repository is private and public approval would fail until fixed.

## Testing linkage

- 40 discovered tests: **37 passed, 0 failed, 3 skipped**. The passed set includes **5 GEOS/Shapely reference tests**, which are independent geometry expectations rather than successful PyQGIS geometry execution.
- Syntax and package structure: passed.
- Fresh-extracted runtime ZIP structural validation: passed.
- Rebuilt runtime ZIP SHA-256: byte-identical across two builds.
- Real QGIS load, output geometry, Qt UI behavior and provider transactions: **not run** (QGIS not installed).

See `QGIS_PLUGIN_TEST_REPORT.md` for exact environment and commands.

## Remaining risks

- Real PyQGIS 3.30 and later QGIS 3 tests are required for the true single-/double-side algorithm, CRS transformations, transaction outcomes, helper action, map canvas disposal and native UI.
- A complete automated native GIS integration suite cannot run here without QGIS and its Qt bindings.
- Projected CRS in meters is necessary but not sufficient for a distortion-free distance: local projection selection remains the GIS operator's responsibility.
- Existing layer constraints, mandatory fields, provider commit behavior and Z/M support need actual QGIS fixtures.
- The GitHub repository indicated in metadata is **private**. Official plugin submission expects public browsable source and active homepage/tracker links.

The upgrade does not modify GitHub, release tags, user files, repository visibility or official QGIS publication state.
