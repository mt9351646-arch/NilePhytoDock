# NilePhytoDock Studio v1.0.2 — Release validation

This record describes software release verification. It does not introduce a scientific method or relabel historical validation.

The automated suite passed 82 tests, including owned-process-tree cancellation, native priority/affinity limits, sequential task execution, one-request window closing, data handling and the existing scientific regression tests. One existing MDAnalysis deprecation warning remains.

The source application also completed the existing integration scenario and its 2D/3D, four-chart, export and retrieval checks. A separate lifecycle probe closed once while an owned native process was active: the process and queued work stopped, and the application loop exited. The same probe is required against the final installed executable.

## Comparative GUI probe

The same retained 20-compound study was copied into isolated databases for the v1.0.1 and updated source GUI probes on this Windows host (8 logical CPUs, approximately 32 GB RAM).

| Measurement | v1.0.1 | Updated source |
| --- | ---: | ---: |
| Idle process-tree RSS sum | 945.50 MB | 351.15 MB |
| Live-results phase peak RSS sum | 994.47 MB | 352.08 MB |
| Longest live-results GUI heartbeat gap | 8,484 ms | 79 ms |
| Molecular-view phase peak RSS sum | 1,458.34 MB | 930.15 MB |
| Longest molecular-view heartbeat gap | 1,016 ms | 157 ms |

RSS is summed across the process tree and may count shared pages more than once; it is not a physical-memory total. Heartbeat gaps measure the application event loop, not operating-system mouse latency. These bounded host measurements are comparative engineering evidence, not a guarantee for every dataset or computer. Final installed-application checks and artifact hashes are recorded separately after the actual build.

The seed catalog remains byte-identical (SHA-256 `da0b0f27f59c4790d06b54ab8de56bed056a524f5514277b340620aec11da90e`). Researcher working data and historical verification records are retained.

## Final installed package

The actual Setup was installed and its executable was exercised with PATH restricted to Windows system directories and developer Python/Java/Qt variables removed. The complete scenario passed: startup, catalog loading, existing native integration calculations, selected output folders containing spaces and Unicode, PDB retrieval, 2D vector/PNG saving, three distinct 3D cameras, readable high-resolution labels, connected contact endpoints, pocket-surface export, four lazy chart types and six export formats per chart, shared-group rendering, and PDF/DOCX/XLSX/CSV/reproducibility exports.

The separate installed-executable lifecycle test issued one close request during a native Java task. The application exited, with no remaining owned engines or queued tasks. This uses the same GUI cancellation path as normal closing. Native calculations were observed at below-normal Windows priority and two-core affinity.

- Installer: `NilePhytoDock-v1.0.2-Setup.exe`, 428,186,624 bytes; one required download.
- Packaging: PyInstaller folder payload inside the existing per-user .NET Framework Setup; runtime dependencies are installed automatically.
- Setup SHA-256: `9daa203dee97121f535d18f6bbf8afc5fadbfd289999f9adb51e92887b165408`.
- Installed application SHA-256: `58ca19ea0b3b8af5bffa46b9fcada9d4ddc8e9ac11e2cf2197d900f53bba087c`.
- Installation: 15.06 seconds on this host.
- Combined native/visual/lifecycle verification: 115.91 seconds.
- Owned-engine close latency: 0.015 seconds in the lifecycle probe.
- All 59 included application modules match the final source; all 20 own resource files match.
- Payload audit: no researcher projects, credentials matching the checked key patterns, development logs, fixtures, bytecode caches or environment files.

The executable is unsigned. Tests ran on this Windows host with restricted environment variables, not in a newly provisioned clean Windows VM; no broader hardware certification is claimed. Existing MDAnalysis deprecation and optional PyInstaller-module warnings did not prevent the tested functions. Historical failed/cancelled verification attempts are retained separately and are not presented as successful release evidence.
