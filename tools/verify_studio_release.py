"""Verify the exact portable PE, icon, shortcuts, guides and native study."""
import json,hashlib,sqlite3,struct
from pathlib import Path
import pefile
from database.store import connect,rows
from app.paths import user_data

root=Path('release/NilePhytoDock Studio 0.3.0').resolve();exe=root/'NilePhytoDock.exe'
pe=pefile.PE(str(exe));props={}
for group in pe.FileInfo:
    for entry in group:
        for table in getattr(entry,'StringTable',[]):props.update({k.decode():v.decode() for k,v in table.entries.items()})
assert props['ProductVersion']=='0.3.0' and props['CompanyName']=='Ahmed G soliman; malak Taha'
ico=(root/'NilePhytoDock.ico').read_bytes();count=struct.unpack_from('<H',ico,4)[0];assert count==7
frames=[]
for i in range(count):
    size,offset=struct.unpack_from('<II',ico,6+16*i+8);frames.append(ico[offset:offset+size])
embedded=[]
for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries:
    if kind.id==3:
        for name in kind.directory.entries:
            for language in name.directory.entries:
                resource=language.data.struct;embedded.append(pe.get_data(resource.OffsetToData,resource.Size))
assert all(frame in embedded for frame in frames),'The embedded PE icon does not match the supplied ICO'
shortcuts=json.loads(Path('data/validation/studio_shortcuts.json').read_text(encoding='utf-8-sig'))
assert len(shortcuts)==2 and all(Path(r['Target']).resolve()==exe for r in shortcuts)
assert all(r['Icon'].casefold()==(str(root/'NilePhytoDock.ico')+',0').casefold() for r in shortcuts)
guide_hashes={}
for name in ['USER_GUIDE_AR.pdf','BUILD_AND_METHOD_AR.pdf']:
    original=Path('docs')/name;outside=root/'Documentation'/name;inside=root/'_internal/docs'/name
    digest=hashlib.sha256(original.read_bytes()).hexdigest()
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p in [outside,inside])
    guide_hashes[name]=digest
db=connect(user_data()/'nilephytodock.sqlite')
project=rows(db,"SELECT * FROM analysis_projects WHERE name='Studio 0.3 packaged validation' ORDER BY id DESC")[0]
assert project['status']=='complete',project['status']
runs=rows(db,'SELECT * FROM docking_runs WHERE project_id=?',(project['id'],));assert len(runs)==6
assert all(r['status']=='complete' and not r['error'] and r['elapsed']>0 for r in runs)
assert {205,206}.issubset({r['compound_id'] for r in runs})
poses=rows(db,'SELECT p.* FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id WHERE r.project_id=?',(project['id'],))
assert poses and all(Path(p[k]).exists() for p in poses for k in ['sdf_path','complex_path'])
commands=[]
for run in runs:
    pocket=rows(db,'SELECT * FROM predicted_pockets WHERE id=?',(run['pocket_id'],))[0]
    cmd=json.loads((Path(run['folder'])/'process.log').read_text(encoding='utf-8').splitlines()[0])
    center=[float(cmd[cmd.index('--center_'+a)+1]) for a in 'xyz'];size=[float(cmd[cmd.index('--size_'+a)+1]) for a in 'xyz']
    assert center==json.loads(pocket['center']) and size==json.loads(pocket['size'])
    commands.append({'run_id':run['id'],'elapsed':run['elapsed'],'center':center,'dimensions':size})
folder=Path(project['folder']);report_json=json.loads((folder/'Reports/reproducibility.json').read_text(encoding='utf-8'))
assert report_json['application']['version']=='0.3.0'
assert (folder/'Project_Data/project.nile.sqlite').exists()
assert not db.execute('PRAGMA foreign_key_check').fetchall();db.close()
seed=sqlite3.connect((root/'_internal/data/nilephytodock.sqlite').as_uri()+'?mode=ro',uri=True)
assert seed.execute('SELECT count(*) FROM analysis_projects').fetchone()[0]==0
assert seed.execute('SELECT count(*) FROM oil_profiles').fetchone()[0]==29;seed.close()
evidence={'version':'0.3.0','platform':'Windows 11 Pro 10.0.26200 x64','entry_point':str(exe),'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'properties':props,'icon_frames_matching_exe':count,'shortcut_targets_and_icons_verified':True,'guide_hashes':guide_hashes,'native_project_id':project['id'],'native_project_folder':project['folder'],'native_run_count':len(runs),'native_pose_count':len(poses),'native_runs':commands,'new_csv_thymol_carvacrol_screened':True,'gui_and_native_boxes_match':True,'project_snapshot_and_reports_verified':True,'seed_has_no_docking_results':True,'windows_10_tested':False,'clean_vm_tested':False}
Path('data/validation/studio_executable_verification.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
print('Studio verification complete:',len(runs),'actual jobs;',len(poses),'poses;',count,'matching icon sizes; both Arabic PDFs present')
