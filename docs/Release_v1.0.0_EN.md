# NilePhytoDock Studio v1.0.0

First official public release. Developed by **Ahmed G Soliman** and **Malak Taha**.

## Install and start

Download `NilePhytoDock-v1.0.0-Setup.exe` from the public [Windows release](https://github.com/ahmedGSoliman99/NilePhytoDock-Studio/releases/tag/v1.0.0). Run it, choose a dedicated writable installation folder, and select Install. Setup installs Python, Qt, the scientific libraries, Java, P2Rank and Smina automatically. Start NilePhytoDock Studio from its desktop or Start menu shortcut and wait for **Engines available**. No development environment or separate dependency installation is needed.

Windows 10/11 x64, 8 GB RAM and 4 GB available disk space are recommended; allow additional space for research outputs. A 1366 × 768 or larger display and working Windows graphics drivers are recommended. Calculations and molecular rendering work locally after installation. Optional online maintenance needs internet access. This release is unsigned; its published SHA-256 identifies the delivered download.

Documentation is stored in the installation's **Documentation** folder, outside the application interface. Runtime dependencies are installed automatically in the hidden `_internal` folder. They are required for the application. User settings and its working database remain under `%LOCALAPPDATA%\NilePhytoDock`; output studies are saved in the folder you select.

## Run a study

1. Open **Botanical library** and select analytical profiles. Read their source, extraction method, location, original units and eligibility notes. Source observations and ready molecular structures are different counts.
2. Import a PDB or mmCIF receptor in **Protein targets**. Inspect chains, missing residues, waters, ligands, metals and cofactors. Preparation choices affect the result.
3. In **Screening setup**, select a writable output folder and set the preparation and docking protocol. Identify bound residues to remove explicitly. `BEN A:1` applies to the supplied trypsin example, not arbitrary receptors.
4. Choose **Prepare and predict all**. Inspect the P2Rank pockets and select a site for each protein. Automatic mode transfers the selected pocket's actual center and dimensions to Smina; Custom box uses your recorded coordinates.
5. Choose exhaustiveness, seed, scoring function, CPU count and number of poses. Run screening and wait for completion. Per-run status distinguishes failed or incomplete calculations.
6. Open **Oil results**, select the protein and site, and inspect the best calculated compounds belonging to each selected oil profile. Shared compounds can occur in several oils. Aliases do not create additional structures.
7. Double-click a compound to inspect its actual docked pose in the independent 3D window. Use **F11** for presentation mode and **Esc** to restore controls. **2D interactions** is a separate page. Both views use saved pose geometry and detected contacts.
8. Open **Functional groups** for the selected protein. Group presence and direct atom participation are separate measurements. Small or redundant cohorts do not support enrichment claims.
9. Open **Scientific charts** and choose one of the three charts below. Only the selected chart is queried and rendered. Select protein, oil and optionally a binding site; Rows limits the displayed structures or residues.
10. Export results and reports. Preserve the complete study folder, including `Project_Data/project.nile.sqlite`, to reopen saved calculations with **Open Saved Project**.

## The three scientific charts

| Chart | What it shows |
| --- | --- |
| Bubble Plot | Actual docking score on the horizontal axis and compounds vertically. Oil colors distinguish source membership. Uniform bubbles avoid implying abundance from incomparable analytical units. Hover identifies oil, protein, pocket and exact score. Small vertical offsets separate shared membership without changing scores. |
| Docking Heatmap | Best saved compound–protein scores within one compatible docking protocol. Missing cells represent unavailable calculations. |
| Interaction Matrix | Protein residues versus detected interaction types in the selected best poses. Cells count distinct compounds; atom-pair events and minimum distances remain in the exported records. Counts are not binding strengths. |

The default limit is 20 structures or residues. Full records remain in results and reports. Long axes are bounded, the legend is compact, and filters run read-only queries in a worker thread. **Export** writes only the selected figure plus its plotted records: PNG, SVG, PDF, CSV, XLSX and JSON. Figure output supports 300 or 600 DPI. Chart filters do not rerun docking or alter the scientific database.

## Read results correctly

Docking scores are model predictions in kcal/mol, not experimental affinities, clinical effects or evidence of whole-oil activity. Compare within the same receptor, preparation, site and scoring protocol. More negative scores alone do not establish biological activity. Retained settings, engine versions and reproducibility metadata are required to interpret comparisons.

GC peak area percentages, absolute concentrations, trace observations and HPLC measurements retain their original meanings. Concentration-based and headspace profiles do not receive a GC-based oil index. Missing structures, incomplete calculations and source coverage must be considered. Functional groups and interactions describe the prepared pose; protonation, receptor selection and geometry affect classifications. Schematic 2D lengths are not distances; displayed distance values come from 3D coordinates.

The v1.0.0 optimization changes packaging and the charts page. It does not expand the library, change docking algorithms, or replace existing interaction/functional-group calculations. The seed remains 57 botanical oils (46 essential and 11 fixed), 119 analytical profiles, 819 normalized compound-name records and 164 distinct ready InChIKeys. These counts do not imply that every compound is ready to dock.

## Output and troubleshooting

Reports include PDF, DOCX, XLSX, source observations and reproducibility JSON. Existing 2D SVG/PNG, 3D PNG and molecular-structure exports remain available. Native PSE export still requires a legitimate separately installed PyMOL; PDB/SDF/PML exports do not require it.

Use a writable folder with sufficient free space. Study folders can contain spaces and Unicode characters; native-engine temporary work uses an ASCII-compatible Windows location. If a run fails, inspect its recorded status and per-run process log in your study output. Do not delete a study folder until its reports and saved project have been backed up. Application-generated research logs are output data; setup does not distribute development logs or previous research projects.

To update, close the application and run Setup. An existing recognized installation is retained as a timestamped previous folder. Setup does not overwrite an unrelated nonempty folder. Uninstall through Windows Installed apps. Uninstall removes only manifest-owned installed files and keeps unrecognized research files and the user database/settings.

## Licensing and source access

NilePhytoDock source is GPL-3.0-or-later. Third-party components retain their licenses and mandatory notices. There is no restriction on reverse engineering required to debug modifications to LGPL components. Installed Qt libraries remain separate replaceable DLLs. Corresponding application source, packaging scripts, dependency source archives and rebuild instructions are available without authentication at [NilePhytoDock Source](https://github.com/ahmedGSoliman99/NilePhytoDock-Source). See the installed `Documentation/SOURCE_ACCESS.md` and `Documentation/LICENSES.md`.

## Release changes

- One Windows setup download; bundled Python, Qt, scientific libraries, Java, P2Rank and Smina.
- A minimal Scientific Charts workspace with Bubble Plot, Docking Heatmap and Interaction Matrix only, selected-chart loading and retained numerical exports.
- Consistent v1.0.0 application and executable metadata; original logo and English interface.
- A separate public product/download page and legally required source access. Historical development and validation records retain their original versions.
