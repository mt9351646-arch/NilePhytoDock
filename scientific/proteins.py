import io
import json
from pathlib import Path
import numpy as np
from Bio.PDB import PDBParser, MMCIFParser, PDBIO, Select
from openbabel import openbabel as ob

METALS={"ZN","FE","MG","MN","CA","CU","CO","NI","CD"}
WATERS={"HOH","WAT","DOD"}

def load(path):
    path=Path(path)
    if not path.exists() or path.stat().st_size==0: raise ValueError("Protein file is empty or missing")
    parser=MMCIFParser(QUIET=True) if path.suffix.lower() in {".cif",".mmcif"} else PDBParser(QUIET=True)
    structure=parser.get_structure(path.stem,str(path))
    if not list(structure.get_atoms()): raise ValueError("No structural atoms found")
    return structure

def inspect(path):
    s=load(path);m=next(s.get_models());chains=list(m.get_chains());residues=list(m.get_residues())
    ligands=[f"{r.resname} {r.parent.id}:{r.id[1]}" for r in residues if r.id[0].startswith("H_") and r.resname not in METALS]
    metals=[f"{r.resname} {r.parent.id}:{r.id[1]}" for r in residues if r.resname in METALS]
    missing=[f"{r.resname} {r.parent.id}:{r.id[1]}" for r in residues if r.id[0]==" " and not all(a in r for a in ["N","CA","C","O"])]
    gaps=[]
    for chain in chains:
        seq=[r.id[1] for r in chain if r.id[0]==" "]
        gaps += [f"{chain.id}:{a}–{b}" for a,b in zip(seq,seq[1:]) if b-a>1]
    return {"chains":len(chains),"residues":sum(r.id[0]==" " for r in residues),"atoms":len(list(m.get_atoms())),"models":len(list(s.get_models())),"ligands":ligands,"metals":metals,"missing_backbone":missing,"numbering_gaps":gaps,"integrity":"Review required" if missing or gaps else "Backbone check passed (side-chain completeness not established)"}

def reference_box(path, residue_label, padding=6):
    s=load(path)
    for r in next(s.get_models()).get_residues():
        label=f"{r.resname} {r.parent.id}:{r.id[1]}"
        if label==residue_label:
            xyz=np.array([a.coord for a in r if a.element!="H"])
            if not len(xyz): break
            return ((xyz.min(0)+xyz.max(0))/2).tolist(),np.maximum(xyz.max(0)-xyz.min(0)+2*padding,12).tolist()
    raise ValueError("Reference ligand was not found in first structural model")

