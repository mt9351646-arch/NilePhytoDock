# Continuation instructions — NilePhytoDock 0.6.1

Continue the existing native Windows project. Read README.md, docs/SCIENTIFIC_METHODOLOGY.md, docs/DATABASE_GUIDE.md and docs/VALIDATION_REPORT.md before edits. Developers are Ahmed G Soliman and Malak Taha. Keep all application text English and all user guides external and English. Preserve the supplied logo, seven-size ICO, splash, P2Rank-to-Smina box transfer, settings and saved projects.

The seed contains **57 distinct botanical oils (46 essential and 11 fixed)**, **164 distinct ready InChIKeys**, 186 ready compound-name records, 819 normalized name records, 68 botanical taxa, 119 analytical profiles and 2109 source observations. The 633 remaining names need review. Repeated profiles, source peaks and aliases do not inflate the home-page counters.

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

## Next useful work

Validate on a clean Windows 10/11 VM and additional GPU/display configurations; broaden external redocking benchmarks; implement a deliberate curator workflow for the 633 unresolved names and source-identity observations; add independently reviewed Egyptian-source peppermint and other oil profiles when primary analytical evidence supports them. Do not describe these future tasks as implemented. No code-signing certificate or proprietary PyMOL is supplied.

Use a fresh private data/output directory for tests. Back up SQLite with its backup API, not a raw WAL-era file copy. Never replace user projects with a seed. Raw docking energies/poses remain immutable; changed derived indices must retain the curation context. Git history begins from the owner-authorized current source snapshot because no repository history existed in this workspace. Never rewrite or invent earlier authorship. Native binary distribution belongs in GitHub Releases. Preserve actual authenticated account identity for commits.

Use Windows x64 and the tested Python 3.12 environment. Install `requirements.txt`, retain third-party notices and restore the external runtime directories from the verified release (see `external_tools/ASSET_MANIFEST.json`). Native runtimes are release assets rather than large Git source blobs. Source includes exact hashes and upstream provenance; no engine rebuild is claimed.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m PyInstaller --noconfirm --distpath dist_comprehensive --workpath build/pyinstaller_comprehensive build/NilePhytoDock.spec
```

For an actual installation check, set a fresh private `NILEPHYTODOCK_DATA` directory and run `NilePhytoDock.exe --verify-installation OUTPUT tests/fixtures/3PTB.pdb`. This performs real P2Rank and three Smina jobs, validates transferred boxes, checks HPLC index suppression and reports, and loads native 3D/Plotly canvases. Normal startup does not enter this path. The test needs a fresh output folder.

The supplied seed has zero research projects. A writable user copy under `%LOCALAPPDATA%/NilePhytoDock` stores projects. Preserve it and complete study folders before upgrades. Seven icon resolutions are embedded in the PE; shortcuts use the explicit ICO and the process sets AppUserModelID `NilePhytoDock.Studio`. The splash uses the supplied logo. English guides are copied to `Documentation` beside the executable, outside `_internal` and outside the application interface.
