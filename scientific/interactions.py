"""ProLIF atom typing and its geometric criteria; no distance-only H bonds."""
import json
from pathlib import Path
import numpy as np
from rdkit import Chem
from rdkit.Chem import Lipinski
import prolif as plf
from scientific.molecules import read_sdf
from scientific.geometry import load_receptor,anchors,verify_contact,GEOMETRY_VERSION
import inspect

TYPES=["HBDonor","HBAcceptor","Hydrophobic","VdWContact","Cationic","Anionic","FaceToFace","EdgeToFace","CationPi","PiCation","MetalDonor","MetalAcceptor"]

def detection_parameters():
    """Persist the installed engine's complete defaults, including SMARTS."""
    return {kind:{k:v.default for k,v in inspect.signature(getattr(plf.interactions,kind)).parameters.items() if v.default is not inspect.Parameter.empty} for kind in TYPES}

def coordination_geometry(protein,ligand,protein_indices,ligand_indices):
    """Conservative complete Zn(II) tetrahedral / Mg(II) octahedral check."""
    metals=[('protein',i,protein.GetAtomWithIdx(i)) for i in protein_indices if protein.GetAtomWithIdx(i).GetAtomicNum() in {12,30}]
    metals += [('ligand',i,ligand.GetAtomWithIdx(i)) for i in ligand_indices if ligand.GetAtomWithIdx(i).GetAtomicNum() in {12,30}]
    if len(metals)!=1:return None
    owner,index,metal=metals[0]
    if metal.GetFormalCharge()!=2:return None
    source=protein if owner=='protein' else ligand;center=np.array(source.GetConformer().GetAtomPosition(index));vectors=[]
    cutoff=2.6 if metal.GetAtomicNum()==30 else 2.5
    for mol in [protein,ligand]:
        acceptors={i for match in Lipinski._HAcceptors(mol) for i in match}
        for i in acceptors:
            atom=mol.GetAtomWithIdx(i)
            if atom.GetAtomicNum() not in {7,8,16}:continue
            vector=np.array(mol.GetConformer().GetAtomPosition(i))-center;distance=float(np.linalg.norm(vector))
            if 1.5<=distance<=cutoff:vectors.append(vector/distance)
    expected=4 if metal.GetAtomicNum()==30 else 6
    if len(vectors)!=expected:return None
    angles=[float(np.degrees(np.arccos(np.clip(np.dot(a,b),-1,1)))) for i,a in enumerate(vectors) for b in vectors[i+1:]]
    if expected==4 and all(abs(a-109.47)<=25 for a in angles):return 'Zn(II) tetrahedral; 4 typed donors; all angles 109.47±25 degrees'
    if expected==6 and all(min(abs(a-90),abs(a-180))<=20 for a in angles):return 'Mg(II) octahedral; 6 typed donors; angles 90/180±20 degrees'
    return None

def analyze(receptor,ligand,protein_identifier=None):
    # Preserve the preparation graph; PDB proximity bonding can create false
    # covalent bonds between spatial contacts, particularly after H addition.
    from scientific.runtime import checkpoint
    checkpoint();protein=load_receptor(receptor)
    lig=read_sdf(ligand,removeHs=False)[0]
    if lig is None:raise ValueError("Invalid ligand pose")
    lig=Chem.AddHs(lig,addCoords=True)
    fp=plf.Fingerprint(interactions=TYPES,count=True)
    # ProLIF ResidueId omits PDB insertion codes. Give every original residue a
    # unique temporary number, preserving parent indices, then restore labels
    # from the actual atom metadata. No residue 100/100A conflation.
    detection_protein=Chem.Mol(protein);residue_ids={}
    residue_charges={}
    for atom in protein.GetAtoms():
        p=atom.GetPDBResidueInfo();key=(p.GetChainId().strip(),p.GetResidueNumber(),p.GetInsertionCode().strip());residue_charges[key]=residue_charges.get(key,0)+atom.GetFormalCharge()
    for atom in detection_protein.GetAtoms():
        p=atom.GetPDBResidueInfo();key=(p.GetChainId(),p.GetResidueNumber(),p.GetInsertionCode(),p.GetResidueName())
        if key not in residue_ids:residue_ids[key]=len(residue_ids)+1
        p.SetResidueNumber(residue_ids[key])
    lm=plf.Molecule.from_rdkit(lig);pm=plf.Molecule.from_rdkit(detection_protein)
    fingerprint=fp.generate(lm,pm,metadata=True)
    result=[]
    for (lr,pr),types in fingerprint.items():
        for kind,items in types.items():
            for data in items:
                checkpoint()
                idx=data.get("parent_indices",data.get("indices",{}))
                pa=list(idx.get("protein",()));la=list(idx.get("ligand",()))
                info=protein.GetAtomWithIdx(pa[0]).GetPDBResidueInfo();chain=info.GetChainId().strip();number=info.GetResidueNumber();icode=info.GetInsertionCode().strip()
                residue=f'{info.GetResidueName().strip()}{number}{icode}'+(f'.{chain}' if chain else '')
                residue_charge=residue_charges[(chain,number,icode)]
                data={**data,'geometry':anchors(protein,lig,kind,pa,la),'residue_name':info.GetResidueName().strip(),'residue_formal_charge':residue_charge,'insertion_code':icode,'protein_identifier':protein_identifier or str(Path(receptor).resolve()),'detection_parameters':detection_parameters()[kind],'geometry_version':GEOMETRY_VERSION}
                if kind in {'MetalDonor','MetalAcceptor'}:
                    geometry=coordination_geometry(protein,lig,pa,la)
                    if geometry is None:continue
                    data={**data,'validated_coordination_geometry':geometry}
                def atom_name(i):
                    a=protein.GetAtomWithIdx(i);p=a.GetPDBResidueInfo()
                    return p.GetName().strip() if p else f"{a.GetSymbol()}{i+1}"
                angles={k:float(v) for k,v in data.items() if "angle" in k.lower() and isinstance(v,(float,int,np.floating))}
                data['reported_angle_name']=next(iter(angles),'')
                record={"residue":residue,"chain":chain,"residue_number":str(number),"interaction_type":kind,"protein_atom":",".join(atom_name(i) for i in pa),"ligand_atom":",".join(f"{lig.GetAtomWithIdx(i).GetSymbol()}{i+1}" for i in la),"distance":float(data["distance"]) if "distance" in data else None,"angle":next(iter(angles.values()),None),"method":f"ProLIF {plf.__version__}","metadata":json.dumps(data,default=lambda o:o.item() if hasattr(o,"item") else list(o))}
                verify_contact(protein,lig,record)
                result.append(record)
    return result

