NilePhytoDock Studio 0.6.1 — Ahmed G Soliman and Malak Taha

The repository is now public. Both the repository and release downloads work without signing in to GitHub.

This release changes the default workflow around the requested outputs:
- Oil results: choose the protein/site and oil, then read its best compounds and scores in a wide concise table. One best pose per distinct chemical identity; source samples and protocols stay separate. Raw docking details remain in a secondary tab.
- Functional groups: choose the top five/ten/twenty or all compounds and see the most common conventional groups, distinct compound counts, actual verified contacts and supporting molecules. Score ties are retained; van der Waals-only contacts are optional and separate from the default specific-contact count.
- Independent 3D: selecting a compound opens its actual saved pose in a separate maximized window. F11 gives the screen to the molecular canvas; Esc restores controls. Ligand focus and Protein overview keep the molecule clear. A dedicated 3D page and separate 2D page are also available.

Validation includes 62 passing automated tests, real 3PTB result/layout/3D checks, and the final frozen Windows EXE with fresh P2Rank and three Smina calculations, reports, offline Plotly and the new summary/fullscreen views. The scientific seed is unchanged; earlier projects/releases are preserved. Docking outputs remain computational predictions. Windows 11 on this host is tested; Windows 10, clean VM and all GPUs are not.

Extract the complete Windows ZIP, keep _internal beside NilePhytoDock.exe, and launch the version 0.6.1 executable. The Documentation ZIP and Documentation folder contain Results_and_3D_Guide_EN.md with screenshots and current steps; retained 0.6.0 PDF/DOCX manuals describe the scientific baseline. Source and raw case data are separate assets. SHA256SUMS and the release manifest identify the verified files and source commit.
