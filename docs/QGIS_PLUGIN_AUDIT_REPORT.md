# QGIS Plugin Audit Report

**Plugin:** Directional Line Buffer  
**Baseline:** Uploaded `Directional_line_buffer_Tool-0.3.0-new-icon.zip` (version `0.3.0`)  
**Revised release candidate:** `0.3.1`  
**Audit date:** 2026-11-04  
**Scope:** Entire eight-file ZIP, supplied `qgisplugindoc.md`, verified QGIS documentation, source changes and offline test results.

## Verdict

The original plugin has a valid minimal QGIS Python plugin entry point, a populated metadata file, a compatible GPL-3.0-or-later license, and a recognizable, functional design. It is **not adequately verified for official release**. The highest-risk observations are indiscriminate reuse of an existing layer named `Directional buffer`, geometry coordinates becoming ambiguous if the project CRS changes mid-operation, and ambiguous commit outcomes triggering unintended fallback copies. These are code-level findings, not claims of demonstrated data loss in an actual QGIS session.

Most feasible defects have been corrected in the source release candidate. **Real QGIS load, geometry output, UI and transactions remain unverified because this environment does not contain QGIS/PyQt.** The listed GitHub repository exists as a **private** repo in the connected account; anonymous public access to its URL returned HTTP 404. This is a definite official-submission blocker until resolved.

## Original ZIP inventory

| File | Purpose | Original status |
|---|---|---|
| `Directional_line_buffer_Tool/__init__.py` | `classFactory(iface)` imports/returns `DirectionalLineBuffer` | Valid entry point |
| `directional_line_buffer.py` | Plugin lifecycle, toolbar/menu action, CRS guard, parameter dialog | Main implementation (correct nonstandard filename) |
| `buffer_dialog.py` | Native `QDialog` with distance spin box and side selector | No `.ui` requirement |
| `map_tool.py` | `QgsMapTool` events, rubber bands, GEOS buffer, output writes | Principal GIS and safety risk concentration |
| `metadata.txt` | QGIS name, version, links, QGIS min, description, icon, category | Parsable, links not public |
| `README.md` | Installation, existing behavior, limits | Incomplete for release |
| `LICENSE` | GNU General Public License v3 text, ~35 KB | Compatible with GPLv2-or-later requirement |
| `icon.png` | 1254 × 1254 RGBA PNG, ~471 KB | Valid, retained unchanged |

The original ZIP contains no nested extra plugin directory, test suite, QGIS Processing provider, translations, Qt `.ui`, `.qrc`, `resources.py`, other compiled assets, `Makefile`, CI config, external Python dependencies, or `.git` history. No optional file is missing merely because a template lists it.

**Original symbols:** `DirectionalLineBuffer` with `__init__`, `tr`, `initGui`, `unload`, `start`; `BufferDialog` with `__init__`, `distance_meters`, `side`; `DirectionalBufferMapTool` with map mouse/keyboard handlers, `_line_points`, `refresh_preview`, `make_buffer`, `finish`, `create_output`, `target_layer`, `build_feature`, `prepare_geometry`, `add_feature`, `temp_layer`, `ensure_fields`, `warn`, `reset_drawing`, `cancel`, and `deactivate`. Entry point is `classFactory`. No native extension or external package is imported. The plugin depends on Qt via `qgis.PyQt`, QGIS core and GUI APIs, and GEOS-backed QGIS geometry methods.

## Findings

Original line numbers are used to preserve audit evidence against the uploaded ZIP. **Fixed (source)** means implemented and covered by a static/unit/mock test where possible, **not** proven to work in a real QGIS application.

