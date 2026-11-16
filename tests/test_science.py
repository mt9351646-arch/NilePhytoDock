import math
from pathlib import Path
import pytest
import numpy as np
from rdkit import Chem
import prolif as plf
from scientific.pockets import validate_box
from scientific.proteins import inspect,prepare
from scientific.runtime import Runner,Cancelled
from scientific.ligands import prepare as prepare_ligand

def molecule(smiles,coordinates):
    mol=Chem.AddHs(Chem.MolFromSmiles(smiles));conf=Chem.Conformer(mol.GetNumAtoms())
    for i,p in enumerate(coordinates):conf.SetAtomPosition(i,p)
    mol.AddConformer(conf);return plf.Molecule.from_rdkit(mol)

def test_hbond_requires_donor_and_angle():
    donor=molecule('[NH4+]',[(0,0,0),(1,0,0),(-.4,.9,0),(-.4,-.5,.8),(-.4,-.5,-.8)])
    acceptor=molecule('[O-]C=O',[(2.8,0,0),(4,0,0),(4.5,1,0),(4.5,-1,0)])
    fp=plf.Fingerprint(interactions=['HBDonor'],count=True,ignore=lambda l,p:False)
    result=fp.generate(donor,acceptor,metadata=True)
    assert result
    meta=next(iter(result.values()))['HBDonor'][0]
    assert meta['distance']==pytest.approx(2.8)
    assert any(float(v)>170 for k,v in meta.items() if 'angle' in k)
    # Same heavy atom distance, but H atoms all point away from the acceptor.
    donor_bad=molecule('[NH4+]',[(0,0,0),(-1,0,0),(-.4,.9,0),(-.4,-.5,.8),(-.4,-.5,-.8)])
    assert not fp.generate(donor_bad,acceptor,metadata=True)
    methane=molecule('C',[(0,0,0),(1,0,0),(-.4,.9,0),(-.4,-.5,.8),(-.4,-.5,-.8)])
    assert not fp.generate(methane,acceptor,metadata=True)

def test_ionic_contacts():
    donor=molecule('[NH4+]',[(0,0,0),(1,0,0),(-.4,.9,0),(-.4,-.5,.8),(-.4,-.5,-.8)])
    acceptor=molecule('[O-]C=O',[(2.8,0,0),(4,0,0),(4.5,1,0),(4.5,-1,0)])
    assert plf.Fingerprint(interactions=['Cationic'],ignore=lambda l,p:False).generate(donor,acceptor,metadata=True)


def test_neutral_and_polar_atoms_do_not_become_ionic_or_hydrophobic_by_distance():
    cation=molecule('[NH4+]',[(0,0,0),(1,0,0),(-.4,.9,0),(-.4,-.5,.8),(-.4,-.5,-.8)])
    neutral=molecule('O',[(2.8,0,0),(3.5,.7,0),(3.5,-.7,0)])
    assert not plf.Fingerprint(interactions=['Cationic'],ignore=lambda l,p:False).generate(cation,neutral,metadata=True)
    assert not plf.Fingerprint(interactions=['Hydrophobic'],ignore=lambda l,p:False).generate(cation,neutral,metadata=True)

def aromatic_ring(z=0,vertical=False):
    points=[]
    for radius in [1.4,2.4]:
        for i in range(6):
            a=i*math.pi/3
            points.append((radius*math.cos(a),z if vertical else radius*math.sin(a),radius*math.sin(a) if vertical else z))
    return molecule('c1ccccc1',points)

def test_aromatic_parallel_and_t_shaped():
    fp=plf.Fingerprint(interactions=['PiStacking'],count=True,ignore=lambda l,p:False)
    assert fp.generate(aromatic_ring(),aromatic_ring(3.5),metadata=True)
    # Explicit edge-to-face criterion is exercised separately via ProLIF type.
    assert not fp.generate(aromatic_ring(),aromatic_ring(12),metadata=True)
    edge=plf.Fingerprint(interactions=['EdgeToFace'],count=True,ignore=lambda l,p:False)
    assert edge.generate(aromatic_ring(),aromatic_ring(3.5,vertical=True),metadata=True)