def prepare(path, folder, keep_waters=False, remove_heterogens=(), ph=7.4):
    """First model; highest occupancy altloc; explicit heterogen removal only."""
    s=load(path);meta=inspect(path)
    if meta["residues"]==0: raise ValueError("No protein residues found")
    if meta["missing_backbone"]: raise ValueError("Incomplete backbone requires external structural repair: "+", ".join(meta["missing_backbone"][:8]))
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    for atom in next(s.get_models()).get_atoms():
        if atom.is_disordered():
            atom.disordered_select(max(atom.child_dict,key=lambda k: atom.child_dict[k].occupancy or 0))
    class Selection(Select):
        def accept_model(self,m):return m.id==0
        def accept_residue(self,r):
            if r.resname in WATERS and not keep_waters:return False
            return f"{r.resname} {r.parent.id}:{r.id[1]}" not in remove_heterogens
        def accept_atom(self,a):
            if a.element in {'H','D'}: return False
            if a.is_disordered() and not a.is_disordered()==1:return False
            if a.is_disordered() and a.get_altloc()!=a.parent[a.name].selected_child.get_altloc():return False
            return True
    raw=folder/"selected.pdb";io_=PDBIO();io_.set_structure(s);io_.save(str(raw),Selection())
    original_lines=[l for l in raw.read_text().splitlines() if l.startswith(('ATOM  ','HETATM'))]
    original_labels={i+1:l for i,l in enumerate(original_lines)}
    # OpenBabel adds H with a pH model, assigns Gasteiger charges and AD types.
    # RDKit's residue-aware PDB reader supplies peptide bond orders. OpenBabel's
    # direct PDB reader in the tested wheel perceives some peptide C–N bonds as
    # double bonds, so pass the validated molecular graph through V3000 instead.
    from rdkit import Chem
    graph_mol=Chem.MolFromPDBBlock(raw.read_text(encoding='utf-8'),removeHs=True,sanitize=True)
    if graph_mol is None:raise ValueError('RDKit could not establish a valid receptor graph; repair structure before docking')
    for atom in graph_mol.GetAtoms():
        if atom.GetAtomicNum() in {12,20,30}:atom.SetFormalCharge(2)
    for bond in graph_mol.GetBonds():
        a,b=bond.GetBeginAtom(),bond.GetEndAtom();ai,bi=a.GetPDBResidueInfo(),b.GetPDBResidueInfo()
        if not ai or not bi:raise ValueError('Receptor atom identity missing')
        if (ai.GetChainId(),ai.GetResidueNumber(),ai.GetInsertionCode())!=(bi.GetChainId(),bi.GetResidueNumber(),bi.GetInsertionCode()):
            names={ai.GetName().strip(),bi.GetName().strip()}
            if not (names=={'C','N'} or (names=={'SG'} and ai.GetResidueName()==bi.GetResidueName()=='CYS') or a.GetAtomicNum() in {12,20,30} or b.GetAtomicNum() in {12,20,30}):
                raise ValueError('Unusual inter-residue covalent bond requires manual chemistry review')
    from scientific.protonation import assign
    graph_mol=assign(graph_mol,float(ph))
    conv=ob.OBConversion();conv.SetInAndOutFormats('mol','pdbqt');mol=ob.OBMol()
    if not conv.ReadString(mol,Chem.MolToMolBlock(graph_mol,forceV3000=True)):raise ValueError('OpenBabel rejected validated receptor graph')
    before={a.GetIdx():np.array([a.GetX(),a.GetY(),a.GetZ()]) for a in ob.OBMolAtomIter(mol) if a.GetAtomicNum()!=1}
    for atom in ob.OBMolAtomIter(mol):atom.SetImplicitHCount(0)
    charge=ob.OBChargeModel.FindType("gasteiger")
    # Gasteiger is not parameterized for isolated metal ions. Charge the organic
    # graph separately, then restore well-defined isolated divalent ions.
    metals=[a.GetIdx() for a in ob.OBMolAtomIter(mol) if a.IsMetal()]
    organic=ob.OBMol(mol)
    for i in reversed(metals):organic.DeleteAtom(organic.GetAtom(i))
    if not charge or not charge.ComputeCharges(organic): raise ValueError("Receptor organic Gasteiger charge assignment failed; review chemistry")
    organic_atoms=iter(ob.OBMolAtomIter(organic))
    for atom in ob.OBMolAtomIter(mol):
        if atom.GetIdx() in metals:
            label=original_labels.get(atom.GetIdx(),'')
            if atom.GetAtomicNum() not in {12,20,30} or label[17:20].strip() not in {'MG','CA','ZN'}:
                raise ValueError("Metal oxidation/coordination requires manual preparation; supported automatic monatomic residues: Mg2+, Ca2+, Zn2+")
            atom.SetFormalCharge(2);atom.SetPartialCharge(2.)
        else:atom.SetPartialCharge(next(organic_atoms).GetPartialCharge())
    mol.SetPartialChargesPerceived(True)
    after={a.GetIdx():np.array([a.GetX(),a.GetY(),a.GetZ()]) for a in ob.OBMolAtomIter(mol) if a.GetAtomicNum()!=1}
    displacement=max(float(np.linalg.norm(before[k]-after[k])) for k in before)
    if displacement>1e-6: raise ValueError("Unexpected receptor heavy atom displacement")
    # OpenBabel's chain perception after pH correction can rename residues.
    # Rebuild the PDB from original heavy-atom records and attach each new H to
    # the original residue of its bonded heavy atom. Never infer residue labels.
    prepared_lines=list(original_lines);hcounts={};serial=max(int(l[6:11]) for l in original_lines)
    for atom in ob.OBMolAtomIter(mol):
        if atom.GetAtomicNum()!=1:continue
        neighbors=[n for n in ob.OBAtomAtomIter(atom) if n.GetAtomicNum()!=1]
        if len(neighbors)!=1:raise ValueError('Cannot associate receptor hydrogen with one original heavy atom')
        label=original_labels[neighbors[0].GetIdx()];reskey=label[17:27];hcounts[reskey]=hcounts.get(reskey,0)+1
        name='H'+str(hcounts[reskey]);serial+=1
        prepared_lines.append(f'{label[:6]}{serial:5d} {name:<4s} {label[17:27]}   {atom.GetX():8.3f}{atom.GetY():8.3f}{atom.GetZ():8.3f}  1.00  0.00           H')
    pdb=folder/'prepared.pdb';pdb.write_text('\n'.join(prepared_lines+['END','']),encoding='utf-8')
    graph=ob.OBConversion();graph.SetOutFormat('sdf')
    graph_text=graph.WriteString(mol)
    # OB 3.1.1 writes legacy wedge flags (e.g. CFG=6) into V3000 bond records.
    # Retain the 3D coordinates and remove these invalid 2D depiction flags;
    # RDKit assigns stereochemistry from the actual 3D geometry.
    import re
    graph_text=re.sub(r' CFG=\d+','',graph_text)
    checked=Chem.MolFromMolBlock(graph_text.split('$$$$')[0],removeHs=False,sanitize=True)
    if checked is None:raise ValueError('Prepared receptor graph failed final RDKit valence validation')
    if checked.HasProp('_Name'):checked.ClearProp('_Name')
    graph_text=Chem.MolToMolBlock(checked,forceV3000=True)+'\n$$$$\n'
    (folder/'prepared.sdf').write_text(graph_text,encoding='utf-8')
    pdbqt=folder/"receptor.pdbqt";conv.AddOption("r",ob.OBConversion.OUTOPTIONS);pdbqt.write_text(conv.WriteString(mol),encoding='utf-8')
    if not pdbqt.exists() or pdbqt.stat().st_size==0: raise ValueError("Empty receptor PDBQT")
    meta.update({"preparation":"RDKit receptor graph and explicit standard-residue protonation approximation; RDKit H coordinates; OpenBabel Gasteiger charges; final RDKit valence validation; no missing residue rebuilding; no heavy atom minimization","ph":ph,"keep_waters":keep_waters,"removed_heterogens":list(remove_heterogens),"max_heavy_atom_displacement_A":displacement,"warnings":["Standard-residue pKa thresholds are a general approximation, not site-specific pKa predictions. Histidine tautomer choices, cofactors, side-chain completeness and missing residues require researcher inspection.","Cofactors and metals are retained unless explicitly selected for removal. Vina-family metal scoring is limited."]})
    (folder/"preparation.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    return pdb,pdbqt,meta

