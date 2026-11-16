"""Cross-check every prepared formula with authoritative PubChem CID data."""
import json,time
from pathlib import Path
import requests
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from database.store import connect,rows
db=connect('data/nilephytodock.sqlite');structures=rows(db,"SELECT * FROM compound_structures WHERE status='ready'");cids=sorted({s['pubchem_cid'] for s in structures},key=int);cache=Path('data/compound_library/pubchem_formula_verification.json')
if cache.exists():payload=json.loads(cache.read_text())
else:payload={}
missing=[cid for cid in cids if cid not in payload]
for start in range(0,len(missing),80):
 group=missing[start:start+80];url='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/'+','.join(group)+'/property/MolecularFormula/JSON';response=requests.get(url,timeout=45);response.raise_for_status()
 for p in response.json()['PropertyTable']['Properties']:payload[str(p['CID'])]={'formula':p['MolecularFormula'],'source_url':url}
 cache.write_text(json.dumps(payload,indent=2),encoding='utf-8');time.sleep(.25)
for s in structures:
 mol=Chem.MolFromSmiles(s['smiles']);formula=rdMolDescriptors.CalcMolFormula(mol);published=payload[s['pubchem_cid']]['formula'];assert formula==published,(s['compound_id'],formula,published)
 props=json.loads(s['properties']);props.update(molecular_formula=formula,formula_verified_against_pubchem_cid=True);db.execute('UPDATE compound_structures SET properties=? WHERE compound_id=?',(json.dumps(props),s['compound_id']))
db.commit();db.close();result={'ready_records':len(structures),'unique_pubchem_cids':len(cids),'all_rdkit_formulas_match_pubchem':True,'source_formula_not_reported_policy':'PubChem/RDKit formula agreement validates the resolved structure; it does not establish an uncertain analytical annotation.'};Path('data/validation/formula_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result)
