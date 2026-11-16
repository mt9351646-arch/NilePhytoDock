"""The minimal chart page must preserve protocol, source and contact semantics."""
import json,time
from test_result_summary import study
from database.store import insert
from visualization.release_charts import CHARTS,chart_spec

def test_chart_protocol_site_deduplication_and_shared_membership(study):
 db,pid,tid,site,oils,_=study
 before=db.total_changes
 spec=chart_spec(db,pid,'Bubble Plot',tid,pocket=site)
 assert sorted({r['score'] for r in spec['rows']})==[-7,-5]
 assert len(spec['rows'])==4 # two aliases merge, shared oils remain separate observations
 assert len({r['identity'] for r in spec['rows']})==3
 assert len({t['marker']['color'] for t in spec['data']})==2
 assert db.total_changes==before
 assert len(chart_spec(db,pid,'Bubble Plot',tid,oil=oils[0],pocket=site)['rows'])==2
 assert not chart_spec(db,pid,'Bubble Plot',tid,oil=oils[2],pocket=site)['available']

def test_heatmap_uses_numeric_scores_not_oil_averages(study):
 db,pid,tid,site,oils,_=study
 spec=chart_spec(db,pid,'Docking Heatmap',tid,pocket=site,top_n=2)
 assert len(spec['rows'])==2
 assert spec['data'][0]['z']==[[-7.0],[-5.0]]
 assert len(CHARTS)==4

def test_duplicate_target_names_remain_separate_heatmap_columns(study):
 db,pid,tid,site,_,_=study
 name=db.execute('SELECT name FROM protein_targets WHERE id=?',(tid,)).fetchone()[0]
 second=insert(db,'protein_targets',project_id=pid,name=name)
 pocket=insert(db,'predicted_pockets',protein_id=second,rank=1)
 run=dict(db.execute('SELECT * FROM docking_runs LIMIT 1').fetchone());run.pop('id');run.update(protein_id=second,pocket_id=pocket)
 rid=insert(db,'docking_runs',**run);insert(db,'docking_poses',run_id=rid,rank=1,score=-8);db.commit()
 spec=chart_spec(db,pid,'Docking Heatmap')
 assert len(spec['data'][0]['z'][0])==2
 assert len(set(spec['layout']['xaxis']['ticktext']))==2

def test_interaction_matrix_counts_structures_not_atom_pair_events(study):
 db,pid,tid,site,_,_=study
 heatmap=chart_spec(db,pid,'Docking Heatmap',tid,pocket=site)
 ids=[r['pose_id'] for r in heatmap['rows']]
 for pose in [ids[0],ids[0],ids[1]]:
  insert(db,'molecular_interactions',pose_id=pose,residue='SER1.A',chain='A',residue_number=1,interaction_type='HBDonor',distance=2.9)
 db.commit();spec=chart_spec(db,pid,'Interaction Matrix',tid,pocket=site)
 assert spec['rows'][0]['distinct_compounds']==2
 assert spec['rows'][0]['contact_events']==3
 assert spec['data'][0]['z']==[[2]]

def test_large_saved_dataset_is_bounded_and_read_only(study):
 db,pid,tid,site,_,_=study
 run=dict(db.execute('SELECT * FROM docking_runs LIMIT 1').fetchone())
 columns=[c for c in run if c!='id'];values=[run[c] for c in columns]
 # Repeated jobs stress the saved-pose query without changing the scientific seed.
 db.executemany('INSERT INTO docking_runs ('+','.join(columns)+') VALUES ('+','.join('?' for _ in columns)+')',[values]*20000)
 db.execute('INSERT INTO docking_poses (run_id,rank,score) SELECT id,1,-6 FROM docking_runs WHERE id>7');db.commit()
 before=db.total_changes;start=time.perf_counter()
 for kind in CHARTS:
  spec=chart_spec(db,pid,kind,tid,pocket=site,top_n=5)
  assert len(spec['rows'])<=10
 assert time.perf_counter()-start<10
 assert db.total_changes==before
