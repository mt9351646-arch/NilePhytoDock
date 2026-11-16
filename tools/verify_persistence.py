import json,time
from pathlib import Path
from app.projects import save_project
from database.store import connect,rows
from scientific.pipeline import run_project

def main():
    folder=Path('data/validation/verified_workflow_v2').resolve();db=connect(folder/'screening.sqlite')
    before=rows(db,'SELECT id,cache_key,status FROM docking_runs ORDER BY id')
    result=run_project(db,1,progress=lambda text,done,total:print(text,flush=True))
    after=rows(db,'SELECT id,cache_key,status FROM docking_runs ORDER BY id')
    if before!=after:raise AssertionError('Resume created or changed docking runs despite unchanged inputs')
    destination=folder/('saved_project_'+str(int(time.time())))
    saved=save_project(db,1,destination);copy=connect(saved)
    poses=rows(copy,'SELECT sdf_path,complex_path FROM docking_poses')
    if not all(Path(p[k]).exists() for p in poses for k in ['sdf_path','complex_path']):raise AssertionError('Snapshot pose files missing')
    if copy.execute('PRAGMA foreign_key_check').fetchall():raise AssertionError('Snapshot foreign keys invalid')
    report={'resume_without_new_docking_runs':True,'run_count':len(after),'saved_project':str(saved),'saved_pose_files_verified':len(poses),'foreign_keys_valid':True}
    (folder/'persistence_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)

if __name__=='__main__':main()
