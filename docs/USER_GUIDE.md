# User guide — 0.6.1

**New result workflow:** [Results and 3D guide](Results_and_3D_Guide_EN.md). Oil results shows the best compounds in each oil; Functional groups summarizes the top compounds for the selected protein. The retained 0.6.0 PDF/DOCX manuals document the scientific baseline; this 0.6.1 guide supersedes their former split-view/result instructions.


NilePhytoDock Studio 0.6.1 is a native Windows molecular-screening application developed by **Ahmed G Soliman and Malak Taha**. The application and its external documentation are English.

1. Extract the complete Windows ZIP. Keep `_internal` beside `NilePhytoDock.exe` and launch the 0.6.1 shortcut. Wait for Engines available.
2. Select the intended analytical profiles in Botanical library. Inspect geography, extraction, original units and source notes.
3. Import PDB/mmCIF receptors in Protein targets. Inspect chains, missing residues, ligands, waters, cofactors and metals.
4. In Screening setup set the study name, preparation choices and specific bound residues to remove. `BEN A:1` is only the supplied 3PTB example.
5. Run Prepare and predict all. Select a P2Rank pocket for each receptor. Automatic mode transfers its actual center and dimensions to the Smina protocol; Custom box records explicit coordinates.
6. Set exhaustiveness, scoring function, pose count, CPU count, seed and a writable output folder. Start the study and inspect progress and per-job status.
7. Open Oil results, choose the protein/site and oil, and review its best compounds. Double-click a compound to open its actual pose in a separate maximized 3D window. F11 uses the full screen; Esc restores controls. The 2D interactions page is separate.
8. Read priorities together with coverage and source warnings. Concentration-based and headspace profiles receive no oil index.
9. Use Charts for supported plots, filters, hover values and point details. Export the actual plotted data alongside PNG/SVG/PDF figures and CSV/XLSX data.
10. Export reports and preserve the complete study directory, including Project_Data/project.nile.sqlite. Open Saved Project reopens its recorded calculations.

## Library

The seed contains **57 distinct botanical oils (46 essential and 11 fixed)**, **164 distinct ready InChIKeys**, 186 ready compound-name records, 819 normalized name records, 68 botanical taxa, 119 analytical profiles and 2109 source observations. The 633 remaining names need review. Repeated profiles, source peaks and aliases do not inflate the home-page counters.

Three reviewed literature packs retain 90 analytical profiles and 1448 observations from 37 primary PMC papers. The original 661 composition records survive unchanged. Original table rows, values, units, uncertainty, source names, PMCID/DOI, table/row IDs, sample origin and cached-file SHA-256 remain traceable. Import hashes make repeat imports idempotent; incompatible changed manifests require reviewed migration. A SQLite backup is created before merging a new bundled literature pack into an existing user library.

The supplied combined CSV is integrated with a source-audit table: 434 corroborating duplicates, 85 source differences retained for review and 64 additional source values. Raw Word rows remain intact. No missing values become zero; unknown peaks, class totals, retention indices and oil yield are not compounds. Partial major-component tables remain labeled partial; percentages are not normalized to 100%.

Peppermint's published methyl acetate at RI1295 is retained but source-specific docking eligibility is false pending review; it is not silently changed to menthyl acetate. Its rounded individual rows sum to 99.52% although the printed total says 99.51%. Cumin is a market sample, peppermint a Moroccan reference, and selected grape, hibiscus and olive growing origins are unverified. Jasmine headspace is not extracted essential oil; olive fatty-acid pools are not native free-fatty-acid or triglyceride molecular compositions. Nymphaea alba is supported; the contradictory blue-lily article and unavailable olive annotation table were excluded.


The preparation filter distinguishes Essential Oils, Fixed Oils, Botanical Extracts, Resins and Aromatic Preparations and Individual Natural Compounds. The Ancient Egyptian Botanical Heritage view evaluates 12 candidates with evidence type, period, confidence, source and taxonomic scope. Genus-level biomarkers do not establish a modern species; reconstructed recipes and uncertain ancient plant names are identified as interpretations. Modern analytical chemistry is stored separately from historical associations.

Fixed-oil fatty-acid pools do not establish native free-acid abundance. Unresolved Moringa sum lipids, analytical TMS derivatives, silicone contaminants and source-suspect assignments are blocked. Structures beyond 900 Da, 80 heavy atoms or 25 rotatable bonds require specialist review. Candidate files, original observations and existing raw results survive these eligibility changes.