def test_hydrophobic_vdw_and_pi_cation_are_chemically_typed():
    a=aromatic_ring()
    b=aromatic_ring(3.3)
    fp=plf.Fingerprint(interactions=['Hydrophobic','VdWContact'],count=True,ignore=lambda l,p:False)
    result=next(iter(fp.generate(a,b,metadata=True).values()))
    assert 'Hydrophobic' in result and 'VdWContact' in result
    cation=molecule('[NH4+]',[(0,0,3.5),(1,0,3.5),(-.4,.9,3.5),(-.4,-.5,4.3),(-.4,-.5,2.7)])
    assert plf.Fingerprint(interactions=['PiCation'],ignore=lambda l,p:False).generate(aromatic_ring(),cation,metadata=True)

def test_bad_inputs(tmp_path):
    empty=tmp_path/'empty.pdb';empty.write_text('')
    with pytest.raises(ValueError):inspect(empty)
    empty.write_text('this is not a structural file')
    with pytest.raises(ValueError):inspect(empty)
    with pytest.raises(ValueError):prepare_ligand('not a SMILES',tmp_path,1)
    with pytest.raises(ValueError):validate_box([0,0,0],[0,20,20])
    with pytest.raises(ValueError):validate_box([float('nan'),0,0],[20,20,20])
    with pytest.raises(FileNotFoundError):Runner().run([str(tmp_path/'missing.exe')],tmp_path/'error.log')

def test_cancellation():
    r=Runner();r.cancelled.set()
    with pytest.raises(Cancelled):r.checkpoint()

def test_unicode_molecule_paths_preserve_identity_and_properties(tmp_path):
    from scientific.molecules import read_sdf,write_sdf
    folder=tmp_path/'مسارات 蛋白 paths';folder.mkdir()
    path=folder/'リガンド مركب.sdf'
    mol=Chem.AddHs(Chem.MolFromSmiles('C[C@H](O)C(=O)O'))
    from rdkit.Chem import AllChem
    assert AllChem.EmbedMolecule(mol,randomSeed=29)==0
    mol.SetProp('source','verified source record')
    write_sdf(path,mol)
    restored=read_sdf(path,removeHs=False)[0]
    assert restored is not None
    assert Chem.MolToSmiles(restored)==Chem.MolToSmiles(mol)
    assert restored.GetProp('source')=='verified source record'
    assert np.allclose(restored.GetConformer().GetPositions(),mol.GetConformer().GetPositions(),atol=0.0001)

def test_preparation_preserves_labels_and_heavy_geometry(tmp_path):
    pdb,pdbqt,meta=prepare('tests/fixtures/3PTB.pdb',tmp_path,remove_heterogens=['BEN A:1'])
    from Bio.PDB import PDBParser
    a=PDBParser(QUIET=True).get_structure('a','tests/fixtures/3PTB.pdb');b=PDBParser(QUIET=True).get_structure('b',str(pdb))
    def atommap(s):return {(r.resname,r.parent.id,r.id,a.name):a.coord for r in s.get_residues() for a in r if a.element!='H' and r.id[0]!='W' and r.resname!='BEN'}
    aa=atommap(a);bb=atommap(b);assert aa.keys()==bb.keys()
    assert max(np.linalg.norm(aa[k]-bb[k]) for k in aa)==0
    assert 'CA A:480' in meta['metals']
    assert pdbqt.stat().st_size>0
    assert Chem.SDMolSupplier(str(pdb.with_suffix('.sdf')),removeHs=False)[0] is not None

def test_coordination_requires_complete_chemical_geometry():
    from scientific.interactions import coordination_geometry
    def make(smiles,xyz):
        m=Chem.MolFromSmiles(smiles);c=Chem.Conformer(m.GetNumAtoms())
        for i,p in enumerate(xyz):c.SetAtomPosition(i,p)
        m.AddConformer(c);return m
    directions=np.array([(1,1,1),(1,-1,-1),(-1,1,-1),(-1,-1,1)])/np.sqrt(3)*2.1
    p=make('[Zn+2].[O-].[O-].[O-]',[(0,0,0),*directions[:3]])
    l=make('[O-]',[directions[3]])
    assert 'tetrahedral' in coordination_geometry(p,l,[0],[0])
    bad=make('[O-]',[(10,10,10)])
    assert coordination_geometry(p,bad,[0],[0]) is None

