"""Idempotent historical metadata import; never changes chromatography values."""
import json
from pathlib import Path
def import_heritage(db,path):
 data=json.loads(Path(path).read_text(encoding='utf-8'));n=0
 for row in data['entries']:
  keys=list(row);n+=db.execute('INSERT OR IGNORE INTO botanical_history ('+','.join(keys)+') VALUES ('+','.join('?' for _ in keys)+')',[row[k] for k in keys]).rowcount
 db.commit();return n
def qualify_fixed_pools(db):
 """Analytical fatty-acid pools do not prove native free-acid abundance."""
 db.execute("UPDATE profile_compounds SET docking_eligible=0,notes=COALESCE(notes,'') || ' | Analytical fatty-acid pool: native free-acid abundance is not established; docking excluded.' WHERE profile_id IN (SELECT id FROM oil_profiles WHERE preparation_category='Fixed Oils' AND (lower(profile_type) LIKE '%fatty%' OR lower(quantitation_basis) LIKE '%fatty%')) AND docking_eligible=1")
 db.execute("UPDATE oil_profiles SET ranking_eligible=0 WHERE preparation_category='Fixed Oils'")
 # Analytical silylation products and silicone contaminants are not native
 # botanical constituents. Preserve the source observation and any old pose.
 for term in ['%trimethylsilyl%','%siloxan%','%silyl ester%','%perfluoro%']:
  db.execute("UPDATE profile_compounds SET docking_eligible=0,notes=COALESCE(notes,'') || ' | Analytical derivative/contaminant requires source review; not a native constituent.' WHERE compound_id IN (SELECT id FROM chemical_compounds WHERE lower(name) LIKE ?) AND docking_eligible=1",(term,))
 invalid=db.execute("SELECT s.compound_id FROM compound_structures s JOIN chemical_compounds c ON c.id=s.compound_id WHERE s.status='ready' AND (lower(c.name) LIKE '%trimethylsilyl%' OR lower(c.name) LIKE '%siloxan%' OR lower(c.name) LIKE '%silyl ester%' OR lower(c.name) LIKE '%perfluoro%')").fetchall()
 for row in invalid:
  note='Source quality review: analytical derivative or silicone/fluorinated library annotation is not approved as a native botanical molecule. Candidate files retained.'
  db.execute("UPDATE compound_structures SET status='source_review',notes=? WHERE compound_id=?",(note,row[0]));db.execute("UPDATE chemical_compounds SET identity_status='source_review',identity_notes=? WHERE id=?",(note,row[0]))
 from scientific.ligands import validate_small_molecule
 from rdkit import Chem
 for row in db.execute("SELECT compound_id,smiles FROM compound_structures WHERE status='ready'").fetchall():
  try:validate_small_molecule(Chem.MolFromSmiles(row[1]))
  except ValueError as error:
   note='Standard scope review: '+str(error)+'; candidate files and previous raw results retained.'
   db.execute("UPDATE compound_structures SET status='scope_review',notes=? WHERE compound_id=?",(note,row[0]));db.execute("UPDATE chemical_compounds SET identity_status='scope_review',identity_notes=? WHERE id=?",(note,row[0]))
 db.commit()
