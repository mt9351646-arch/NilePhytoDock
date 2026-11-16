# Scientific methodology — 0.6.0

NilePhytoDock Studio 0.6.0 is a native Windows molecular-screening application developed by **Ahmed G Soliman and Malak Taha**. The application and its external documentation are English.

P2Rank 2.5.1 with bundled Temurin Java 17.0.19 predicts pockets on the prepared receptor. The selected per-target center and dimensions are recorded and passed unchanged to native Smina 2020.12.10. Actual commands, seed, scoring function, input files and engine versions accompany results. RDKit 2026.09.1 validates molecular graphs and prepares ETKDGv3 conformers (seed 20261029), followed by converged MMFF94s or UFF optimization; Meeko generates PDBQT. ProLIF 2.2.3 classifies contacts on chemically typed RDKit graphs. PLIP is not used.

Contacts retain original atom indices, residue/chain/sequence/insertion identifiers, protein identity, method, parameters and geometry version `atom-anchors-3`. Hydrogen-bond distance joins donor and acceptor heavy atoms; the donor-H-acceptor angle is independently recomputed. Aromatic contacts use ring centroids and normal/plane geometry. Metal classification is restricted to complete chemically plausible Zn tetrahedral or Mg octahedral shells. Geometry mismatches fail visibly. Reanalysis first succeeds, then archives old records in `interaction_reanalyses` before replacing contacts. Raw docking scores and saved poses are preserved.

Exact normalized PubChem synonyms, accepted RDKit connectivity, single-component identity, molecular formula and source stereochemistry are checked independently. Unresolved stereocenters or required E/Z assignments are not approved. A source-geometry review withdrew 17 earlier automated approvals while retaining candidate files and audit data. Formula agreement with a PubChem CID verifies the resolved structure's consistency, not the identity of a tentative chromatographic peak.

Within each target, identical InChIKeys count once in the percentile population. With average ascending energy rank r among N identities, q=(N−r)/(N−1); a singleton receives 0.5. Oil index is sum(w*q)/sum(w) over successful, eligible constituents with original positive GC peak-area weights w. Coverage is the unnormalized sum of screened original areas; below 70% is flagged. Duplicate chemical identities in one profile block its index. Source-review observations cannot contribute to coverage, even if an older docking result exists. HPLC, qualitative LC-MS, headspace and fatty-acid pools have no oil index. Missing positive-weight targets make multitarget priority unavailable rather than being silently reweighted. Sensitivity varies one abundance at a time by ±10%.


Functional groups are assigned with versioned atom-centred SMARTS and specific-class precedence. Explicit-H contacts map to their bonded heavy atom. Conventional groups and overlapping aromatic, alkene and hydrophobic features remain separate domains. Presence is distinct from directly participating atoms; event counts, unique InChIKeys and ligand-residue pairs are reported separately.

Chemical similarity uses Morgan radius 2, 2048 bits, chirality and Tanimoto; Butina clusters use a 0.65 similarity threshold. Site interaction similarity is binary chain/residue/insertion/category Jaccard within one prepared receptor and pocket. Two empty fingerprints are unavailable. Approximate classical MDS uses structural distances independently of scores.

Exploratory enrichment requires at least 12 structural-cluster representatives, selected lexicographically by InChIKey independently of score. Two-sided Fisher tests compare top/bottom energy quartiles with ties, with BH correction over tested groups. A small or redundant cohort is explicitly withheld. Associations do not establish activity or causation.

Export Interaction Table supports complete, best pose, selected protein, selected compound, group summary and frequency summary modes. CSV/XLSX retain full values and metadata; DOCX preserves required identities, source profiles, geometry, group atoms and methods, grouping repeated identifiers by pose. Empty scientific exports fail visibly.


The preparation filter distinguishes Essential Oils, Fixed Oils, Botanical Extracts, Resins and Aromatic Preparations and Individual Natural Compounds. The Ancient Egyptian Botanical Heritage view evaluates 12 candidates with evidence type, period, confidence, source and taxonomic scope. Genus-level biomarkers do not establish a modern species; reconstructed recipes and uncertain ancient plant names are identified as interpretations. Modern analytical chemistry is stored separately from historical associations.

Fixed-oil fatty-acid pools do not establish native free-acid abundance. Unresolved Moringa sum lipids, analytical TMS derivatives, silicone contaminants and source-suspect assignments are blocked. Structures beyond 900 Da, 80 heavy atoms or 25 rotatable bonds require specialist review. Candidate files, original observations and existing raw results survive these eligibility changes.

## Display semantics

The interaction palette is shared across 2D, 3D and charts: hydrogen bonds blue/dashed; hydrophobic green/dotted; ionic orange; pi-pi purple; pi-cation magenta; van der Waals gray; metal gold. Residue fills independently encode polarity, charge, biochemical class, amino-acid identity , hydrophobicity, aromaticity or interaction participation. The latter uses segmented 2D rings for multiple categories. Charge uses the prepared residue formal charge where available and an explicitly stated general convention otherwise.

Classic uses ordered rails; Circular arranges collision-checked residue circles around the ligand. A minimum-distance link per residue/type reduces clutter; parentheses count contacts. The complete atom pairs remain in SVG tooltips and source tables. 2D line lengths are schematic and labels report actual 3D distances.

The 3D viewer offers nine protein representations, three ligand styles, eight standard color modes, surfaces, site and contact filters, labels, interaction focus and reset/fit. Structural confidence requires explicit confirmation that B values contain pLDDT. Crystallographic B factors are never automatically treated as confidence. Contact-endpoint hydrogens remain chemically bonded and visible. Ring contacts use actual centroids. Protein/ligand atom coordinates are checked again after parsing in the browser.

Export 2D SVG and PNG at 300/600 DPI, 3D PNG at 2400×1800 or 4800×3600 pixels with matching DPI metadata, complex PDB, saved ligand SDF and PyMOL PML. PSE export is enabled only when an installed legitimate PyMOL is available.


Three actual appearance presets (Scientific Classic, High Contrast and Publication Quality) control background, protein/surface opacity, ligand carbon color, optional protein color, labels, outline material, ambient occlusion and fog. Split, 3D focus and 2D focus views make the canvas usable at smaller sizes. The former automatic 0.33 protein opacity has been removed.

## Limits

Docking scores and oil indices are computational screening priorities. They do not establish affinity, potency, efficacy, safety or mixture synergy. GC peak area is not an absolute mass fraction. Preparation uses a general protonation approximation, does not rebuild missing loops or side chains, and does not enumerate a pH-dependent ligand ensemble. One BEN/3PTB redocking system is not broad validation. Windows 11 on the current host is tested; Windows 10, a clean VM and all GPU configurations are untested. The executable is unsigned. PyMOL is optional and is not bundled.
