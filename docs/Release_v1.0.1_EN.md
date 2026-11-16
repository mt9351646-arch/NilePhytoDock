# NilePhytoDock Studio v1.0.1

Maintenance update to the first official public release v1.0.0. Developed by **Ahmed G Soliman** and **Malak Taha**.

## Install and start

Download `NilePhytoDock-v1.0.1-Setup.exe` from the public [Windows release](https://github.com/ahmedGSoliman99/NilePhytoDock-Studio/releases/tag/v1.0.1). Run it, choose a dedicated writable installation folder, and select Install. Setup installs Python, Qt, the scientific libraries, Java, P2Rank and Smina automatically. Start NilePhytoDock Studio from its desktop or Start menu shortcut and wait for **Engines available**. No development environment or separate dependency installation is needed.

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

## Scientific charts

| Chart | What it shows |
| --- | --- |
| Bubble Plot | Actual docking score on the horizontal axis and compounds vertically. Oil colors distinguish source membership. Uniform bubbles avoid implying abundance from incomparable analytical units. Hover identifies oil, protein, pocket and exact score. Small vertical offsets separate shared membership without changing scores. |
| Docking Heatmap | Best saved compound–protein scores within one compatible docking protocol. Missing cells represent unavailable calculations. |
| Docking Network | A radial protein–ligand score map, colored by oil. Radius is 1 + (score − the minimum displayed score), so more negative scores lie closer. Distances are score differences, not angstroms or experimental affinities. Equal scores have equal radius. The view shows one protein at a time; choose the Protein filter to switch. Shared oil memberships are separate nodes. Labels use aligned callouts for up to 32 nodes; larger views use hover. Up to 80 oil memberships are plotted; filter by oil to inspect additional memberships. |
| Interaction Matrix | Protein residues versus detected interaction types in the selected best poses. Cells count distinct compounds; atom-pair events and minimum distances remain in the exported records. Counts are not binding strengths. |

The default limit is 20 structures or residues. Full records remain in results and reports. Long axes are bounded, the legend is compact, and filters run read-only queries in a worker thread. **Export** writes only the selected figure plus its plotted records: PNG, SVG, PDF, CSV, XLSX and JSON. Figure output supports 300 or 600 DPI. Chart filters do not rerun docking or alter the scientific database.

## Read results correctly

Docking scores are model predictions in kcal/mol, not experimental affinities, clinical effects or evidence of whole-oil activity. Compare within the same receptor, preparation, site and scoring protocol. More negative scores alone do not establish biological activity. Retained settings, engine versions and reproducibility metadata are required to interpret comparisons.

GC peak area percentages, absolute concentrations, trace observations and HPLC measurements retain their original meanings. Concentration-based and headspace profiles do not receive a GC-based oil index. Missing structures, incomplete calculations and source coverage must be considered. Functional groups and interactions describe the prepared pose; protonation, receptor selection and geometry affect classifications. Schematic 2D lengths are not distances; displayed distance values come from 3D coordinates.

This update repairs coordinate retrieval and improves molecular figures, adds the requested docking network and draws shared functional groups. It does not expand the library, change docking algorithms, or replace existing interaction/functional-group calculations. The seed remains 57 botanical oils (46 essential and 11 fixed), 119 analytical profiles, 819 normalized compound-name records and 164 distinct ready InChIKeys. These counts do not imply that every compound is ready to dock.

## Output and troubleshooting

Reports include PDF, DOCX, XLSX, source observations and reproducibility JSON. Existing 2D SVG/PNG, 3D PNG and molecular-structure exports remain available. Native PSE export still requires a legitimate separately installed PyMOL; PDB/SDF/PML exports do not require it.

Use a writable folder with sufficient free space. Study folders can contain spaces and Unicode characters; native-engine temporary work uses an ASCII-compatible Windows location. If a run fails, inspect its recorded status and per-run process log in your study output. Do not delete a study folder until its reports and saved project have been backed up. Application-generated research logs are output data; setup does not distribute development logs or previous research projects.

To update, close the application and run Setup. An existing recognized installation is retained as a timestamped previous folder. Setup does not overwrite an unrelated nonempty folder. Uninstall through Windows Installed apps. Uninstall removes only manifest-owned installed files and keeps unrecognized research files and the user database/settings.

## Licensing and source access

NilePhytoDock source is GPL-3.0-or-later. Third-party components retain their licenses and mandatory notices. There is no restriction on reverse engineering required to debug modifications to LGPL components. Installed Qt libraries remain separate replaceable DLLs. Corresponding application source, packaging scripts, dependency source archives and rebuild instructions are available without authentication at [NilePhytoDock Source](https://github.com/ahmedGSoliman99/NilePhytoDock-Source). See the installed `Documentation/SOURCE_ACCESS.md` and `Documentation/LICENSES.md`.

## Retrieve a protein by ID

In **Protein targets**, select **Retrieve PDB ID**. Enter a code such as `3PTB`, an extended `pdb_` identifier, or an RCSB structure URL. Surrounding spaces are accepted. Legacy PDB coordinates are tried first when available, with mmCIF and a PDBe fallback. Downloads are parsed before being imported; server error pages are never saved as protein files. Internet access is required. Structures are unmodified on download; inspect preparation and select the biologically relevant chains/site before docking. The retrieval format does not remove preparation limits for very large or chemically unusual structures.

## Save clear molecular figures

Open a calculated compound, then choose **2D interactions**. **Save 2D figure** directly saves a 300 DPI PNG with its SVG companion, or an SVG vector file. Zoom and Fit controls remain beside the save button. **More controls** opens styles, residue colors, contact tables and molecular exports. The default Interaction map places the chemical structure among compact typed residue circles. Green links identify hydrogen bonds, pink links hydrophobic contacts, and the legend shows only categories present. Van der Waals contacts appear as pale nodes without extra spokes. Other categories have one link per residue/type; optional labels show the minimum measured 3D distance. The complete event counts and atom mappings remain in source tables and SVG metadata. Classic, Circular and Functional group drawings remain under More controls. This presentation does not substitute BIOVIA interaction rules for the existing ProLIF calculations.

In **3D viewer**, choose **Front**, **Back**, **Left**, **Right**, **Top** or **Bottom**, use Rotate/Tilt, or drag to rotate freely. **Auto rotate** can be stopped before choosing an image. **Fit binding site** includes the ligand and nearby receptor atoms. Open the separate 3D window for the largest canvas. The initial Protein + ligand view shows the complete receptor as a secondary-structure cartoon with the docked ligand. Binding site switches to a close view with labeled contacting residues while keeping the receptor context; Pocket surface adds the computed solvent-accessible surface. Labels are suppressed in the overall composition and appear automatically in the binding-site view. The appearance panel controls label size; the contact panel can restrict labels and interactions. **Export 3D PNG** captures the current camera at 300 or 600 DPI, scales label pixels with the image resolution, and restores the on-screen view. Label placement avoids the projected ligand where space permits and reduces overlap without changing molecular coordinates. Prepared receptor bonds come from the same validated chemical graph as contact detection. Contact endpoints retain their actual coordinates and visible covalently connected residues; aromatic centroid endpoints have explicit ring guides. Residue summary limits links to the minimum-distance event of each category, while All atom contacts retains individual lines. Surface export waits for completed meshes and reuses them at high resolution. Very dense views may still need a contact filter or a different camera.

## Draw the shared functional group

Open **Functional groups → Similarity & shared groups**, select a protein and calculated pocket, then **Analyze saved poses**. **Shared functional group structures** shows conventional functional groups detected by the existing atom-centred SMARTS in at least two unique structures in that analysis scope. Select a group to see an illustrative R-group drawing and up to five actual compounds with the functional-centre atoms highlighted. The count explicitly states how many of the analyzed unique structures contain it. It is not a maximum-common-substructure calculation, a claim that every compound shares the group, or evidence of a common mechanism. **Export analysis tables** also saves the selected group as PNG/SVG. Existing structural clusters and present-versus-participating tables remain available.

## Release changes

- Robust PDB-ID/URL normalization, validated coordinate downloads and mmCIF/PDBe fallbacks.
- Complete-protein, labeled binding-site and pocket-surface compositions; visible covalent contact endpoints, camera controls and orientation-preserving high-resolution exports.
- A larger 2D canvas, typed circular residue maps and a prominent Save 2D figure button.
- One additional requested chart: Docking Network; all four chart types still load individually.
- Shared functional-group drawings with actual SMARTS-verified compound examples.
- Version 1.0.1; the original v1.0.0 release and previous validation records remain unchanged. Library contents and docking/interaction algorithms are unchanged.
