from pathlib import Path
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from database.store import connect,rows
for r in rows(connect('data/nilephytodock.sqlite'),"SELECT c.id,c.name,s.inchikey FROM chemical_compounds c JOIN compound_structures s ON s.compound_id=c.id WHERE s.status='ready' AND s.inchikey IN (SELECT inchikey FROM compound_structures WHERE status='ready' GROUP BY inchikey HAVING count(*)>1)"):
 print(r)
