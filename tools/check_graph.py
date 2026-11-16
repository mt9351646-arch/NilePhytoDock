from pathlib import Path
from rdkit import Chem
m=Chem.SDMolSupplier('data/validation/science/3PTB/prepared.sdf',removeHs=False)[0]
print('Receptor graph valid:',m is not None)
