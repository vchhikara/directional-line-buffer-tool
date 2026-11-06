# QGIS Plugin Test and Verification Report

**Candidate:** Directional Line Buffer `0.3.1`  
**Date:** 2026-11-04  
**Result:** Offline tests pass. **Actual QGIS installation and runtime integration were not verified.**

## Test environment

| Component | Actual environment |
|---|---|
| Operating system | Debian GNU/Linux 13 (`trixie`) |
| Python | CPython 3.13.5 |
| QGIS application / PyQGIS | **Not installed / unavailable** |
| Qt / qgis.PyQt | **Not installed / unavailable** |
| Shapely (test-only reference) | 2.1.2 |
| GEOS used by Shapely | 3.13.1 |
| Test runner | `python -m unittest` (standard library) |
| QGIS target metadata | `qgisMinimumVersion=3.30`; `qgisMaximumVersion=3.99`; **neither endpoint was runtime tested** |

The independent Shapely GEOS library is not a runtime dependency of the plugin. Its tests illustrate expected planar buffer orientation and geometry. **They do not prove QGIS `QgsGeometry` behavior or QGIS provider output.**

## Commands executed

From `QGIS_PLUGIN_SOURCE.zip`'s project root:

```bash
python3 scripts/validate_plugin.py Directional_line_buffer_Tool
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/package_plugin.py --source Directional_line_buffer_Tool --output /mnt/data/QGIS_PLUGIN_UPGRADED.zip
python3 scripts/validate_plugin.py Directional_line_buffer_Tool --zip /mnt/data/QGIS_PLUGIN_UPGRADED.zip
```

Also executed: clean extraction of `QGIS_PLUGIN_UPGRADED.zip` into a separate temporary directory, followed by `validate_tree(extracted_plugin, reject_cache=True)` and `validate_zip(archive)`. A second deterministic packaging run was performed and the resulting SHA-256 hashes compared.

**Final suite: 40 tests discovered, 37 passed, 0 failed, 3 skipped.** Some tests exercise fake QGIS interfaces, not real QGIS. One intermediate first run failed a source-tree test because running Python created `__pycache__`; the validator was corrected to tolerate caches in the development tree while rejecting caches from the release ZIP. After correction, the full suite passed with no remaining failures.

## Executed test groups

| Test file | Cases | Pass | Fail | Skip | What it establishes |
|---|---:|---:|---:|---:|---|
| `tests/test_validation.py` | 12 | 12 | 0 | 0 | Pure parameter/vertex validation, duplicates, invalid values, ordering |
| `tests/test_mock_qgis.py` | 13 | 13 | 0 | 0 | Control-flow against **test doubles**: buffer API dispatch, destination freeze, temp ownership, guarded commits, CRS cancellation, action lifecycle |
| `tests/test_geos_reference.py` | 5 | 5 | 0 | 0 | Shapely/GEOS geometric reference for signed sides, reversed direction, area, corner validity |
| `tests/test_package.py` | 7 | 7 | 0 | 0 | Static source/metadata/help expectations; ZIP traversal and duplicate-name rejection |
| `tests/test_qgis_runtime.py` | 3 | 0 | 0 | **3** | Real QGIS geometry orientation, reversal, plugin action/scene lifecycle, memory output |
| **Total** | **40** | **37** | **0** | **3** | Excludes unperformed interactive GUI tests |

## Static and archive evidence

- All runtime Python modules parsed successfully with Python 3.13.5 AST and passed syntax checks.
- `metadata.txt` decoded as UTF-8 and parsed as INI. Required fields, version syntax, category, experimental/deprecated flags, and icon file existence were checked.
- Plugin root and `classFactory` source checked.
- PNG signature and nonzero pixel dimensions checked (1254 × 1254 RGBA input icon retained).
- Release ZIP contains exactly one top-level `Directional_line_buffer_Tool/` folder and an allowlisted set of 11 runtime files.
- ZIP has no development caches, compiled Python, test suite, CI files, external URLs, symlinks or traversal paths.
- Fresh extraction of runtime ZIP into a clean directory passed the same tree checks in strict mode.
- Reproducibility: two independent packaging runs yielded identical byte streams, SHA-256 `4861b474fa7c035c18cad6d60573b6e4cfa930ed3266d201896b725974a701e4` for the runtime ZIP used in this run.
- Runtime ZIP size at validation: 420,745 bytes, below QGIS's published 25 MB maximum.
- No vulnerability scan from the official QGIS repository was run; none was claimed.

## Not executed, limitations and corrective instructions

**Actual PyQGIS runtime tests: skipped, not passed.** No `qgis` binary, `qgis_process`, QGIS Python package or native `qgis.PyQt` was available in the test environment.

Native test script is included. In an environment with QGIS 3 and a configured QGIS Python interpreter:

```bash
# Set the environment for your actual QGIS install (do not use a generic
# virtualenv that lacks qgis.core / qgis.gui).
export QT_QPA_PLATFORM=offscreen
python3 -m unittest discover -s tests -p 'test_qgis_runtime.py' -v
```

On Linux, `xvfb-run -a python3 -m unittest discover -s tests -p 'test_qgis_runtime.py' -v` is an alternative if Qt's offscreen platform plugin is unavailable. These commands have **not been executed in a QGIS-equipped environment** in this audit.

The following remain **unverified** and require real QGIS integration/manual testing:

1. QGIS plugin discovery, exact ZIP installation, `classFactory`, actual toolbar/menu/help behavior, UI and high-DPI rendering.
2. QGIS `QgsGeometry` area/side accuracy for normal, reversed, bent and invalid inputs; handling of multipart output.
3. Source/target CRS transforms and geographic/projected unit rejection under QGIS 3.30+.
4. Edits to writable target layers, already-editable layers, undo, provider constraints and partial transaction commits.
5. Actual canvas mouse, keyboard and double-click event handling, map rubber-band disposal and repeat activation.
6. Windows/macOS installations, different versions of QGIS/Python/Qt and QGIS 4/Qt 6 compatibility (QGIS 4 is expressly excluded).
7. UI responsiveness and performance of very long lines; no before/after performance numbers were fabricated.

## Coverage

Line/branch coverage percentage **not measured**. The tests exercise validation code and representative mocked QGIS control-flow, but they cannot cover the actual C++-backed PyQGIS geometry and Qt integration without QGIS. No coverage percentage is asserted.

## Validation interpretation

The produced runtime ZIP is **structurally valid according to the implemented static checks and ready for a controlled installation test**. It is **not represented as a runtime-tested plugin** and is **not certified for public release**.
