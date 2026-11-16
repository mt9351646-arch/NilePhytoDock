from rdkit import Chem
from pathlib import Path
for f in ['data/validation/science/benchmark_ligand/compound_BEN.sdf','data/validation/science/redocking/docked.sdf']:
 print(f)
 for m in Chem.SDMolSupplier(f,removeHs=True):print(Chem.MolToSmiles(m),m.GetPropsAsDict())
