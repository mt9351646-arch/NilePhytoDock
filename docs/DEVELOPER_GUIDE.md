# Developer guide — 0.6.1

NilePhytoDock Studio 0.6.1 is a native Windows molecular-screening application developed by **Ahmed G Soliman and Malak Taha**. The application and its external documentation are English.

Use Windows x64 and the tested Python 3.12 environment. Install `requirements.txt`, retain third-party notices and restore the external runtime directories from the verified release (see `external_tools/ASSET_MANIFEST.json`). Native runtimes are release assets rather than large Git source blobs. Source includes exact hashes and upstream provenance; no engine rebuild is claimed.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m PyInstaller --noconfirm --distpath dist_comprehensive --workpath build/pyinstaller_comprehensive build/NilePhytoDock.spec
```

For an actual installation check, set a fresh private `NILEPHYTODOCK_DATA` directory and run `NilePhytoDock.exe --verify-installation OUTPUT tests/fixtures/3PTB.pdb`. This performs real P2Rank and three Smina jobs, validates transferred boxes, checks HPLC index suppression and reports, and loads native 3D/Plotly canvases. Normal startup does not enter this path. The test needs a fresh output folder.

The supplied seed has zero research projects. A writable user copy under `%LOCALAPPDATA%/NilePhytoDock` stores projects. Preserve it and complete study folders before upgrades. Seven icon resolutions are embedded in the PE; shortcuts use the explicit ICO and the process sets AppUserModelID `NilePhytoDock.Studio`. The splash uses the supplied logo. English guides are copied to `Documentation` beside the executable, outside `_internal` and outside the application interface.

## Architecture

`UpgradeMixin → StudioMixin → RedesignMixin → BaseWindow` preserves the existing desktop workflow. `database` contains migrations and importers; `scientific` owns preparation, pockets, docking, geometry and ranking; `visualization` owns shared semantics, 2D/3D, charts and exports; `reporting` emits source observations and actual result tables. `app/chart_workspace.py` hosts offline Plotly 3.3.0 with a Qt WebChannel for selection details. No remote scripts are needed for normal screening.

## Verification commands

```powershell
python -m tools.validate_redesign data/validation/NEW_workflow
python -m tools.validate_comprehensive_geometry
python -m tools.validate_comprehensive_charts
python -m tools.validate_comprehensive_exports
python -m tools.validate_appearance
python -m tools.validate_final_workspace
python -m tools.verify_library_formulas
python -m tools.verify_english_release
```

The geometry/chart helpers use private copies of actual study results. Do not use them against live user data. Source imports, source-specific eligibility and identity approvals are separate gates. Do not promote a candidate solely to increase a displayed count.
