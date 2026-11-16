"""Real multi-protein integration test, using only source-library ligands."""
import json
from pathlib import Path
from database.store import connect,rows
from scientific.pipeline import create_project,run_project,DEFAULTS
from reporting.export import export_all

def main():
    folder=Path('data/validation/verified_workflow_v2').resolve();folder.mkdir(parents=True,exist_ok=True)
    dbpath=folder/'screening.sqlite'
    if not dbpath.exists():
        seed=connect('data/nilephytodock.sqlite');db=connect(dbpath);seed.backup(db);seed.close()
    else:db=connect(dbpath)
    existing=db.execute('SELECT id FROM analysis_projects ORDER BY id DESC LIMIT 1').fetchone()
    pid=existing[0] if existing else create_project(db,'Real multi-target validation — 3PTB and 1IEP',['tests/fixtures/3PTB.pdb','tests/fixtures/1IEP.pdb'],[17],{**DEFAULTS,'exhaustiveness':2,'num_modes':2,'remove_heterogens':['BEN A:1','STI A:201','STI B:202']},folder/'calculations')
    result=run_project(db,pid,progress=lambda text,done,total:print(f'{done}/{total} {text}',flush=True))
    print('RESULT',result,flush=True)
    export_all(db,pid,folder/'report')
    summary={'project_id':pid,**result,'runs':rows(db,'SELECT id,protein_id,compound_id,status,error FROM docking_runs'),'pose_count':db.execute('SELECT count(*) FROM docking_poses').fetchone()[0],'interaction_count':db.execute('SELECT count(*) FROM molecular_interactions').fetchone()[0],'targets':rows(db,'SELECT name,status,error FROM protein_targets')}
    (folder/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(summary,flush=True)
    if result['failures'] or any(r['status']!='complete' for r in summary['runs']):raise RuntimeError('End-to-end test has failures or interaction review statuses')

if __name__=='__main__':main()
