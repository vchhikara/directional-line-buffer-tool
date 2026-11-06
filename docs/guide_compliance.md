# Development guide compliance and interpretive decisions

Authoritative user guide: `qgisplugindoc.md` supplied with the request. Cross-checked against the current official online [QGIS 3.44 PyQGIS plugin cookbook](https://doc.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/plugins.html), [QGIS 3.44 vector editing cookbook](https://documentation.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/vector.html), [QGIS `QgsGeometry`](https://api.qgis.org/api/3.44/classQgsGeometry.html) reference, [QGIS repository publishing rules](https://plugins.qgis.org/docs/publish) and [approval rules](https://plugins.qgis.org/docs/approval) (checked 2026-11-04).

| Guide topic | Decision |
|---|---|
| `metadata.txt`, `__init__.py`, `classFactory` | Mandatory; existing identifiers preserved. |
| `mainPlugin.py` | **Example filename, not mandatory**; preserve valid `directional_line_buffer.py`. |
| `initGui`, `unload` | Required lifecycle; make registration idempotent and disposal explicit. |
| `LICENSE` | Included; GPL-3.0-or-later is compatible with official repository licensing guidance. |
| `form.ui`, `form.py` | Optional; Qt widgets built directly in Python. |
| `.qrc` and compiled `resources.py` | Optional; filesystem PNG icon is sufficient. No `.qrc` compilation. |
| `index-en.html`, `showPluginHelp` | Optional but added because local help improves usability. |
| `i18n`, `.ts`, `.qm`, `.pro`, `pylupdate5` | Optional. Translatable strings are improved; **no empty or fabricated translations**. Guide's strict two-letter naming example is a convention for a particular workflow, not a universally mandatory pattern. |
| `qgisMaximumVersion` | Optional; explicitly `3.99` to prevent false QGIS 4 compatibility claims. The [official QGIS 4 migration guide](https://plugins.qgis.org/docs/migrate-qgis4) confirms `3.99` means QGIS 3 only and `4.99` would require Qt 6 testing. |
| `plugin_dependencies`, `server`, `hasProcessingProvider` | Omitted because plugin uses none of these capabilities. |
| `QgsGeometry.singleSidedBuffer` | Official signature supports left/right directional buffering, miter joins and miter limit. Exact real-QGIS behavior remains unverified locally. |
| `qgis-plugin-ci` | Optional automation tool; deliberately not adopted. Lightweight stdlib checks and a ZIP script suffice for now. |
| Official repository | Requires license, minimal docs, valid metadata URLs, public readable repository, non-binary ZIP under 25 MB and license compliance. Approval/security scan are external steps, **not completed** by this source upgrade. |

The uploaded guide's metadata example uses Markdown-formatted URLs in its demonstration values. Actual `metadata.txt` must use plain URLs, as the original file correctly did. The guide calls `mainPlugin.py` required in a table but the official cookbook describes it as *core code* in an example, and `classFactory` dynamically imports the actual module; renaming would be unnecessary and possibly disruptive.
