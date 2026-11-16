> 0.6.1 update: public downloads; oil-first best-compound results, a separate functional-group summary, and an independent maximized/fullscreen 3D window. See [Results and 3D guide](Results_and_3D_Guide_EN.md). The following records retain the 0.6.0 scientific baseline.

# NilePhytoDock 0.6.0 validation report

Date: 29 October 2026. Developers: Ahmed G Soliman and Malak Taha. Repository evidence is in validation/0.6.0; complete case data is a separate release asset. Original raw outputs remain preserved in data/validation in the workspace.

## Host and build

Native Windows 11 Pro x64 build 26200; Python 3.12.14; Smina 2020.12.10; P2Rank 2.5.1; Temurin Java 17.0.19; RDKit 2026.09.1; ProLIF 2.2.3; PySide6 6.12.0. requirements.txt records exact Python versions. Fifty own application modules in the final frozen archive matched current source bytecode recursively. Local resources and portable chemistry files are checked in release_verification.json.

## Database preservation

The final seed has 57 distinct botanical oils (46 essential and 11 fixed), 68 taxa, 119 source profiles, 819 normalized names and 2109 source observations. 186 ready name records represent 164 distinct InChIKeys; 633 names remain non-ready. All 1613 preceding source observations retain their raw scientific fields. The seed has zero research projects and passes SQLite integrity and foreign-key checks. Research databases receive a backup before library migration.

Ninety literature profiles and 1448 observations come from 37 primary papers across three reviewed manifests. There are twelve historical evidence evaluations. Geography, preparation, raw names/values/units, table rows and citations remain distinct. The Moringa lipid subset is explicitly mean-only with the source supplement hash preserved. Uncertain identity, unresolved stereochemistry, derivatization and out-of-scope structures are withheld. Fixed-oil fatty-acid pools do not imply native free acids or triacylglycerols and receive no oil index. All 186 ready records (164 PubChem CIDs) have concordant RDKit/PubChem formulas; this does not authenticate a source peak annotation.

## Tests and integration

- 56 automated tests passed with one upstream MDAnalysis deprecation warning. Tests cover raw-source preservation, identity/ranking, interactions, SMARTS, fingerprints/enrichment, exports, multi-project save/relocation and desktop workflow.
- Six actual poses on two receptors: 222 contacts independently checked against saved coordinates, including three ring-feature contacts. Deliberately altered coordinates and distances were rejected. Complex coordinates matched saved ligands.
- Three 2D styles exercised across seven independent residue modes. Final segmented functional-group participation rings and the positive native Molecular Analysis worker/views were checked separately after the last SVG refinement.
- Native WebGL checked nine protein representations, eight standard color modes, three ligand styles and three appearance presets. Actual pixels changed with background/material/opacity; a 1600x1200 PNG carried 300 DPI metadata. Structural-confidence coloring requires explicit source confirmation.
- All sixteen chart types rendered offline with real saved values. Plotly hover and Qt WebChannel point selection were executed through actual APIs. PNG/SVG/PDF/CSV/XLSX exports matched numbers. This does not claim physical mouse testing of every chart.
- Six interaction export modes matched CSV/XLSX/DOCX: 381 complete rows, 381 best-identity rows in this particular fixture, 156 selected-protein, 96 selected-compound, 18 functional-group associations and 44 frequency rows. Distances and source atom mappings retained precision; empty exports were rejected.
- Layout checks cover twelve pages at 1366, 1920 and 2560 widths with scale factors 1.0 and 1.5: 72 screen captures. Chart export control and scrollable sidebar were rechecked after correcting clipping.
- A fresh final Windows EXE installation workflow runs actual P2Rank and three new Smina jobs, verifies exact pocket-box transfer and HPLC index suppression, produces report formats and loads actual native 3D/Plotly canvases. Final results and executable hash are in release_install/verification.json and release_verification.json.
- Seven embedded icon sizes and versioned shortcut target/icon paths are checked. English manuals are in Documentation outside _internal and outside the application UI.

## Real reference benchmark and botanical case

The 3PTB bovine trypsin/BEN protocol retains receptor coordinates, removes BEN and waters explicitly and retains calcium. P2Rank placed its top center 0.608343 Angstrom from the crystal ligand centroid, with all nine heavy atoms inside the predicted box. Reference controls used exhaustiveness 16, five modes, seed 20261029 and two CPU threads.

Neutral BEN top RMSD was 0.393705 Angstrom. Explicit +1 amidinium BEN gave 0.390331 in the reference box and 0.388594 in the predicted box. These are graph-symmetry-aware heavy-atom RMSDs in the original coordinate frame, without post-docking alignment. Repeating the charged reference reproduced all saved pose coordinates exactly on this host. This single system is not general validation of ligand ranking.

Five profiles were selected: thyme, basil, cumin, anise and coriander. Four contribute structures; anise has no approved native constituent. There are 23 compound-name jobs, 20 distinct InChIKeys, 69 poses and 1917 independently verified contacts (maximum distance residual below 1e-12 Angstrom). Constituent screening uses exhaustiveness 8 and three modes. The case transparently reuses hash-verified identical raw Smina outputs from preceding actual QC executions; elapsed zero denotes reuse. P2Rank and four reference controls ran freshly, as did the three frozen-installation jobs.

Screened original GC area coverage is cumin 59.73%, thyme 69.04%, coriander 1.66%, basil 23.33% and anise 0%. All are below 70%; whole-oil efficacy cannot be inferred. Twenty structures form eighteen Morgan clusters. Only ten independent non-repeated scaffold/cluster representatives remain, so enrichment is withheld. No matched botanical activity/decoy dataset exists: no AUROC or affinity correlation is invented. The published benzamidine comparator is contextual.

## Documents and limits

All four English DOCX documents were rendered and all 37 pages visually inspected. Changed pages were rerendered and reinspected. Final page-count, language and author checks are recorded in document_qa.json. The User Guide has nine pages, Build and Methods fifteen, the fourteen-section case study nine, and the complete software summary four.

Windows 10, a clean VM and all GPU/driver configurations are untested. The EXE is unsigned. Preparation does not rebuild missing loops/side chains, predict site pKa or enumerate ligand protonation/tautomer ensembles. PSE requires separately installed legitimate PyMOL. Scores, contacts and composition-informed priorities are computational results, not measured affinity, efficacy, safety or mixture synergy.

The final SVG export check also passed ten focused diagram/upgrade tests after replacing unsupported QtSvg text paint-order with separate label backgrounds. Native PNG labels were visually reinspected; distances and interaction names remain readable.
## 0.6.1 native result verification

The interface change is verified with 62 automated tests and real saved 3PTB screening data. The source UI test checks the default best oil selection, no repeated identity rows, an independent maximized 3D window, F11/Esc restoration, direct group-supporting compounds and layouts at 1366/1920 widths. Zero or unreported source abundance cannot imply membership; explicit trace/presence annotations remain eligible. The final native EXE runs an additional fresh P2Rank/three-Smina integration, including oil/group views and fullscreen rendering. Full evidence is in validation/0.6.1. The scientific seed, prior research records and earlier release remain preserved.
