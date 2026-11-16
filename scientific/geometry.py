"""Atom-indexed geometry shared by ProLIF, validation and the 3D renderer."""
import json,hashlib
from functools import lru_cache
from pathlib import Path
import numpy as np
from rdkit import Chem
from scientific.molecules import read_sdf

GEOMETRY_VERSION = 'atom-anchors-3'

def load_receptor(path):
    path=Path(path).resolve()
    # Content hashes invalidate cached validation even when a file is replaced
    # with the same name and size. Return a copy so callers cannot mutate cache.
    return Chem.Mol(_validated_receptor(str(path),hashlib.sha256(path.read_bytes()).hexdigest(),hashlib.sha256(path.with_suffix('.sdf').read_bytes()).hexdigest()))

@lru_cache(maxsize=3)
def _validated_receptor(path,pdb_hash,graph_hash):
    path=Path(path)
    mols=read_sdf(path.with_suffix('.sdf'),removeHs=False)
    if not mols or mols[0] is None:raise ValueError('Prepared receptor chemistry graph is required')
    mol=mols[0]
    labels=[l for l in path.read_text(encoding='utf-8').splitlines() if l.startswith(('ATOM  ','HETATM'))]
    if len(labels)!=mol.GetNumAtoms():raise ValueError('Receptor graph/atom-label count mismatch')
    for atom,line in zip(mol.GetAtoms(),labels):
        xyz=np.array([float(line[k:k+8]) for k in (30,38,46)])
        if not np.allclose(xyz,mol.GetConformer().GetAtomPosition(atom.GetIdx()),atol=.002,rtol=0):
            raise ValueError(f'Receptor coordinate/atom-order mismatch at atom {atom.GetIdx()}')
        symbol=line[76:78].strip()
        if symbol and symbol.upper()!=atom.GetSymbol().upper():raise ValueError('Receptor atom element mismatch')
        info=Chem.AtomPDBResidueInfo();info.SetName(line[12:16]);info.SetResidueName(line[17:20]);info.SetResidueNumber(int(line[22:26]));info.SetChainId(line[21:22]);info.SetInsertionCode(line[26:27]);info.SetSerialNumber(int(line[6:11]));info.SetIsHeteroAtom(line.startswith('HETATM'));atom.SetMonomerInfo(info)
    return mol

def indices(contact):
    data=json.loads(contact.get('metadata') or '{}')
    idx=data.get('parent_indices')
    if not idx or not idx.get('protein') or not idx.get('ligand'):
        raise ValueError('Interaction lacks global parent atom indices; reanalyze this pose')
    return data,list(map(int,idx['protein'])),list(map(int,idx['ligand']))

def anchors(protein,ligand,kind,pa,la):
    # H bond metadata additionally includes donor H. The measured distance is
    # donor–acceptor, never the centroid of donor and H.
    pi=pa if kind in {'FaceToFace','EdgeToFace','CationPi'} else pa[:1]
    li=la if kind in {'FaceToFace','EdgeToFace','PiCation'} else la[:1]
    def center(mol,ids):
        if not ids or any(i<0 or i>=mol.GetNumAtoms() for i in ids):raise ValueError('Interaction atom index outside molecular graph')
        return np.mean([mol.GetConformer().GetAtomPosition(i) for i in ids],axis=0)
    a,b=center(protein,pi),center(ligand,li)
    return {'version':GEOMETRY_VERSION,'protein_indices':pi,'ligand_indices':li,
            'protein_anchor':a.tolist(),'ligand_anchor':b.tolist(),
            'protein_feature':'ring centroid' if len(pi)>1 else 'atom',
            'ligand_feature':'ring centroid' if len(li)>1 else 'atom',
            'distance_A':float(np.linalg.norm(a-b))}

