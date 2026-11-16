"""Apply the release ontology and verify every retained case-study contact."""
import json
from pathlib import Path
import numpy as np
from database.store import connect,rows
from scientific.molecular_analysis import analyze,export_analysis
from scientific.geometry import load_receptor,verify_contact
from scientific.molecules import read_sdf
from visualization.charts import chart_spec,export_chart
from visualization.interaction_diagram import diagram,save_diagram
root=Path('data/validation/case_study_final');db=connect(root/'case_study.sqlite');r=json.loads((root/'validation.json').read_text(encoding='utf-8'));a=analyze(db,1);export_analysis(a,root/'analysis')
count=0;max_error=0
for p in rows(db,'SELECT p.*,t.prepared_path FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id JOIN protein_targets t ON t.id=r.protein_id'):
 protein=load_receptor(p['prepared_path']);ligand=read_sdf(p['sdf_path'],removeHs=False)[0]
 for c in rows(db,'SELECT * FROM molecular_interactions WHERE pose_id=?',(p['id'],)):
  verify_contact(protein,ligand,c);g=json.loads(c['metadata'])['geometry'];pa=protein.GetConformer().GetPositions()[g['protein_indices']].mean(axis=0);la=ligand.GetConformer().GetPositions()[g['ligand_indices']].mean(axis=0);max_error=max(max_error,abs(float(np.linalg.norm(pa-la))-c['distance']));count+=1
r['enrichment']=[s['enrichment'] for s in a['site_cohorts']];r['all_contacts_independently_verified']=count;r['maximum_contact_distance_residual_A']=max_error;r['analysis_method']='Release ontology; independent Morgan/Tanimoto and site Jaccard; no repeated cluster or nonempty Murcko scaffold in enrichment representatives.'
first=next(b for b in r['benchmark'] if b['box']=='charged_experimental_box');repeat=next(b for b in r['benchmark'] if b['box']=='repeat_charged_experimental_box');delta=max(float(np.abs(read_sdf(p['sdf'],removeHs=True)[0].GetConformer().GetPositions()-read_sdf(q['sdf'],removeHs=True)[0].GetConformer().GetPositions()).max()) for p,q in zip(first['poses'],repeat['poses']));assert delta<1e-6;r['reference_repeat_max_coordinate_difference_A']=delta
fig=root/'publication_figures';fig.mkdir(exist_ok=True)
for kind in ['Compound Ranking','Functional Group Frequency Plot','Molecular Similarity Heatmap','Interaction Fingerprint Similarity Heatmap']:
 export_chart(chart_spec(db,1,kind,top_n=30),fig/kind.replace(' ','_'),300)
p=rows(db,"SELECT p.*,c.name FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id JOIN chemical_compounds c ON c.id=r.compound_id WHERE c.name='Thymol' ORDER BY p.score LIMIT 1")[0];svg,layout=diagram(p['sdf_path'],rows(db,'SELECT * FROM molecular_interactions WHERE pose_id=?',(p['id'],)),'Thymol | 3PTB | actual best saved pose',style='Circular');save_diagram(svg,fig/'Thymol_Circular',300);r['illustrated_pose_id']=p['id']
(root/'validation.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');db.close();print(count,'contacts verified;',delta,'A repeat difference;',r['enrichment'],flush=True)