| ID | Severity | Classification / category | Original location and direct evidence | Impact and remediation | Status |
|---|---|---|---|---|---|
| DLB-001 | **High** | Confirmed code defect, integrity | `map_tool.py:177-202`: any existing polygon layer *named* `Directional buffer` is returned and passed to `ensure_fields()` | Unrelated layer may have columns added. Create/reuse only plugin-tagged memory layers, and modify fields only on those layers. | **Fixed (source)**, mocked regression passed |
| DLB-002 | **High** | Confirmed code defect, CRS integrity | `directional_line_buffer.py:51-58`, `map_tool.py:151-158`: CRS checked once at start; output transform reads project CRS again | Mid-operation project CRS change can reinterpret digitized points. Freeze the original CRS; abort if project or canvas CRS changes. | **Fixed (source)**, mocked regression passed |
| DLB-003 | **High** | Confirmed risk, write integrity | `map_tool.py:163-175,112-125`: broad `except Exception` returns `False` and triggers temporary fallback | A failed commit can leave provider state uncertain, and fallback can create a duplicate polygon. Preserve diagnostic, classify uncertain commit, never auto-retry uncertain output. | **Fixed (source)**; provider semantics require QGIS integration test |
| DLB-004 | Medium | Confirmed code defect, digitizing | `map_tool.py:45-64,99-104`: repeated vertices added and only count `>=2` tested | Degenerate or duplicated line geometry. Deduplicate successive points; require two distinct finite coordinates and positive length. | **Fixed (source)**, independent validation tests passed |
| DLB-005 | Medium | Confirmed cleanup gap, Qt | `directional_line_buffer.py:39-49,65-74`, `map_tool.py:32-42`: bands never explicitly disposed | Canvas items may accumulate after repeated starts/reloads. Idempotent `dispose`, Qt scene removal, `deleteLater` and action disconnection. | **Fixed (source)**, mock lifecycle test passed; native UI still unverified |
| DLB-006 | Medium | Confirmed risk, destination selection | `map_tool.py:128-139`: writes to `iface.activeLayer()` at *finish* | User switching active layer while drawing may redirect output. Freeze intended layer at activation, check it remains registered, show intended destination before drawing. | **Fixed (source)**, mock test passed |
| DLB-007 | Medium | Confirmed maintainability/API risk | `directional_line_buffer.py:53`: `crs.mapUnits() != 0` | Assumes undocumented numeric enum meaning. Replace with `QgsUnitTypes.DistanceMeters`. | **Fixed (source)**, API reference corroborated |
| DLB-008 | Medium | Confirmed usability risk, editing | `map_tool.py:165-169`: no distinct edit command for already-editable target | Harder to undo only this insertion. Add begin/end/destroy edit commands; preserve the user's overall edit buffer. | **Fixed (source)**, mock test passed |
| DLB-009 | Medium | Confirmed risk, failure handling | `map_tool.py:93-110,151-175`: geometry and CRS transform errors have weak reporting | Possible unhandled errors or ambiguous no-output failures. Add geometry guards, errors in QGIS message bar/log, preserve line when output fails. | **Fixed (source)**; native exceptions need testing |
| DLB-010 | Medium | Confirmed risk, memory CRS/fields | `map_tool.py:187-201`: memory layer creation depends on `crs.authid()` and field-creation return is unchecked | Custom projected CRS may have no authority ID; partial output schema possible. Create memory polygon layer independently, set its CRS, and check required fields. | **Fixed (source)**, mocked validation passed |
| DLB-011 | Medium | Confirmed gap, testability | Original ZIP has no test files | No reproducible regressions. Add QGIS-independent validation, mocked lifecycle/output tests, optional GEOS reference tests and native PyQGIS integration tests. | **Fixed (suite added)**, native tests skipped |
| DLB-012 | Low | Confirmed gap, documentation | `README.md:1-59`: limited help and workflow examples | User cannot readily diagnose provider writes or unit pitfalls. Rewrite README; add `index-en.html`, `DEVELOPMENT.md`, `CHANGELOG.md`. | **Fixed (source)** |
| DLB-013 | Low | Confirmed gap, release process | Original archive has no build/release automation | Output not reproducible; packaging errors go undetected. Add validated standard-library ZIP script and CI checks; patch bump `0.3.1`. | **Fixed (source)**, two identical ZIP hashes |
| DLB-014 | Low | Enhancement, i18n | `buffer_dialog.py:7-29`, `map_tool.py:204-205`: literal UI strings | Less ready for future translation. Add translation wrappers for main dialog and actions; no empty language files. | **Partially addressed**, complete localization deferred as optional |
| DLB-015 | **High** | Confirmed external blocker, repository | `metadata.txt:14-16`: linked repo `https://github.com/vchhikara/directional-line-buffer-tool` | Anonymous retrieval yielded 404; connected GitHub reports the repository as private. Official QGIS repo requires publicly browseable source. | **Blocked: owner action** |
| DLB-016 | Medium | Compatibility boundary | Original metadata omitted `qgisMaximumVersion`; source uses QGIS3/Qt5-era APIs | QGIS 4 supports Qt 6 and requires its own verification; do not imply 4.x support. Declare `qgisMaximumVersion=3.99`. | **Scoped to QGIS 3**, QGIS 4 support deferred |
| DLB-017 | Medium | Untested risk, specialized output layers | `map_tool.py:141-160`: generic polygon converted to multi only when necessary | Z/M-required providers, field constraints, transactional providers, and exotic CRS transforms may reject features. Remain explicit and fail safely; integration tests required. | **Deferred pending native QGIS** |
| DLB-018 | Low | Untested risk, performance | `map_tool.py:54-57,78-91`: buffer preview regenerated on pointer moves | Potential responsiveness issues on long polylines; no representative benchmark available. Avoid speculative rearchitecture. | **Deferred**, no claim of speed-up |