def verify_contact(protein,ligand,contact,tolerance=.003):
    data,pa,la=indices(contact);kind=contact['interaction_type']
    geometry=anchors(protein,ligand,kind,pa,la)
    distance=contact.get('distance')
    if distance is None or not np.isfinite(distance) or abs(geometry['distance_A']-distance)>tolerance:
        raise ValueError('Interaction distance disagrees with mapped molecular coordinates')
    saved=data.get('geometry',{})
    for key in ['protein_anchor','ligand_anchor']:
        if key in saved and not np.allclose(saved[key],geometry[key],atol=tolerance,rtol=0):
            raise ValueError('Interaction anchor disagrees with current molecular coordinates')
    pinfo=protein.GetAtomWithIdx(pa[0]).GetPDBResidueInfo()
    if pinfo:
        if pinfo.GetChainId().strip()!=(contact.get('chain') or '').strip() or str(pinfo.GetResidueNumber())!=str(contact['residue_number']):
            raise ValueError('Interaction residue/chain mapping mismatch')
        if data.get('insertion_code',pinfo.GetInsertionCode().strip())!=pinfo.GetInsertionCode().strip():raise ValueError('Interaction insertion-code mismatch')
        if contact.get('protein_atom') and ','.join(protein.GetAtomWithIdx(i).GetPDBResidueInfo().GetName().strip() for i in pa)!=contact['protein_atom']:
            raise ValueError('Interaction atom labels disagree with mapped atoms')
    if kind in {'HBDonor','HBAcceptor'}:
        donor,di,acceptor,ai=(ligand,la,protein,pa) if kind=='HBDonor' else (protein,pa,ligand,la)
        if len(di)<2 or donor.GetAtomWithIdx(di[1]).GetAtomicNum()!=1:raise ValueError('Hydrogen-bond mapping lacks explicit donor hydrogen')
        d,h=np.array(donor.GetConformer().GetAtomPosition(di[0])),np.array(donor.GetConformer().GetAtomPosition(di[1]));a=np.array(acceptor.GetConformer().GetAtomPosition(ai[0]))
        u,v=d-h,a-h;angle=float(np.degrees(np.arccos(np.clip(np.dot(u,v)/(np.linalg.norm(u)*np.linalg.norm(v)),-1,1))))
        if abs(angle-data['DHA_angle'])>.05:raise ValueError('Hydrogen-bond angle disagrees with atom mapping')
    def angle_degrees(a,b):
        length=np.linalg.norm(a)*np.linalg.norm(b)
        if length<1e-10:raise ValueError('Degenerate interaction geometry')
        return float(np.degrees(np.arccos(np.clip(np.dot(a,b)/length,-1,1))))
    def ring_normal(mol,ids):
        xyz=mol.GetConformer().GetPositions()[ids];center=xyz.mean(axis=0)
        if len(ids)<3:raise ValueError('Aromatic feature lacks ring atoms')
        return center,np.cross(xyz[0]-center,xyz[1]-center)
    if kind in {'FaceToFace','EdgeToFace'}:
        pc,pn=ring_normal(protein,pa);lc,ln=ring_normal(ligand,la);plane=angle_degrees(ln,pn)
        if abs(plane-data['plane_angle'])>.05:raise ValueError('Aromatic plane angle disagrees with mapped ring atoms')
        candidates=[angle_degrees(ln,pc-lc),angle_degrees(pn,lc-pc)]
        if min(abs(v-data['normal_to_centroid_angle']) for v in candidates)>.05:raise ValueError('Aromatic orientation angle disagrees with mapped ring atoms')
    if kind in {'CationPi','PiCation'}:
        ring,ri,cation,ci=(protein,pa,ligand,la) if kind=='CationPi' else (ligand,la,protein,pa)
        center,normal=ring_normal(ring,ri);point=cation.GetConformer().GetPositions()[ci[0]];angle=angle_degrees(normal,point-center)
        if abs(angle-data['angle'])>.05:raise ValueError('Pi-cation angle disagrees with mapped feature atoms')
    return geometry

def viewer_contacts(receptor,ligand,contacts):
    protein=load_receptor(receptor);mol=read_sdf(ligand,removeHs=False)[0]
    result=[]
    for contact in contacts:
        geometry=verify_contact(protein,mol,contact)
        data,pa,la=indices(contact);info=protein.GetAtomWithIdx(pa[0]).GetPDBResidueInfo()
        result.append({**contact,'geometry':geometry,'protein_indices':pa,'ligand_indices':la,
                       'insertion_code':info.GetInsertionCode().strip(),'residue_name':info.GetResidueName().strip()})
    return result
