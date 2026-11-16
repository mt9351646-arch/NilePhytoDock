"""Synthetic persistence fixtures, never packaged as scientific results."""
import json,shutil
from pathlib import Path
from database.store import connect,insert
from app.projects import save_project,relocate_saved_project

def test_save_one_of_two_analyzed_projects_and_move_copy_without_losing_history(tmp_path):
 db=connect(tmp_path/'original.sqlite');cid=insert(db,'chemical_compounds',name='Synthetic fixture');projects=[]
 for number in [1,2]:
  folder=tmp_path/('study'+str(number));folder.mkdir();file=folder/'fixture.sdf';file.write_text('Synthetic persistence fixture, not molecular data',encoding='utf-8')
  pid=insert(db,'analysis_projects',name='Synthetic '+str(number),folder=str(folder),settings='{}');projects.append(pid);tid=insert(db,'protein_targets',project_id=pid,original_path=str(file),prepared_path=str(file),pdbqt_path=str(file));site=insert(db,'predicted_pockets',protein_id=tid,rank=1);rid=insert(db,'docking_runs',project_id=pid,protein_id=tid,pocket_id=site,compound_id=cid,folder=str(folder));pose=insert(db,'docking_poses',run_id=rid,rank=1,sdf_path=str(file),complex_path=str(file));insert(db,'ligand_functional_annotations',pose_id=pose,ontology_version='test',groups_json='[]');insert(db,'interaction_reanalyses',pose_id=pose,previous_records='[]');insert(db,'molecular_analysis_runs',project_id=pid,result='{}')
 db.commit();saved=save_project(db,projects[0],tmp_path/'saved');assert db.execute('SELECT count(*) FROM analysis_projects').fetchone()[0]==2 and db.execute('SELECT count(*) FROM interaction_reanalyses').fetchone()[0]==2
 moved=tmp_path/'moved';assert saved.parent.resolve().is_relative_to(tmp_path.resolve()) and moved.resolve().is_relative_to(tmp_path.resolve());shutil.move(str(saved.parent),moved)
 copy=connect(moved/saved.name);assert relocate_saved_project(copy,moved/saved.name)
 assert copy.execute('SELECT count(*) FROM analysis_projects').fetchone()[0]==1 and copy.execute('SELECT count(*) FROM ligand_functional_annotations').fetchone()[0]==1
 assert copy.execute('SELECT count(*) FROM interaction_reanalyses').fetchone()[0]==1 and copy.execute('SELECT count(*) FROM molecular_analysis_runs').fetchone()[0]==1
 assert Path(copy.execute('SELECT sdf_path FROM docking_poses').fetchone()[0]).read_text(encoding='utf-8').startswith('Synthetic') and not copy.execute('PRAGMA foreign_key_check').fetchall();copy.close();db.close()
