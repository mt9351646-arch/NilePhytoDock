"""Scientific regression tests; synthetic records here are test fixtures only."""
import json,sqlite3
from pathlib import Path
import pytest
from rdkit import Chem
from database.store import connect,counts,insert,rows
from scientific.ranking import oil_indices
from scientific.ligands import validate_geometric_identity
from visualization.semantics import PALETTE,residue_color,stable_color

def test_unique_dashboard_counts_do_not_count_profiles_or_structure_aliases(tmp_path):
 src=sqlite3.connect('data/nilephytodock.sqlite');dst=sqlite3.connect(tmp_path/'counts.sqlite');src.backup(dst);dst.close();src.close();db=connect(tmp_path/'counts.sqlite');before=counts(db)
 assert before['essential_oils']>=35 and before['botanical_oils']>=before['essential_oils']
 p=dict(db.execute("SELECT * FROM oil_profiles WHERE profile_type='Essential oil' LIMIT 1").fetchone());p.pop('id');p['name']='Synthetic test copy';insert(db,'oil_profiles',**p)
 s=dict(db.execute("SELECT * FROM compound_structures WHERE status='ready' LIMIT 1").fetchone());s.pop('id');cid=insert(db,'chemical_compounds',name='Synthetic identity alias');s['compound_id']=cid;insert(db,'compound_structures',**s)
 after=counts(db);assert after['essential_oils']==before['essential_oils'] and after['unique_ready']==before['unique_ready'];assert after['profiles']==before['profiles']+1 and after['compounds']==before['compounds']+1;db.close()

def test_six_oils_evaluated_without_duplicate_thyme_and_without_false_egyptian_claim():
 m=json.loads(Path('data/literature/six_oils_manifest.json').read_text(encoding='utf-8'));assert len(m['evaluation'])==6 and len(m['profiles'])==5
 assert not any(p['species']=='Thymus vulgaris' for p in m['profiles'])
 peppermint=next(p for p in m['profiles'] if p['common_name']=='Peppermint');assert 'Morocco' in peppermint['origin'] and peppermint['geography_status']=='Non-Egyptian reference sample'
 # Published rounded rows sum to 99.52 while the printed total says 99.51.
 # Preserve every row rather than altering one to force the total.
 assert sum(o['value'] for o in peppermint['observations'])==pytest.approx(99.52)
 suspect=next(o for o in peppermint['observations'] if o['original_name']=='Methyl acetate');assert suspect['value']==12.1 and not suspect['docking_eligible']

def test_source_review_abundance_cannot_enter_coverage_even_if_a_score_exists():
 result=oil_indices({1:[{'compound_id':1,'percentage':50,'docking_eligible':0},{'compound_id':2,'percentage':30,'docking_eligible':1},{'compound_id':3,'percentage':20,'docking_eligible':1}]},{1:-10,2:-8,3:-4})[0]
 assert result['screened_peak_area_percent']==50 and result['reported_peak_area_percent']==100
 assert result['index']==pytest.approx(.6) and result['best_constituent_score']==-8

def test_identical_structures_do_not_duplicate_percentile_population_or_oil_composition():
 records={1:[{'compound_id':1,'chemical_identity':'same','percentage':80},{'compound_id':3,'chemical_identity':'other','percentage':20}],2:[{'compound_id':2,'chemical_identity':'same','percentage':100}]}
 result=oil_indices(records,{1:-8,2:-8,3:-4});assert next(r for r in result if r['profile_id']==1)['index']==pytest.approx(.8)
 duplicate=oil_indices({1:[{'compound_id':1,'chemical_identity':'same','percentage':50},{'compound_id':2,'chemical_identity':'same','percentage':50}]},{1:-8,2:-8})[0];assert duplicate['index'] is None

def test_ambiguous_geometric_identity_is_not_approved():
 with pytest.raises(ValueError,match='does not establish'):validate_geometric_identity(Chem.MolFromSmiles('CCC/C=C/C'),'Hexene')
 with pytest.raises(ValueError,match='unspecified'):validate_geometric_identity(Chem.MolFromSmiles('CCCC=CC'),'trans-Hexene')
 validate_geometric_identity(Chem.MolFromSmiles('CCC/C=C/C'),'(E)-Hexene')

def test_residue_colors_are_independent_from_interaction_line_categories():
 assert PALETTE['PiCation']!=PALETTE['FaceToFace'] and PALETTE['MetalDonor']!=PALETTE['Cationic']
 assert residue_color('ASP','Charge')!=PALETTE['HBDonor'] and residue_color('ASP','Charge')==residue_color('GLU','Charge')
 assert stable_color('Ocimum basilicum')==stable_color('Ocimum basilicum')
