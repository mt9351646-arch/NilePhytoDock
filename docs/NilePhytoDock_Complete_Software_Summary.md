# NilePhytoDock Complete Software Summary

This document describes the implemented Windows desktop application, the verified scientific workflow, the delivered source and documentation, and the limits of the current validation. Developers are Ahmed G Soliman and Malak Taha.

## Application and workflow

NilePhytoDock 0.6.1 connects source-qualified botanical chemistry with protein inspection, explicit receptor preparation, P2Rank pockets, native Smina docking, geometry-verified interactions and composition-informed priorities. The application is English with left-to-right layout; its user and development guides are external English documents. The supplied emblem is used by the splash, window, executable and seven-resolution Windows ICO. Existing research databases and prior releases are preserved.

## Database and source evidence

The seed has 57 distinct botanical oils: 46 essential and 11 fixed oils. Across 68 botanical taxa it retains 819 normalized compound-name records and 2109 source observations. There are 186 ready name records representing 164 distinct InChIKeys; 633 names remain outside the ready set. A source peak, an alias and a unique chemical structure are different counts. The seed contains no research projects or demonstration results.

Three reviewed literature packs contain 90 profiles and 1448 observations from 37 primary PMC papers, in addition to the original 661 source observations. The latest pack adds anise, coriander, chamomile, garlic, oregano, Damask rose, camphor-tree/Ravintsara and cardamom references; sweet almond, pistachio, castor, sesame, safflower, flax, Balanites and both Moringa species; tea and coffee extracts, a pomegranate fraction, myrrh, frankincense, mastic, juniper and cedar tar. Existing thyme and previously requested Egyptian/Mediterranean botanicals are retained. Countries and market-origin uncertainty are explicit; non-Egyptian reference samples are not relabelled as Egyptian.

The five preparation categories distinguish essential oils, fixed oils, botanical extracts, resins/aromatic preparations and individual natural compounds. Historical metadata evaluates twelve candidates separately, with source, period, evidence type, confidence and taxonomic uncertainty. Safflower dye and flax linen demonstrate botanical uses, not evidence for those seed oils in a sacred recipe. Modern cedar/juniper species are not inferred from genus-level ancient residues.

Fixed fatty-acid pools, unresolved sum lipids, analytical TMS derivatives and source-suspect annotations are excluded where they do not establish native individual molecules. Molecular scope limits are 900 Da, 80 heavy atoms and 25 rotatable bonds. Original values, units, raw rows, candidate files and previous raw calculations survive these review decisions. All 1613 observations present before this upgrade were checked unchanged in their original scientific fields.

## Scientific methods

RDKit performs structure checks, ETKDGv3 embedding, converged minimization and molecular descriptors. PubChem CID formulas agree with all 186 ready records. Receptor preparation uses an explicit chemistry graph and general protonation approximation, without loop/side-chain rebuilding. P2Rank 2.5.1 and Smina 2020.12.10 run locally through recorded commands and hash-based cache checks. ProLIF 2.2.3 supplies chemical contact typing; PLIP is not used.

Functional centres use versioned SMARTS with specificity precedence and saved atom indices. Presence and directly participating atoms are separate results. Chemical similarity is chirality-aware Morgan/Tanimoto with Butina clustering; contact similarity uses same-receptor/site residue-category Jaccard. Empty fingerprints, small cohorts and missing results remain explicit. Exploratory Fisher/BH statistics prune repeated clusters and Murcko scaffolds. No activity or causal contribution is inferred from a predicted group contact.

Within-target best energies are converted to percentiles over unique InChIKeys. An oil index weights these by original successfully screened GC peak area. Duplicate identities can suppress a source index; incomplete coverage is reported. HPLC concentrations, headspace, fixed fatty-acid pools and qualitative annotations receive no GC-weighted oil index. Multi-target results do not silently drop a missing positive-weight target.

## Executed validation

The automated suite passes 56 tests. Geometry QA checks 222 contacts in six real poses across two proteins, rejects corrupted coordinates/distances and exercises three 2D styles, seven residue color modes, nine protein representations and three actual appearance presets. Sixteen charts render offline with numeric checks, tooltip execution, Qt selection callbacks and static/tabular exports. Six interaction export modes preserve complete numeric values; unsupported empty exports fail visibly.

The case study retains 23 real compound-name calculations, 20 unique structures, 69 poses and 1917 verified contact events. P2Rank center error is 0.608 Å and its box contains all nine crystal ligand heavy atoms. Charged reference redocking reaches 0.390 Å RMSD in the crystal box and 0.389 Å in the predicted box without post-alignment; a repeated charged run produces identical saved coordinates. All selected profile coverages remain below 70%, and anise has no approved native constituent. No matched botanical activity dataset was available for AUROC or affinity correlation.

## Build distribution and documentation

The native PySide6 application is packaged with PyInstaller for 64-bit Windows. Java, P2Rank, Smina and the scientific libraries are included in the portable distribution with notices and native asset hashes. Keep _internal beside NilePhytoDock.exe. Documentation is delivered in Documentation beside the executable. A private data-directory installation check performs actual P2Rank/Smina HPLC screening, verifies reports, native atom mapping, offline charts and English UI. The final validation report records the tested executable and its SHA-256.

Deliverables include the portable Windows ZIP, a source ZIP, README, USER_GUIDE, INSTALLATION, SCIENTIFIC_METHODOLOGY, DATABASE_GUIDE, DEVELOPER_GUIDE, VALIDATION_REPORT, CHANGELOG, NEXT_CODEX_PROMPT, the English user and methods manuals, this summary and the full scientific case study. The release is under X:/nile/release. The private repository is https://github.com/ahmedGSoliman99/NilePhytoDock and versioned release is https://github.com/ahmedGSoliman99/NilePhytoDock/releases/tag/v0.6.1; private access is required.

## Limits and future validation

Scores are predictions, not measured affinity, efficacy or safety. Relative GC peak area is not an absolute mass fraction. Coverage and stereochemical uncertainties materially limit source interpretation; mixture synergy, exposure and pharmacology are not modelled. The current preparation does not calculate site-specific pKa, enumerate ligand protonation ensembles or rebuild missing receptor atoms. Optional PyMOL sessions require an installed legitimate PyMOL. The executable is unsigned. Windows 10, a clean VM and every GPU/display configuration are untested. Broader prospective benchmarks and curated identity resolution remain future scientific work; they are not claimed as completed features.

Area | Implemented behavior

Library | 119 separate source profiles; preparation and historical evidence filters

Screening | PDB/mmCIF import, per-target pockets and exact box transfer, protocol controls, pause/cancel and saved projects

Interactions | ProLIF/RDKit typing, atom/feature geometry checks, archived reanalysis and explicit review states

Visualization | Classic, Circular and Functional group 2D; independent residue fills; custom line colors; three real 3D presets

Analysis | SMARTS participation, independent chemical and compatible-site fingerprints, clusters and exploratory statistics

Export | Six interaction modes; CSV/XLSX/DOCX; sixteen charts with PNG/SVG/PDF/CSV/XLSX; reproducibility reports


The 0.6.1 interface presents the best compounds per oil first and a separate functional-group summary for the chosen receptor/site. Compound selection opens an independent maximized 3D window; F11 shows only the molecular canvas and Esc restores controls. See Results_and_3D_Guide_EN.md for current steps.
