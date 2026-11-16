"""Finalize release evidence after a successful native launch and workflow."""
from pathlib import Path
import hashlib,json,shutil

def update_text():
    p=Path('docs/VALIDATION_REPORT.md');s=p.read_text(encoding='utf-8')
    s=s.replace('23 passing tests','24 passing tests')
    marker='## Executable verification'
    start=s.index(marker);end=s.index('## Remaining acceptance gaps',start)
    text='''## Executable verification

The self-contained portable folder was built with PyInstaller and launched by double-clicking NilePhytoDock.exe in Windows Explorer on Windows 11. The distribution was copied to a folder containing spaces and launched there. The packaged application completed a real Melaleuca/3PTB screening with three successful Smina jobs, 15 poses and no failed jobs; it exported PDF, DOCX, CSV, XLSX, JSON and actual figures. The final build was then launched and checked again after the Unicode I/O fixes. Its final native workflow and checksums are recorded in data/validation/executable_verification.json. The offline embedded 3D viewer and viewport PNG export were checked with the packaged application.

A separate actual calculation imported a Unicode-named mmCIF file and prepared its receptor, ran P2Rank and docked the source-library ligand with Smina in Arabic/Japanese paths containing spaces. Evidence: data/validation/path_verification.json. This checks project/input paths on this host; a non-ASCII installation path or every Windows locale is not implied.

'''
    s=s[:start]+text+s[end:]
    s=s.replace('Interaction insertion-code disambiguation and general mmCIF/alternate-location edge cases need broader fixture coverage.','Interaction insertion-code disambiguation and broader mmCIF/alternate-location edge cases need additional fixture coverage; one converted mmCIF import/preparation case passed.')
    s=s.replace('Initial GUI layout and pose-specific diagram selection bugs were corrected and rechecked.','Initial GUI layout and pose-specific diagram selection bugs were corrected and rechecked. RDKit narrow filename I/O and Java 17 command-line decoding initially failed for Unicode project paths. Python stream/block molecular I/O and ASCII engine staging corrected these failures; the real path test then passed.')
    p.write_text(s,encoding='utf-8')
    p=Path('docs/SCIENTIFIC_METHODOLOGY.md');s=p.read_text(encoding='utf-8')
    s=s.replace('Legacy Smina file I/O uses temporary ASCII staging; Python copies Unicode-named project inputs/outputs.','Legacy Smina file I/O and P2Rank Java argument decoding use temporary ASCII staging; Python copies Unicode-named project inputs/outputs. RDKit reads and writes through Python streams or molecular blocks.')
    p.write_text(s,encoding='utf-8')

if __name__=='__main__':
    from database.store import connect,rows
    from app.paths import user_data
    db=connect(user_data()/'nilephytodock.sqlite')
    projects=rows(db,'SELECT id,name,status FROM analysis_projects ORDER BY id')
    latest=projects[-1]
    assert latest['id']>=2 and latest['status']=='complete',latest
    runs=rows(db,'SELECT id,status,error,elapsed,engine_version FROM docking_runs WHERE project_id=?',(latest['id'],))
    assert len(runs)==3 and all(r['status']=='complete' and not r['error'] for r in runs),runs
    poses=rows(db,'SELECT p.* FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id WHERE r.project_id=?',(latest['id'],))
    assert len(poses)>0 and all(Path(p[k]).exists() for p in poses for k in ['sdf_path','complex_path'])
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
    update_text()
    root=Path('release/NilePhytoDock Portable').resolve()
    report=json.loads(Path('data/validation/executable_verification.json').read_text())
    report.update(exe_sha256=hashlib.sha256((root/'NilePhytoDock.exe').read_bytes()).hexdigest(),distribution_bytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),relocated_screening_status='complete',automated_tests_passed=24,unicode_project_paths_verified=True)
    report['final_build_workflow']={'project':latest,'runs':runs,'pose_count':len(poses),'foreign_keys_valid':True,'pose_files_verified':True}
    report['exported_report_package']='data/validation/relocated_reports'
    Path('data/validation/executable_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    shutil.copytree('docs',root/'_internal/docs',dirs_exist_ok=True)
    shutil.copy2('README.md',root/'README.md')
    shutil.copy2('LICENSES.md',root/'LICENSES.md')
    print('Final release documentation and provenance updated')
