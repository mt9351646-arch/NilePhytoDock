import json
import shutil
import sqlite3
from pathlib import Path
from database.store import connect,rows

def relocate_saved_project(db,database_path):
    """Repair a moved self-contained copy, validating files before mutation."""
    base=Path(database_path).resolve().parent
    candidate=base/'calculations' if (base/'calculations').is_dir() else base.parent if base.name=='Project_Data' and (base.parent/'Docking').is_dir() else None
    if candidate is None:return False
    projects=rows(db,'SELECT * FROM analysis_projects')
    if len(projects)!=1:return False
    old=Path(projects[0]['folder']);candidate=candidate.resolve()
    if old.resolve()==candidate:return False
    updates=[]
    for table,fields in [('protein_targets',['original_path','prepared_path','pdbqt_path']),('docking_runs',['folder','log_path']),('docking_poses',['sdf_path','complex_path'])]:
        for row in rows(db,'SELECT * FROM '+table):
            for field in fields:
                if not row[field]:continue
                try:target=candidate/Path(row[field]).relative_to(old)
                except ValueError:continue
                if field not in ['log_path','folder'] and not target.is_file():raise ValueError('Saved study file is missing: '+str(target))
                updates.append((table,field,str(target),row['id']))
    with db:
        for table,field,value,identity in updates:db.execute('UPDATE '+table+' SET '+field+'=? WHERE id=?',(value,identity))
        db.execute('UPDATE analysis_projects SET folder=?',(str(candidate),))
    return True

def save_project(db,pid,destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    project=rows(db,'SELECT * FROM analysis_projects WHERE id=?',(pid,))[0]
    source=Path(project['folder']).resolve();target=destination/'calculations'
    if target.exists():raise ValueError('Choose a new empty project folder')
    shutil.copytree(source,target)
    copy=connect(destination/'project.nile.sqlite');db.backup(copy)
    # A saved project snapshot includes the selected analysis and its library,
    # rather than dangling references to other analyses' calculation folders.
    for table in ['ligand_functional_annotations','interaction_reanalyses']:
        copy.execute('DELETE FROM '+table+' WHERE pose_id IN (SELECT p.id FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id WHERE r.project_id!=?)',(pid,))
    copy.execute('DELETE FROM molecular_analysis_runs WHERE project_id!=?',(pid,))
    copy.execute('DELETE FROM molecular_interactions WHERE pose_id IN (SELECT p.id FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id WHERE r.project_id!=?)',(pid,))
    copy.execute('DELETE FROM docking_poses WHERE run_id IN (SELECT id FROM docking_runs WHERE project_id!=?)',(pid,))
    copy.execute('DELETE FROM docking_runs WHERE project_id!=?',(pid,))
    copy.execute('DELETE FROM ranking_results WHERE project_id!=?',(pid,))
    copy.execute('DELETE FROM predicted_pockets WHERE protein_id IN (SELECT id FROM protein_targets WHERE project_id!=?)',(pid,))
    copy.execute('DELETE FROM protein_targets WHERE project_id!=?',(pid,))
    copy.execute('DELETE FROM execution_logs WHERE project_id!=?',(pid,))
    copy.execute('DELETE FROM analysis_projects WHERE id!=?',(pid,))
    copy.execute('DELETE FROM calculation_cache')
    def rewrite(value):
        if not value:return value
        try:return str(target/Path(value).resolve().relative_to(source))
        except ValueError:return value
    for table,fields in [('protein_targets',['original_path','prepared_path','pdbqt_path']),('docking_runs',['folder','log_path']),('docking_poses',['sdf_path','complex_path'])]:
        for row in rows(copy,'SELECT * FROM '+table):
            for field in fields:copy.execute(f'UPDATE {table} SET {field}=? WHERE id=?',(rewrite(row[field]),row['id']))
    copy.execute('UPDATE analysis_projects SET folder=? WHERE id=?',(str(target),pid));copy.commit();copy.close()
    (destination/'project.json').write_text(json.dumps({'format':'NilePhytoDock project 1','project_id':pid,'database':'project.nile.sqlite','note':'Library resources resolve against installed application. Original project database snapshot retained.'},indent=2),encoding='utf-8')
    return destination/'project.nile.sqlite'