## Metadata assessment

- `name`, `description`, `about`, `version`, `author`, `email`, `repository`, and `qgisMinimumVersion` are supplied and parse as expected. Author details and URLs were preserved verbatim from the original ZIP.
- `category=Vector`, `icon=icon.png`, `experimental=True`, `deprecated=False`, `tags`, `changelog`, `homepage`, and `tracker` exist. Existing icon PNG signature and dimensions checked.
- `version` is now `0.3.1` to identify the safety-fix release candidate; changelog updated.
- `qgisMaximumVersion=3.99` now explicitly excludes untested QGIS 4. The official QGIS 4 migration documentation confirms this range.
- `plugin_dependencies`, `server`, and `hasProcessingProvider` are omitted because their functionality is absent. No `qgis-plugin-ci` requirement was discovered.
- Author and contact details are supplied by the owner in the original package but their identity/consent is not independently verified.
- **Public repository/homepage/tracker availability fails at present** because the repository is private. No URLs were fabricated or silently replaced.

## Guide versus official sources

1. User guide marks `mainPlugin.py` *required*, but the official QGIS 3.44 plugin cookbook uses it as an example of the main module. The actual `classFactory()` correctly imports `directional_line_buffer.py`. **No rename** is justified.
2. GUI `.ui`, Python UI compilation, `.qrc`/compiled Qt resources, and a full translation tree are optional. A Python-defined dialog and local PNG work without them. Do not manufacture placeholders.
3. The user guide describes strict `plugin_XX.ts` locale filename naming. That is a sample project convention, not a mandatory prerequisite when no translations exist. Translatable source strings remain useful.
4. Help HTML is a supported, useful optional capability. Offline `index-en.html` was added and is invoked through `showPluginHelp(packageName=__package__)`.
5. Minimum QGIS `3.30` was retained rather than speculatively lowered. A maximum `3.99` was added as a compatibility guard for the new QGIS 4/Qt 6 ecosystem.
6. The metadata examples in the supplied Markdown contain Markdown-formatted URL examples; actual metadata correctly uses plain URLs.
7. `qgis-plugin-ci` is optional; the lightweight reproducible package script meets this project's local needs without repository credentials.
8. Official repository acceptance also requires public source, minimum documentation, compatible licensing, metadata links, automated security scanning and approval. These are **not** automatically satisfied by source cleanup.

## Evidence and reference URLs

- Supplied user guide: `qgisplugindoc.md`, sections 1-7.
- Official QGIS 3.44 plugin cookbook: https://doc.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/plugins.html
- Official QGIS 3.44 editing cookbook: https://documentation.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/vector.html
- QGIS 3.44 geometry API: https://api.qgis.org/api/3.44/classQgsGeometry.html
- Repository requirements: https://plugins.qgis.org/docs/publish
- Repository approval/security: https://plugins.qgis.org/docs/approval
- QGIS 4 migration and compatibility declaration: https://plugins.qgis.org/docs/migrate-qgis4

See `QGIS_PLUGIN_UPGRADE_REPORT.md` and `QGIS_PLUGIN_TEST_REPORT.md` for implementation-level detail and test classification. Actual QGIS availability was checked locally and was absent.
