"""Fresh real-engine validation and botanical screening with complete raw evidence."""
import json,sqlite3,time,hashlib
from pathlib import Path
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolAlign
from database.store import connect,rows
from scientific.pipeline import create_project,run_project,DEFAULTS
from scientific.runtime import Runner,health,sha
from scientific.proteins import reference_box
from scientific.ligands import prepare
from scientific.docking import dock
from scientific.molecular_analysis import analyze,export_analysis,interaction_rows,export_tables
from scientific.ranking import project_rankings

def main():
 root=Path('data/validation/case_study_reviewed').resolve();root.mkdir(parents=True,exist_ok=True);path=root/'case_study.sqlite'
 if path.exists():raise ValueError('Case-study destination already exists; preserve it and select a fresh folder')
 source=sqlite3.connect('data/nilephytodock.sqlite');target=sqlite3.connect(path);source.backup(target);target.close();source.close();db=connect(path)
 profiles=[r['id'] for r in rows(db,"SELECT id FROM oil_profiles WHERE name LIKE 'Thymus vulgaris%Giza%' OR name LIKE 'Coriandrum sativum%ARC%' OR name LIKE 'Pimpinella anisum%ARC%' OR name LIKE 'Ocimum basilicum%Tanta%' OR name LIKE 'Cuminum cyminum%Egyptian market%'")];assert len(profiles)==5
 settings={**DEFAULTS,'exhaustiveness':8,'num_modes':3,'seed':20261029,'cpu':2,'remove_heterogens':['BEN A:1'],'pocket_mode':'Automatic'}
 pid=create_project(db,'Five botanical profiles against bovine trypsin 3PTB',['tests/fixtures/3PTB.pdb'],profiles,settings,root/'screening')
 started=time.monotonic();result=run_project(db,pid,progress=lambda text,done,total:print(f'{done}/{total} {text}',flush=True));assert not result['failures'],result
 assert all(r['status']=='complete' for r in rows(db,'SELECT status FROM docking_runs WHERE project_id=?',(pid,)))
 receptor=rows(db,'SELECT * FROM protein_targets WHERE project_id=?',(pid,))[0];pockets=rows(db,'SELECT * FROM predicted_pockets WHERE protein_id=? ORDER BY rank',(receptor['id'],));top=pockets[0]
 experimental=Chem.SDMolSupplier('tests/fixtures/3PTB_BEN_reference.sdf',removeHs=True)[0];xyz=experimental.GetConformer().GetPositions();centroid=xyz.mean(axis=0);center=np.array(json.loads(top['center']));size=np.array(json.loads(top['size']));inside=np.all(np.abs(xyz-center)<=size/2,axis=1)
 sdf,_,props=prepare(Chem.MolToSmiles(experimental),root/'reference_ligand','BEN');ref_center,ref_size=reference_box('tests/fixtures/3PTB.pdb','BEN A:1');benchmark=[]
 for label,c,s in [('experimental_box',ref_center,ref_size),('predicted_box',center.tolist(),size.tolist()),('repeat_experimental_box',ref_center,ref_size)]:
  poses,elapsed=dock(receptor['pdbqt_path'],sdf,c,s,{**settings,'exhaustiveness':16,'num_modes':5},root/label,Runner());metrics=[]
  for p in poses:
   mol=Chem.SDMolSupplier(p['sdf_path'],removeHs=True)[0];metrics.append({'pose':p['rank'],'score_kcal_mol':p['score'],'symmetry_corrected_no_alignment_rmsd_A':rdMolAlign.CalcRMS(mol,experimental),'sdf':p['sdf_path']})
  benchmark.append({'box':label,'center':c,'size':s,'elapsed_seconds':elapsed,'poses':metrics});print(label,metrics,flush=True)
 a=analyze(db,pid);repeat=analyze(db,pid,save=False);assert a['signature']==repeat['signature'] and a['chemical_similarity']==repeat['chemical_similarity'];export_analysis(a,root/'analysis')
 contacts=interaction_rows(db,pid);export_tables(contacts,root/'tables/complete_interactions','Complete case study interactions');export_tables(interaction_rows(db,pid,'Best Pose Interactions'),root/'tables/best_pose_interactions','Best pose interactions')
 runs=rows(db,'SELECT * FROM docking_runs WHERE project_id=?',(pid,));boxes=[]
 for run in runs:
  command=json.loads((Path(run['folder'])/'process.log').read_text(encoding='utf-8').splitlines()[0]);actual_center=[float(command[command.index('--center_'+c)+1]) for c in 'xyz'];actual_size=[float(command[command.index('--size_'+c)+1]) for c in 'xyz'];assert actual_center==json.loads(top['center']) and actual_size==json.loads(top['size']);boxes.append({'run':run['id'],'center':actual_center,'size':actual_size})
 report={'target':'Bovine beta-trypsin 3PTB','reference_ligand':'Benzamidine BEN A:1','target_source':'https://www.rcsb.org/structure/3PTB','experimental_comparator':'Published bovine trypsin benzamidine Ki 33 micromolar, PMC17520; protocol and botanical measurements not matched, so no score/activity correlation or AUROC calculated.','experimental_reference_source':'https://pmc.ncbi.nlm.nih.gov/articles/PMC17520/','project_id':pid,'engines':health(),'settings':settings,'profiles':rows(db,'SELECT id,name,origin FROM oil_profiles WHERE id IN ('+','.join('?' for _ in profiles)+')',profiles),'unique_jobs':len(runs),'saved_poses':db.execute('SELECT count(*) FROM docking_poses').fetchone()[0],'all_runs_complete':True,'p2rank_pocket_center_to_crystal_ligand_centroid_A':float(np.linalg.norm(center-centroid)),'crystal_heavy_atoms_inside_predicted_box':int(inside.sum()),'crystal_heavy_atom_count':len(xyz),'benchmark':benchmark,'ranking':project_rankings(db,pid),'chemical_diversity':{k:v for k,v in a['chemical_similarity'].items() if k not in ['matrix','clusters']},'functional_group_associations':len(a['functional_group_interactions']),'interaction_events':len(contacts),'enrichment':[s['enrichment'] for s in a['site_cohorts']],'repeat_analysis_identical':True,'all_actual_command_boxes_match_selected_pocket':boxes,'elapsed_seconds':time.monotonic()-started,'limitations':'Single rigid-receptor target; standard protonation approximation; no side-chain/loop repair or water network analysis. Source coverage is incomplete. No mixture synergy, clinical activity, potency or selectivity inference.'}
 (root/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');db.close();print('Case study complete',report['unique_jobs'],'jobs',flush=True)
if __name__=='__main__':main()
