# Packaging and validation — NilePhytoDock Studio v1.0.0

Developers: **Ahmed G Soliman** and **Malak Taha**. First official public release. Historical validation records retain their original version numbers.

## Delivered Windows download

`NilePhytoDock-v1.0.0-Setup.exe`: **429,300,736 bytes** (429.30 MB; 409.41 MiB). One file is required to download. Setup automatically installs 4,341 payload files (947,544,387 bytes). Those runtime files are necessary for Python, Qt, scientific extensions and native engines. The hidden `_internal` directory is installed automatically. Researchers do not download or assemble it manually. Documentation stays outside the application interface.

SHA-256: `11a83003a28b399636366e61a2b066d8f93aa665a3cb810e6e6cae75c0ca3ac1`.

Installed EXE SHA-256: `876b11c470705e16efd48d7d3f66ee16f87212c862485415562781c938514873`.

## Packaging comparison

| Candidate | Size / files | Observed engine-ready startup |
| --- | --- | --- |
| Previous distribution | approximately 1.32 GB installed; 7,190 files; 693.68 MB ZIP | Not retrospectively timed with the new benchmark flag |
| PyInstaller folder candidate | 28.25 MB launcher plus runtime directory | 29.79 s first run; 16.44 s second run |
| PyInstaller one-file candidate | 440.79 MB; one EXE | 37.05 s and 46.36 s |
| Final setup / installed application | 429.30 MB; one setup download | 9.22 s and 9.43 s after installation |
| Nuitka 4.3.1 one-file | No successful candidate | Probe stopped at missing Windows dependency-analysis/compiler prerequisites; no timing or size claimed |

These are two-run observations on this Windows host, not controlled cold-boot or cross-machine benchmarks. Candidates were run on X:; the final application was installed in the standard LocalAppData Programs folder on C:. Timings include process creation, bundled-library loading, database loading and engine health checks. File caching, antivirus and drive speed affect them. The final setup installed in 18.39 seconds. Real one-file integration also succeeded; setup was selected to avoid repeated extraction and its startup cost. No scientific engine was replaced to reduce file count.

## Verification performed

- **67 automated tests passed**, including 20,000 additional saved runs in a private synthetic database, protocol/site isolation, structural alias deduplication, shared oil membership, duplicate target names and distinct-compound interaction counts.
- **54 own Python modules** in the final frozen archive matched the current source signatures.
- The final setup installed in `%LOCALAPPDATA%/Programs/NilePhytoDockStudio`. The installed EXE launched and loaded the library with developer paths and Python/Java environment variables removed.
- Real P2Rank 2.5.1 / Temurin 17.0.19+10 prediction completed on 3PTB. Each docking command used the actual selected P2Rank center and dimensions.
- Three real Smina 2020.12.10 calculations completed for the supplied HPLC curcuminoids: seed 20261029, exhaustiveness 1, CPU 2, one pose per run. This is an integration protocol, not an experimental-affinity validation.
- Final native verification checked actual 2D figures/contacts, offline 3D atom mapping, the dedicated 3D page and independent full-screen window.
- PDF, DOCX, XLSX, source-observation CSV and reproducibility JSON were generated. Oil-first results and functional-group summaries remained available. HPLC units and suppression of GC-style oil indices were checked.
- The final installed native engines worked in an output directory containing spaces and Unicode: `v1.0.0 Results Ω`.
- Scientific Charts contained **exactly three choices**. Initial loading issued one chart query; switching issued one query for the selected chart. Plotly rendered offline, no chart-page document scrollbar was needed, and a 10 ms Qt heartbeat continued during loading.

| Chart | Saved-data query | Native switch, including settling |
| --- | --- | --- |
| Bubble Plot | 0.0227 s | 0.423 s |
| Docking Heatmap | 0.0051 s | 0.963 s |
| Interaction Matrix | 0.0060 s | 0.932 s |

Each chart exported PNG, SVG, PDF, CSV, XLSX and JSON. Numeric CSV row counts matched plotted records. Measured chart-loading heartbeat gaps were below 24 ms in the final chart-page QA study. Export QA intentionally waited synchronously outside the production worker, so the global harness heartbeat is not an interactive export benchmark.

## Installer, data and confidentiality checks

Install/update/uninstall tests passed in a dedicated QA folder. Updating preserved the complete prior installation. Uninstall kept unknown research files. Setup rejected a nonempty unrelated folder. Default-folder testing exposed Windows' legacy path-length limit in long notice filenames; short filenames with an original-name index fixed it. Full license texts were retained. Final default-folder installation passed.

The seed SHA-256 remains `da0b0f27f59c4790d06b54ab8de56bed056a524f5514277b340620aec11da90e`; it contains zero user research projects. Working data were backed up before the final normal launch. Existing development and release artifacts were preserved. No database expansion was performed.

The payload passed filename and text/config/data scans for development/research logs, personal working databases, common credential tokens and private keys. The public CA certificate bundle is retained for HTTPS. No matching credentials were found. This is a scoped audit, not a proof against every possible encoding. Mandatory license and source-access notices remain installed. Source archives exclude user project outputs and unrelated development records.

## Public distribution

Product/download: https://github.com/ahmedGSoliman99/NilePhytoDock-Studio

Corresponding source and licensing: https://github.com/ahmedGSoliman99/NilePhytoDock-Source

The product repository is separate from the working development history. Required source access for current and earlier distributed builds remains public. See LICENSE_AUDIT.md and THIRD_PARTY_SOURCES.json. Native binaries were version/provenance identified and tested; a byte-for-byte rebuild of upstream binaries is not asserted. These tests used a restricted PATH on this host, rather than a clean Windows virtual machine.
