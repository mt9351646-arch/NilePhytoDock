from database.store import connect,rows
from rdkit import Chem
import json
D=connect('data/nilephytodock.sqlite')
for r in rows(D,"SELECT c.id,c.name,s.smiles,s.pubchem_cid,s.sdf_path FROM chemical_compounds c JOIN compound_structures s ON s.compound_id=c.id WHERE c.name IN ('gamma-Terpinene','Eucalyptol','m-Cymene')"):
 print(r);print(Chem.MolToSmiles(Chem.SDMolSupplier(r['sdf_path'])[0]))
 payload=json.load(open(f'data/compound_library/pubchem_{r["id"]}.json',encoding='utf-8'));print(payload['PropertyTable']);print(payload['synonyms'][:15])
