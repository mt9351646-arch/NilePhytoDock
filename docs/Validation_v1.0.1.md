# NilePhytoDock Studio v1.0.1 — verification

Verified on Windows 11 x64 on 2026-10-30. Developers: **Ahmed G Soliman** and **Malak Taha**. This is a maintenance release; v1.0.0 remains the first official public release. Earlier validation records retain their original versions.

## Final installer and native regression

The final single-file Setup was installed into the normal per-user application folder. The installed EXE then ran with only Windows system directories on PATH and with developer Python, Java and Qt environment overrides removed. Its data folder and study output were isolated from the researcher's working database; the selected output path contained spaces and Ω.

- Setup: 429,361,152 bytes; one researcher download; PyInstaller scientific runtime inside the existing source-provided per-user .NET Framework installer.
- Setup SHA-256: `9f01a6f7a1073ca126ac18c98f982466aaf25fa81af2769dfd2fc4e2b26781eb`.
- Installed application SHA-256: `324e2bc7dbcce7ea0a336026ffe522911816f2c78a1f31af3e064999d9c5ed4c`.
- Installation: 11.83 seconds. Full native calculation and visual/export verification: 88.20 seconds. This is not a cold-start benchmark.
- Real P2Rank 2.5.1 prediction using bundled Temurin Java 17.0.19+10, followed by three actual Smina 2020.12.10 docking calculations against 3PTB using the retained HPLC curcuminoid profile. Validation settings: seed 20261029, exhaustiveness 1, CPU 2, one mode. These smoke-test settings are not a recommended production protocol.
- All three runs completed; the command-line boxes matched the saved pocket boxes. HPLC units were preserved and the GC oil index was suppressed.
- PDF, DOCX, XLSX, CSV and reproducibility JSON reports existed, with the current application version recorded correctly.
- PDB retrieval from a pasted RCSB structure URL succeeded through the real installed GUI callback.
- The Save 2D figure button saved a 300 DPI PNG and vector SVG into the selected Unicode path.
- The default 3D composition displayed the full protein cartoon and ligand. Binding-site and computed pocket-surface views worked. Front, Right and Top exports differed, retained the selected camera, and produced 2400 × 1800 PNGs with resolution-scaled labels. Exported surfaces were present.
- The displayed pose had 54 detected atom/feature contacts, 15 residue/category records and seven non-VdW summary links. Every displayed summary endpoint had visible ligand/receptor atoms and visible covalently connected receptor context, including when emphasis was disabled. Unaggregated contacts remain available through All atom contacts and the raw exports. Centroid endpoints are feature locations, not additional atoms; their ring guides are explicit.
- All four lazy chart selections rendered and exported PNG, SVG, PDF, CSV, XLSX and JSON. Final native queries took 0.0069–0.0093 seconds; switching plus exports took approximately 0.34–0.94 seconds in this warmed test. The unit suite also checks bounded read-only queries with 20,000 additional synthetic saved runs.
- Shared-group analysis drew Ketone in all three unique analyzed structures, with actual highlighted compound examples. A separate retained 20-structure verification study checked shared Ether drawings, multiple oil memberships and real aromatic contacts.

## Regressions and scientific boundaries

The full unit suite passed **77 tests**. The existing MDAnalysis deprecation warning remains. All 58 application modules matched the final PyInstaller code archive. The supplied runtime-specific ssl source also matched its frozen module.

The packaged network test exposed a missing 906-byte public certificate distrust policy required by the supplied Python ssl module. The original policy was included unchanged at the frozen runtime root; verified HTTPS then succeeded. Certificate verification was not disabled and Windows trust stores were not changed. The module, policy, PSF license and rebuild explanation are supplied with corresponding source. The failed candidate evidence remains separate from the successful final run.

Protein and ligand covalent bonds now render from the already validated chemistry graphs, rather than relying on a second PDB bond-perception pass. Atom identities, coordinates and saved interaction distances were verified without moving endpoints to make a picture look connected. The 2D layout is schematic. VdW nodes omit spokes; specific categories use minimum-distance residue/category links. Docking Network radius is `1 + (score − minimum displayed score)` within one target/protocol; this is a score map, not an angstrom distance or experimental affinity.

The scientific seed SHA-256 remains `da0b0f27f59c4790d06b54ab8de56bed056a524f5514277b340620aec11da90e`: 57 botanical oils, 119 profiles, 819 compound-name records and 164 distinct ready structures. No database expansion, new docking algorithm or new interaction classifier was introduced. These tests establish software execution, geometric consistency and export behavior; they do not establish experimental binding or whole-oil efficacy. This was a restricted-environment test on the development host, not a clean-VM certification.

Maintainer test logs, process records and generated figures are retained locally under `data/validation` and the isolated release-QA output. Public product screenshots are real application captures; user research databases and raw working records are excluded from the download repositories.