## Visualization

The interaction palette is shared across 2D, 3D and charts: hydrogen bonds blue/dashed; hydrophobic green/dotted; ionic orange; pi-pi purple; pi-cation magenta; van der Waals gray; metal gold. Residue fills independently encode polarity, charge, biochemical class, amino-acid identity , hydrophobicity, aromaticity or interaction participation. The latter uses segmented 2D rings for multiple categories. Charge uses the prepared residue formal charge where available and an explicitly stated general convention otherwise.

Classic uses ordered rails; Circular arranges collision-checked residue circles around the ligand. A minimum-distance link per residue/type reduces clutter; parentheses count contacts. The complete atom pairs remain in SVG tooltips and source tables. 2D line lengths are schematic and labels report actual 3D distances.

The 3D viewer offers nine protein representations, three ligand styles, eight standard color modes, surfaces, site and contact filters, labels, interaction focus and reset/fit. Structural confidence requires explicit confirmation that B values contain pLDDT. Crystallographic B factors are never automatically treated as confidence. Contact-endpoint hydrogens remain chemically bonded and visible. Ring contacts use actual centroids. Protein/ligand atom coordinates are checked again after parsing in the browser.

Export 2D SVG and PNG at 300/600 DPI, 3D PNG at 2400×1800 or 4800×3600 pixels with matching DPI metadata, complex PDB, saved ligand SDF and PyMOL PML. PSE export is enabled only when an installed legitimate PyMOL is available.


Three actual appearance presets (Scientific Classic, High Contrast and Publication Quality) control background, protein/surface opacity, ligand carbon color, optional protein color, labels, outline material, ambient occlusion and fog. The 3D viewer has its own page and independent maximized window. F11 hides controls for an uninterrupted molecular canvas; Esc restores them. Ligand focus and Protein overview provide clear alternative views. The former automatic 0.33 protein opacity has been removed.

## Charts

Sixteen chart types use saved calculations: docking heatmap; compound–protein bubbles; oil–protein bubbles; oil ranking; compound ranking; interaction matrix; interaction network; residue frequency; compound–oil relationship network; multitarget comparison. Unsupported plots are disabled.

Compound bubbles preserve source-profile-specific membership. Color and marker identify botanical oil; area is uniform or original GC peak area using one scale across all oils. Concentrations in other units cannot enter GC area sizing. Oil bubbles use normalized oil index or screened original GC area. Filters do not recalculate the study's original priority population. Heatmaps distinguish missing cells; interaction matrices preserve multiple categories per cell. Network source-membership edges are distinguished from classified molecular contacts. Exports include PNG, SVG, PDF, CSV and the plotted JSON specification.


Functional groups are assigned with versioned atom-centred SMARTS and specific-class precedence. Explicit-H contacts map to their bonded heavy atom. Conventional groups and overlapping aromatic, alkene and hydrophobic features remain separate domains. Presence is distinct from directly participating atoms; event counts, unique InChIKeys and ligand-residue pairs are reported separately.

Chemical similarity uses Morgan radius 2, 2048 bits, chirality and Tanimoto; Butina clusters use a 0.65 similarity threshold. Site interaction similarity is binary chain/residue/insertion/category Jaccard within one prepared receptor and pocket. Two empty fingerprints are unavailable. Approximate classical MDS uses structural distances independently of scores.

Exploratory enrichment requires at least 12 structural-cluster representatives, selected lexicographically by InChIKey independently of score. Two-sided Fisher tests compare top/bottom energy quartiles with ties, with BH correction over tested groups. A small or redundant cohort is explicitly withheld. Associations do not establish activity or causation.

Export Interaction Table supports complete, best pose, selected protein, selected compound, group summary and frequency summary modes. CSV/XLSX retain full values and metadata; DOCX preserves required identities, source profiles, geometry, group atoms and methods, grouping repeated identifiers by pose. Empty scientific exports fail visibly.

## Interpretation

Docking scores and oil indices are computational screening priorities. They do not establish affinity, potency, efficacy, safety or mixture synergy. GC peak area is not an absolute mass fraction. Preparation uses a general protonation approximation, does not rebuild missing loops or side chains, and does not enumerate a pH-dependent ligand ensemble. One BEN/3PTB redocking system is not broad validation. Windows 11 on the current host is tested; Windows 10, a clean VM and all GPU configurations are untested. The executable is unsigned. PyMOL is optional and is not bundled.
