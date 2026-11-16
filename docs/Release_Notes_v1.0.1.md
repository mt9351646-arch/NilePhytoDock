# NilePhytoDock Studio v1.0.1

Maintenance update by **Ahmed G Soliman** and **Malak Taha**.

- Fixed packaged PDB retrieval, including IDs, pasted structure links, validated downloads and mmCIF/PDBe fallback.
- Replaced the default 2D diagram with typed circular residue maps and a prominent Save 2D figure button.
- Show the complete protein and ligand in 3D, with separate labeled binding-site and computed pocket-surface compositions. Contact endpoints use the validated covalent graph; aromatic centroid guides are explicit.
- Added camera views, rotation controls and readable, orientation-preserving high-resolution exports, including surfaces.
- Added the requested oil-colored Docking Network and shared functional-group drawings with actual compound examples.

Verified: 77 unit tests, real P2Rank prediction and three Smina calculations from the installed EXE with developer runtimes removed from PATH; PDB retrieval, 2D/3D, all four charts, figure/data exports and reports.

One download: `NilePhytoDock-v1.0.1-Setup.exe` — 429.36 MB. Windows 10/11 x64; 8 GB RAM and 4 GB free space plus research output recommended. Close the application and run Setup to update. Python, Qt, Java, P2Rank, Smina and scientific dependencies are installed automatically. The English guide is in the external Documentation folder.

SHA-256: `9f01a6f7a1073ca126ac18c98f982466aaf25fa81af2769dfd2fc4e2b26781eb`.

The library and docking/contact calculations are preserved. Network lengths represent docking-score differences, not physical distances or experimental affinities. Docking and contact predictions require experimental validation. v1.0.0 remains the first official release; its records are unchanged.

GPL-3.0-or-later; mandatory third-party notices remain in the installation. [Corresponding source, licenses and rebuild inputs](https://github.com/ahmedGSoliman99/NilePhytoDock-Source/releases/tag/v1.0.1), with unchanged dependency sources retained in the v1.0.0 source release. The Windows download is unsigned; use its published checksum.
