"""Record verified native results, then synchronize final documentation."""
import json,hashlib,shutil,sqlite3,sys
from pathlib import Path
import pefile
from docx import Document
from database.store import connect,rows,counts
from app.paths import user_data

root=Path('release/NilePhytoDock Portable').resolve();exe=root/'NilePhytoDock.exe'
db=connect(user_data()/'nilephytodock.sqlite')
projects=rows(db,"SELECT * FROM analysis_projects WHERE name='Packaged v0.2 validation' ORDER BY id DESC")
assert projects,'The final native workflow has not been performed'
project=projects[0];assert project['status']=='complete',project['status']
runs=rows(db,'SELECT * FROM docking_runs WHERE project_id=?',(project['id'],))
assert len(runs)==6 and all(r['status']=='complete' and not r['error'] and r['elapsed']>0 for r in runs)
poses=rows(db,'SELECT p.* FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id WHERE r.project_id=?',(project['id'],))
assert poses and all(Path(p[k]).exists() for p in poses for k in ['sdf_path','complex_path'])
assert {205,206}.issubset({r['compound_id'] for r in runs})
checks=[]
for run in runs:
    pocket=rows(db,'SELECT * FROM predicted_pockets WHERE id=?',(run['pocket_id'],))[0]
    command=json.loads((Path(run['folder'])/'process.log').read_text(encoding='utf-8').splitlines()[0])
    center=[float(command[command.index('--center_'+a)+1]) for a in 'xyz'];size=[float(command[command.index('--size_'+a)+1]) for a in 'xyz']
    assert center==json.loads(pocket['center']) and size==json.loads(pocket['size'])
    checks.append({'run_id':run['id'],'center':center,'dimensions':size,'elapsed_seconds':run['elapsed']})
assert not db.execute('PRAGMA foreign_key_check').fetchall()
folder=Path(project['folder']);package=json.loads((folder/'Reports/reproducibility.json').read_text(encoding='utf-8'))
assert package['application']['version']=='0.2.0' and 'Ahmed G soliman' in package['application']['developers'] and 'malak Taha' in package['application']['developers']
assert len(package['tables']['Docking results'])==len(poses)
assert Document(folder/'Reports/scientific_report.docx').core_properties.author=='Ahmed G soliman and malak Taha'
pe=pefile.PE(str(exe));properties={}
for group in pe.FileInfo:
    for entry in group:
        if hasattr(entry,'StringTable'):
            for table in entry.StringTable:properties.update({k.decode():v.decode() for k,v in table.entries.items()})
assert properties['ProductVersion']=='0.2.0'
assert properties['CompanyName']=='Ahmed G soliman; malak Taha'
assert {3,14}.issubset({entry.id for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries})
seed=sqlite3.connect((root/'_internal/data/nilephytodock.sqlite').as_uri()+'?mode=ro',uri=True)
assert seed.execute('SELECT count(*) FROM oil_profiles').fetchone()[0]==29
assert seed.execute('SELECT count(*) FROM analysis_projects').fetchone()[0]==0;seed.close()
report={'version':'0.2.0','developers':['Ahmed G soliman','malak Taha'],'platform':'Windows 11 Pro 10.0.26200 x64','entry_point':str(exe),'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'launched_by_double_click_in_explorer':True,'portable_folder_with_spaces':True,'native_workflow_project':project,'native_runs':checks,'native_job_count':len(runs),'native_pose_count':len(poses),'new_csv_thymol_carvacrol_screened':True,'native_command_boxes_match_persisted_choices':True,'reports_and_credits_verified':True,'windows_executable_properties':properties,'icon_resources_present':True,'bundle_seed_has_29_profiles_and_no_seeded_scores':True,'windows_10_tested':False,'clean_vm_tested':False}
Path('data/validation/redesign_executable_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
p=Path('docs/VALIDATION_REPORT.md');s=p.read_text(encoding='utf-8')
s=s.replace('Version 0.2.0 is being rebuilt with the supplied logo, icon, splash, corrected credits, redesigned UI, CSV update, automatic pocket transfers and output selection. Final version 0.2 executable evidence is recorded separately in redesign_executable_verification.json; source execution alone does not establish packaged functionality.',f'Version 0.2.0 was rebuilt, copied to the portable folder containing spaces and launched by double-clicking in Windows Explorer. Its native P2Rank/Smina workflow completed six successful jobs and {len(poses)} poses, including new CSV Thymol and Carvacrol, with no failed jobs. The selected output folder contains actual reports and a project snapshot. Per-target boxes, report metadata, executable version/developer properties and icon resources were verified. Final evidence: data/validation/redesign_executable_verification.json. This does not constitute a Windows 10 or clean-VM test.')
s=s.replace('There are 41 automatically verified docking-ready records representing 40 distinct InChIKeys and 161 unresolved/review records.','The original Word-only library had 41 automatically verified docking-ready records representing 40 distinct InChIKeys and 161 unresolved/review records; current CSV-inclusive counts are recorded below.')
p.write_text(s,encoding='utf-8')
shutil.copytree('docs',root/'_internal/docs',dirs_exist_ok=True)
for name in ['README.md','LICENSES.md']:shutil.copy2(name,root/name)
for name in ['database_validation.json','extraction_records.csv','gui_smoke.png']:
    shutil.copy2(Path('data/validation')/name,root/'_internal/data/validation'/name)
db.close();print('Final native release evidence recorded:',len(runs),'jobs;',len(poses),'poses')
