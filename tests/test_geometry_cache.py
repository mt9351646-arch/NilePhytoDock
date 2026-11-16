import pytest
from rdkit import Chem
from scientific.geometry import load_receptor
from scientific.molecules import write_sdf

def test_receptor_cache_cannot_hide_file_corruption_or_caller_mutation(tmp_path):
 mol=Chem.MolFromSmiles('CC');conf=Chem.Conformer(2);conf.SetAtomPosition(0,(0,0,0));conf.SetAtomPosition(1,(1.5,0,0));mol.AddConformer(conf)
 path=tmp_path/'protein.pdb';path.write_text(Chem.MolToPDBBlock(mol),encoding='utf-8');write_sdf(path.with_suffix('.sdf'),mol)
 first=load_receptor(path);first.GetConformer().SetAtomPosition(0,(9,0,0));assert load_receptor(path).GetConformer().GetAtomPosition(0).x==0
 text=path.read_text();line=text.splitlines()[0];path.write_text(text.replace(line,line[:30]+'   0.200'+line[38:],1),encoding='utf-8')
 with pytest.raises(ValueError,match='coordinate/atom-order'):load_receptor(path)
