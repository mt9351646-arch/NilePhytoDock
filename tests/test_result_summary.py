"""Result summaries must respect source membership, identities, sites and protocols."""
import json
import pytest
from database.store import connect,insert
from scientific.result_summary import oil_results,group_results
from rdkit import Chem

@pytest.fixture
def study(tmp_path):
 db=connect(tmp_path/'summary.sqlite');species=insert(db,'plant_species',name='Synthetic fixture plant');oils=[insert(db,'essential_oils',species_id=species,name=n) for n in ['Fixture oil A','Fixture oil B','Fixture empty oil']];profiles=[insert(db,'oil_profiles',oil_id=o,name='Fixture sample '+str(i),quantitation_basis='GC peak area %') for i,o in enumerate(oils)];pid=insert(db,'analysis_projects',name='Synthetic summary test',settings=json.dumps({'profiles':profiles}));tid=insert(db,'protein_targets',project_id=pid,name='Fixture receptor');site=insert(db,'predicted_pockets',protein_id=tid,rank=1);other=insert(db,'predicted_pockets',protein_id=tid,rank=2)
 molecules=[]
 for i,smiles in enumerate(['CCO','CCO','COC','CC(=O)C']):
  mol=Chem.MolFromSmiles(smiles);path=tmp_path/f'ligand_{i}.sdf';writer=Chem.SDWriter(str(path));writer.write(mol);writer.close();cid=insert(db,'chemical_compounds',name='Fixture compound '+str(i));insert(db,'compound_structures',compound_id=cid,inchikey=Chem.MolToInchiKey(mol),smiles=smiles,status='ready',sdf_path=str(path));molecules.append((cid,path))
 def member(profile,index,value=20,eligible=1):insert(db,'profile_compounds',profile_id=profiles[profile],compound_id=molecules[index][0],reported_value=value,reported_unit='GC peak area %',docking_eligible=eligible)
 member(0,0);member(0,1);member(0,2);member(1,0,5);member(1,3,50);member(2,2,10,0)
 def pose(index,score,scoring='vina',pocket=site,status='complete'):
  run=insert(db,'docking_runs',project_id=pid,protein_id=tid,pocket_id=pocket,compound_id=molecules[index][0],settings=json.dumps({'scoring':scoring,'exhaustiveness':8,'seed':1}),engine_version='Fixture engine',status=status);return insert(db,'docking_poses',run_id=run,rank=1,score=score,sdf_path=str(molecules[index][1]))
 pose(0,-6);pose(1,-7);pose(2,-5);pose(3,-5);pose(2,-99,'ad4_scoring');pose(0,-100,pocket=other);pose(3,-101,status='failed');db.commit()
 yield db,pid,tid,site,oils,pose
 db.close()

def test_oil_summary_deduplicates_aliases_and_keeps_shared_oil_membership(study):
 db,pid,tid,site,oils,_=study;r=oil_results(db,pid,tid,site);a=next(o for o in r['oils'] if o['oil_id']==oils[0]);b=next(o for o in r['oils'] if o['oil_id']==oils[1]);empty=next(o for o in r['oils'] if o['oil_id']==oils[2])
 assert len(a['compounds'])==2 and len(b['compounds'])==2 and not empty['compounds']
 assert a['compounds'][0]['score']==b['compounds'][0]['score']==-7
 assert len(r['compounds'])==3 and len(a['compounds'][0]['observations'])==1

def test_oil_summary_does_not_mix_sites_protocols_or_failed_runs(study):
 db,pid,tid,site,_,_=study;r=oil_results(db,pid,tid,site);assert len(r['protocols'])==2
 # Explicitly select Vina because the default is deterministic by saved energy.
 key=next(p['key'] for p in r['protocols'] if json.loads(p['key'])['scoring']=='vina');r=oil_results(db,pid,tid,site,key)
 assert sorted(p['score'] for p in r['compounds'])==[-7,-5,-5]

def test_group_summary_retains_cutoff_ties_and_separates_presence_from_contacts(study,monkeypatch):
 db,pid,tid,site,_,_=study
 monkeypatch.setattr('scientific.contact_store.ensure_pose_contacts',lambda *_:[])
 r=oil_results(db,pid,tid,site);key=next(p['key'] for p in r['protocols'] if json.loads(p['key'])['scoring']=='vina');g=group_results(db,pid,tid,site,top_n=2,protocol=key)
 assert g['cohort_size']==3 and g['available_compounds']==3 and g['cutoff']==-5
 assert {v['group'] for v in g['groups']}=={'Alcohol hydroxyl','Ether','Ketone'}
 assert all(v['top_compounds']==1 and v['contacting_compounds']==0 for v in g['groups'])
 assert all(v['domain']=='Molecular feature' for v in g['features'])

def test_group_summary_does_not_treat_unavailable_contacts_as_verified_absence(study,monkeypatch):
 db,pid,tid,site,_,_=study
 def fail(*_):raise ValueError('Synthetic missing geometry')
 monkeypatch.setattr('scientific.contact_store.ensure_pose_contacts',fail)
 g=group_results(db,pid,tid,site,top_n=1);assert g['contact_errors'] and all(d['direct_contact']=='Unavailable' for d in g['details'])

def test_vdw_only_contacts_are_optional_and_not_specific_group_participation(study,monkeypatch):
 db,pid,tid,site,_,_=study
 monkeypatch.setattr('scientific.contact_store.ensure_pose_contacts',lambda *_:[{'metadata':json.dumps({'geometry':{'ligand_indices':[2]}}),'interaction_type':'VdWContact','residue':'SER1.A'}])
 default=group_results(db,pid,tid,site,top_n=1);including=group_results(db,pid,tid,site,top_n=1,include_vdw=True)
 assert default['groups'][0]['group']=='Alcohol hydroxyl' and default['groups'][0]['contacting_compounds']==0
 assert including['groups'][0]['contacting_compounds']==1

def test_zero_or_unreported_values_do_not_imply_membership_but_explicit_trace_does(study):
 db,pid,tid,site,oils,_=study
 profile=db.execute('SELECT id FROM oil_profiles WHERE oil_id=?',(oils[2],)).fetchone()[0];cid=db.execute('SELECT id FROM chemical_compounds WHERE name=?',('Fixture compound 0',)).fetchone()[0]
 observation=insert(db,'profile_compounds',profile_id=profile,compound_id=cid,reported_value=0,reported_unit='GC peak area %',docking_eligible=1)
 assert not next(o for o in oil_results(db,pid,tid,site)['oils'] if o['oil_id']==oils[2])['compounds']
 db.execute('UPDATE profile_compounds SET reported_value=NULL WHERE id=?',(observation,));db.commit()
 assert not next(o for o in oil_results(db,pid,tid,site)['oils'] if o['oil_id']==oils[2])['compounds']
 db.execute('UPDATE profile_compounds SET value_status=? WHERE id=?',('trace',observation));db.commit()
 assert len(next(o for o in oil_results(db,pid,tid,site)['oils'] if o['oil_id']==oils[2])['compounds'])==1
