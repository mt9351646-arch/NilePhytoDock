"""Withdraw ambiguous automated approvals while preserving candidate files."""
import json
from pathlib import Path
from rdkit import Chem
from database.store import connect,rows
from scientific.ligands import validate_geometric_identity
db=connect('data/nilephytodock.sqlite');changed=[]
for row in rows(db,"SELECT s.*,c.name FROM compound_structures s JOIN chemical_compounds c ON c.id=s.compound_id WHERE s.status='ready'"):
 try:validate_geometric_identity(Chem.MolFromSmiles(row['smiles']),row['name'])
 except ValueError as error:
  changed.append({'compound_id':row['compound_id'],'name':row['name'],'previous_record':row,'reason':str(error)})
  props=json.loads(row['properties']);props['source_geometry_review']=str(error)
  note='Source geometry review: '+str(error)+' Candidate coordinates are retained; not authorized for new docking.'
  db.execute("UPDATE compound_structures SET status='identity_review',notes=?,properties=? WHERE compound_id=?",(note,json.dumps(props),row['compound_id']));db.execute("UPDATE chemical_compounds SET identity_status='identity_review',identity_notes=? WHERE id=?",(note,row['compound_id']))
db.commit();db.close();Path('data/validation/geometric_identity_review.json').write_text(json.dumps({'policy':'source-geometry-1','review_records':changed},ensure_ascii=False,indent=2),encoding='utf-8');print(len(changed),'generic geometric identities moved to review; candidate files preserved')
