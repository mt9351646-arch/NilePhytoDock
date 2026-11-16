"""Retain versioned proof for the public oil-first results release."""
from pathlib import Path
import shutil,json,hashlib,subprocess
from app.branding import VERSION
ROOT=Path(__file__).resolve().parents[1];qa=ROOT/'data/validation'/('release_'+VERSION);out=ROOT/'validation'/VERSION;out.mkdir(parents=True,exist_ok=True)
for source,name in [(ROOT/'data/validation/result_ux_tests.xml','pytest.xml'),(ROOT/'data/validation/result_ux_0_6_1/verification.json','result_ui.json'),(qa/'verification.json','release_verification.json'),(qa/'frozen_source.json','frozen_source.json'),(qa/'install/verification.json','native_installation.json'),(qa/'shortcuts.json','shortcuts.json')]:
 assert source.exists(),source;shutil.copy2(source,out/name)
for name in ['oil_results_1366.png','functional_groups_1366.png','fullscreen_3d.png','dedicated_3d_page.png']:
 shutil.copy2(ROOT/'data/validation/result_ux_0_6_1'/name,out/name)
(out/'README.md').write_text('''# NilePhytoDock 0.6.1 verification

62 automated tests passed. New summary tests check identity aliases, shared oil membership, separate sites/protocols, failed runs, cutoff ties, source zeros/missing values versus explicit trace, unavailable contacts and optional van der Waals participation.

The actual preserved 3PTB study has five selected botanical profiles, four contributing profiles and twenty distinct eligible structures. Native Qt checks exercise the oil-first result page, functional group summary, independent maximized 3D window, F11/Esc restoration and layouts at 1366/1920 widths. No new synthetic docking results are inserted into research data.

The final frozen EXE separately executes actual P2Rank and three fresh Smina jobs, checks transferred boxes, reports, offline Plotly, verified 3D coordinates and the new result/group/fullscreen windows. The scientific seed is unchanged from 0.6.0. The repository and Windows download were checked without authentication after the owner requested public visibility.

Reproduce automated tests with `python -m pytest -q`. For native installation checks use a fresh NILEPHYTODOCK_DATA and output folder with `NilePhytoDock.exe --verify-installation OUTPUT tests/fixtures/3PTB.pdb`. For result-layout QA, extract the case-data release ZIP under data/validation and run `python -m tools.validate_result_ux`; it uses a private SQLite copy and relocates moved calculation paths. See the external Results_and_3D_Guide_EN.md for the user workflow. The retained 0.6.0 documents/evidence describe the scientific baseline.
''',encoding='utf-8')
records=[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256.json'];(out/'SHA256.json').write_text(json.dumps(records,indent=2));print(len(records),'versioned verification files collected')
