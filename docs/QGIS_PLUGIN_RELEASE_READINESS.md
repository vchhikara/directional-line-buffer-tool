# QGIS Plugin Release Readiness

**Artifact:** `QGIS_PLUGIN_UPGRADED.zip`  
**Plugin:** Directional Line Buffer  
**Candidate version:** `0.3.1`  
**Date:** 2026-11-04  
**Status: BLOCKED for official repository submission. Structurally validated candidate for a controlled QGIS desktop installation test.**

## Verified release checks

| Check | Status | Evidence |
|---|---|---|
| Correct top-level QGIS plugin folder | **Passed** | `Directional_line_buffer_Tool/` is the only root inside ZIP |
| Metadata syntax and mandatory keys | **Passed static** | Parsed as UTF-8 INI and validated required keys |
| Plugin `classFactory` entry point | **Passed static/mock** | `__init__.py` unchanged; mocked class factory returns expected class |
| Runtime Python syntax | **Passed** | Python 3.13 AST parser; no syntax errors |
| LICENSE, README, icon, offline help | **Passed static** | Present in runtime ZIP; PNG header checked |
| Runtime ZIP resource presence | **Passed static** | 11 explicit allowlisted files present |
| No caches, compiled bytecode, path traversal, symlinks | **Passed** | ZIP validator and clean extraction validation |
| Reproducible packaging | **Passed** | Independently rebuilt ZIPs with the same SHA-256 |
| ZIP size within repository limit | **Passed** | 420,745 bytes vs published 25 MB limit |
| Automatic non-QGIS regressions | **Passed** | 37 passed, 0 failed, 3 native tests skipped |
| Actual QGIS install and GUI/geometry behavior | **NOT RUN** | No QGIS/PyQt runtime present |
| QGIS 3.30-3.x broad compatibility | **NOT ESTABLISHED** | Metadata scope only, not evidence of a tested range |
| QGIS 4 and Qt 6 support | **Excluded intentionally** | `qgisMaximumVersion=3.99`; QGIS 4 requires migration testing |
| Public GitHub source repository | **BLOCKED** | Connected GitHub identifies `vchhikara/directional-line-buffer-tool` as **private**; anonymous URL returned 404 |
| Public homepage and issue tracker | **BLOCKED** | Paths under the private repository are not anonymously usable |
| Public source matches submitted ZIP | **NOT VERIFIED** | No publication or source sync performed |
| Repository automated scanning, moderation, approval | **NOT RUN** | Requires explicit owner's publication actions |

## Metadata

`name=Directional Line Buffer`; `version=0.3.1`; `qgisMinimumVersion=3.30`; `qgisMaximumVersion=3.99`; `category=Vector`; `icon=icon.png`; `experimental=True`; `deprecated=False`. Description, about, author, email, homepage, source repository, tracker, tags and changelog are provided. No `server`, `hasProcessingProvider` or external plugin dependency is declared because those capabilities are absent.

Version `0.3.1` is intentionally a patch bump from `0.3.0` because it changes error handling, target selection and release behavior. This is **not** an automatic GitHub release or a claim that the official QGIS repository has accepted the plugin. Keeping `experimental=True` is appropriate pending real native validation.

## Required owner and QGIS actions, in order

1. **Run real QGIS 3 integration tests and an exact-ZIP smoke test.** Use a clean profile; verify `classFactory`, `initGui`, help, icon, drawing, directional sides, output layer, CRS transformation, right-click/double-click/Enter/Escape, undo, fallback, unload and reload. Record exact QGIS, Python, Qt, GEOS and OS versions. Test at least one representative supported QGIS 3 version; test additional platforms/versions before making broader compatibility claims.
2. **Make the source publicly browseable** or provide a verified public repository with the actual updated source. The current repo named in metadata is private. If using a different repository, update `repository`, `homepage` and `tracker` only to their verified real URLs.
3. **Confirm metadata ownership, license and icon rights** and publish the matching revised source in the indicated repository after review. Verify homepage README and issue tracker open without authentication. Do not upload merely the ZIP as the purported source.
4. **Confirm native provider edge cases:** writable target and different CRS; existing edits/undo; attribute constraints; invalid polygon output; plugin-owned vs unrelated memory layers; no duplicate writes after failed commit.
5. **Rebuild and inspect** the exact ZIP from the reviewed source. Keep the `version`, changelog and release tag aligned. Optional GitHub Actions CI can be enabled after committing `.github/workflows/validate.yml`; no real CI run occurred here.
6. **Only after all blockers clear**, submit the ZIP through the QGIS plugin repository using the owner account and comply with security scanning and approval. This assignment did **not** submit or publish anything.

## Official rules and significant differences from supplied guide

- Official [QGIS publishing requirements](https://plugins.qgis.org/docs/publish) specify minimum documentation, valid homepage/repository/tracker links, publicly accessible source, GPL-compatible license, no binaries and ZIP size under 25 MB. The package meets the checkable local portions, but **not the public repository portion**.
- Official [QGIS approval](https://plugins.qgis.org/docs/approval) includes security scanning and approval. Passing local static tests does not substitute for them.
- Official [QGIS 4 migration documentation](https://plugins.qgis.org/docs/migrate-qgis4) notes that QGIS 4 uses Qt 6. `qgisMaximumVersion=3.99` explicitly restricts this candidate to QGIS 3 rather than claiming untested QGIS 4 support.
- Official [QGIS plugin cookbook](https://doc.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/plugins.html) does **not** require the main module to be literally named `mainPlugin.py`. The supplied guide's table is overly strict on that point. Qt resources, UI compilation and translation catalogs are optional for this specific source layout.

## Release classification

**Not ready for official public distribution.** Two primary blockers remain: native QGIS functionality is untested, and the metadata's code repository/homepage/tracker are not public. No critical unresolved defects are known from the source/static audit, but that is not evidence that native integration is defect-free. The ZIP can now be used for a controlled installation and acceptance test.
