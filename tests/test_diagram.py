import json
import pytest
from rdkit import Chem
from scientific.molecules import write_sdf
from visualization.interaction_diagram import diagram

@pytest.mark.parametrize('smiles,n,classes',[('CCO',2,1),('c1ccccc1',12,1),('CC(C)(C)c1cc(O)c(C(C)C)cc1O',26,1),('c1ccccc1',30,4)])
def test_atom_anchored_vector_diagram_and_nonoverlap(tmp_path,smiles,n,classes):
    mol=Chem.MolFromSmiles(smiles);path=tmp_path/'ligand.sdf';write_sdf(path,mol)
    contacts=[{'residue':f'ALA{i}.A','interaction_type':['Hydrophobic','HBAcceptor','VdWContact','FaceToFace'][j],'distance':2.8+i/100,'metadata':json.dumps({'parent_indices':{'ligand':[i%mol.GetNumAtoms()]}})} for i in range(n) for j in range(classes)]
    svg,layout=diagram(path,contacts)
    assert '<image' not in svg and len(layout['anchors'])==n*classes
    assert [a['distance'] for a in layout['anchors']]==[next(c['distance'] for c in contacts if c['residue']==a['residue']) for a in layout['anchors']]
    for anchor in layout['anchors']:assert anchor['ligand_atom_indices']==[int(anchor['residue'][3:].split('.')[0])%mol.GetNumAtoms()]
    boxes=layout['residue_boxes']
    for i,(x,y,w,h) in enumerate(boxes):
        assert x>=0 and y>=45 and x+w<=layout['width'] and y+h<=layout['height']-45
        for xx,yy,ww,hh in boxes[i+1:]:assert x+w<=xx or xx+ww<=x or y+h<=yy or yy+hh<=y
