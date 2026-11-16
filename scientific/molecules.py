"""Unicode-safe molecular file I/O on Windows.

Python opens paths through Windows Unicode APIs; chemistry libraries receive
streams or in-memory blocks instead of narrow-character filenames.
"""
from pathlib import Path
from rdkit import Chem

def read_sdf(path,removeHs=True):
    with Path(path).open('rb') as stream:
        return list(Chem.ForwardSDMolSupplier(stream,removeHs=removeHs))

def write_sdf(path,molecule):
    with Path(path).open('w',encoding='utf-8',newline='\n') as stream:
        writer=Chem.SDWriter(stream)
        writer.write(molecule)
        writer.close()
