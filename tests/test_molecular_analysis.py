import pytest
from rdkit import Chem
from scientific.functional_groups import identify,participating
from scientific.similarity import chemical,interaction,enrichment
from scientific.ligands import validate_small_molecule

def names(smiles):return [g['name'] for g in identify(Chem.MolFromSmiles(smiles))]

def test_specific_groups_take_precedence_over_overlapping_patterns():
 assert names('CC(=O)OC').count('Ester')==1 and 'Ether' not in names('CC(=O)OC')
 assert 'Ketone' not in names('CC(=O)OC') and 'Amine' not in names('CC(=O)N')
 assert 'Phenolic hydroxyl' in names('Oc1ccccc1') and 'Alcohol hydroxyl' not in names('Oc1ccccc1')
 assert 'Alcohol hydroxyl' in names('CCO') and 'Carboxylic acid/carboxylate' in names('CC(=O)[O-]')

def test_presence_is_distinct_from_contact_participation_and_h_mapping():
 m=Chem.AddHs(Chem.MolFromSmiles('CCO'));g=identify(m);h=next(a.GetIdx() for a in m.GetAtoms() if a.GetAtomicNum()==1 and a.GetNeighbors()[0].GetAtomicNum()==8)
 assert any(v['name']=='Alcohol hydroxyl' for v in participating(m,g,[h],'HBDonor'))
 assert not any(v['name']=='Alcohol hydroxyl' for v in participating(m,g,[0],'Hydrophobic'))

def test_morgan_similarity_is_h_representation_invariant_and_symmetric():
 a=Chem.MolFromSmiles('CCO');r=chemical([a,Chem.AddHs(a),Chem.MolFromSmiles('c1ccccc1')]);assert r['matrix'][0][1]==1 and r['matrix'][0][2]<1
 assert all(r['matrix'][i][j]==r['matrix'][j][i] for i in range(3) for j in range(3));assert r['clusters'][0]==r['clusters'][1]

def test_interaction_fingerprint_similarity_handles_empty_sets_and_categories():
 a={('A','10','','HBDonor')};b={('A','10','','Hydrophobic')};r=interaction([a,a,b,set()])['matrix'];assert r[0][1]==1 and r[0][2]==0 and r[3][3] is None

def test_enrichment_withholds_small_repeated_scaffolds():
 data=[{'identity':str(i),'cluster':1,'score':-10+i/10,'groups':['Ether']} for i in range(30)]
 assert not enrichment(data)['available'] and enrichment(data)['cluster_representatives']==1

def test_enrichment_bh_and_effect_sizes_are_explicit():
 data=[{'identity':str(i).zfill(2),'cluster':i,'score':float(i),'groups':['Alcohol hydroxyl'] if i<8 else ['Ether']} for i in range(24)]
 r=enrichment(data);assert r['available'] and len(r['rows'])==2
 assert all(0<=v['p_value']<=v['bh_q_value']<=1 for v in r['rows']);assert all(v['high_total']==6 and v['low_total']==6 for v in r['rows'])

def test_large_lipids_are_flagged_for_specialist_protocol():
 with pytest.raises(ValueError,match='standard small-molecule'):validate_small_molecule(Chem.MolFromSmiles('C'*85))

def test_polysulfide_feature_contains_the_complete_connected_sulfur_chain():
 m=Chem.MolFromSmiles('CSSSC');groups=[g for g in identify(m) if g['name']=='Disulfide/polysulfide'];assert len(groups)==1 and groups[0]['atoms']==[1,2,3]

def test_fixed_oil_and_sum_lipid_records_are_not_native_small_molecules():
 import json
 from pathlib import Path
 m=json.loads(Path('data/literature/comprehensive_manifest.json').read_text(encoding='utf-8'))
 fixed=[p for p in m['profiles'] if p['category']=='Fixed Oils'];assert len(fixed)>=8
 assert all(not p['rankable'] and all(not o['docking_eligible'] for o in p['observations']) for p in fixed)
 moringa=[p for p in fixed if p['species'].startswith('Moringa')];assert len(moringa)==2 and all('ratio' in p['basis'] for p in moringa)
 tea=next(p for p in m['profiles'] if p['species']=='Camellia sinensis');assert tea['category']=='Botanical Extracts' and tea['pmcid']=='PMC4115333'
