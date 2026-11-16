import math
import xml.etree.ElementTree as ET
import pytest
import requests
from test_result_summary import study
from scientific.pdb_retrieval import normalize_id,retrieve
from visualization.release_charts import chart_spec,export_chart
from visualization.shared_groups import shared_groups,diagram

@pytest.mark.parametrize('value',[' 3ptb ','pdb_00003ptb','PDB: 3ptb','https://www.rcsb.org/structure/3PTB','https://files.rcsb.org/download/3PTB.pdb','https://doi.org/10.2210/pdb3ptb/pdb'])
def test_normalized_pdb_identifiers(value):assert normalize_id(value)=='3PTB'

def test_download_fallback_validates_and_never_poison_cached_structure(tmp_path):
 fixture=__import__('pathlib').Path('tests/fixtures/3PTB.pdb').read_text()
 class Session:
  calls=[]
  def get(self,url,**kwargs):
   self.calls.append(url);r=requests.Response();r.status_code=503 if len(self.calls)==1 else 200
   # A malformed mmCIF response also falls back to the alternate archive.
   if len(self.calls)==3:
    from Bio.PDB import PDBParser,MMCIFIO
    io=MMCIFIO();io.set_structure(PDBParser(QUIET=True).get_structure('3ptb','tests/fixtures/3PTB.pdb'));io.save(str(tmp_path/'fixture.cif'));text=(tmp_path/'fixture.cif').read_text()
   else:text='data_invalid\n# incomplete mmCIF response'
   r._content=text.encode();return r
 s=Session();path=retrieve(' 3ptb ',tmp_path,session=s)
 assert path.endswith('3PTB.cif') and len(s.calls)==3
 assert not (tmp_path/'3PTB.pdb').exists()
 class Missing:
  def get(self,*args,**kwargs):r=requests.Response();r.status_code=404;r._content=b'not found';return r
 with pytest.raises(ValueError,match='not found'):retrieve('0000',tmp_path,session=Missing())
 assert not (tmp_path/'0000.cif').exists()

def test_network_is_score_scaled_keeps_ties_and_oil_membership(study,tmp_path):
 db,pid,tid,site,oils,_=study
 spec=chart_spec(db,pid,'Docking Network',tid,pocket=site)
 assert len(spec['rows'])==4 and sorted({r['score'] for r in spec['rows']})==[-7,-5]
 for row in spec['rows']:
  assert math.isclose(math.hypot(row['network_x'],row['network_y']),1+row['score']+7)
 assert len({r['network_radius'] for r in spec['rows'] if r['score']==-5})==1
 bubble=chart_spec(db,pid,'Bubble Plot',tid,pocket=site)
 colors={t['name']:t['marker']['color'] for t in bubble['data']}
 assert all(colors[t['name']]==t['marker']['color'] for t in spec['data'] if t.get('showlegend',True))
 export_chart(spec,tmp_path/'network',100)
 assert all((tmp_path/'network').with_suffix(ext).stat().st_size>100 for ext in ('.png','.svg','.pdf','.csv','.xlsx','.json'))

def test_shared_drawings_use_actual_smarts_and_conventional_groups():
 details={'a':{'smiles':'CCO','compound':'Ethanol'},'b':{'smiles':'CCCO','compound':'Propanol'},'c':{'smiles':'COC','compound':'Dimethyl ether'}}
 groups=shared_groups(details)
 assert [g['name'] for g in groups]==['Alcohol hydroxyl'] and groups[0]['count']==2
 svg,meta=diagram(details,'Alcohol hydroxyl');ET.fromstring(svg)
 assert 'Ethanol' in svg and meta['total']==3 and 'Presence alone' in svg
 with pytest.raises(ValueError):diagram(details,'Ether')
 assert not shared_groups({'a':details['a']})

def test_interaction_map_uses_vdw_nodes_and_preserves_measured_contact_minimum(tmp_path):
 from rdkit import Chem
 from scientific.molecules import write_sdf
 from visualization.interaction_diagram import diagram
 import json
 path=tmp_path/'ethanol.sdf';write_sdf(path,Chem.MolFromSmiles('CCO'))
 contacts=[{'residue':'SER10.A','chain':'A','residue_number':10,'interaction_type':'HBDonor','distance':d,'metadata':json.dumps({'parent_indices':{'ligand':[2]}})} for d in [3.1,2.8]]
 contacts.append({'residue':'ALA11.A','chain':'A','residue_number':11,'interaction_type':'VdWContact','distance':3.5,'metadata':json.dumps({'parent_indices':{'ligand':[0]}})})
 svg,layout=diagram(path,contacts,types=False)
 assert layout['style']=='Interaction map' and layout['contact_count']==3 and layout['residues']==2
 assert len(layout['anchors'])==2
 assert next(a for a in layout['anchors'] if a['kind']=='HBDonor')['distance']==2.8
 assert not next(a for a in layout['anchors'] if a['kind']=='VdWContact')['visible_link']
 root=ET.fromstring(svg);assert len(list(root.iter('{http://www.w3.org/2000/svg}line')))==1
