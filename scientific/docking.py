import json
import math
import os
import shutil
import tempfile
from pathlib import Path
from rdkit import Chem
from scientific.runtime import smina, sha
from scientific.pockets import validate_box
from scientific.molecules import read_sdf,write_sdf

def dock(receptor,ligand_sdf,center,size,settings,folder,runner):
    validate_box(center,size)
    for field in ["exhaustiveness","num_modes","cpu"]:
        if int(settings[field])<1: raise ValueError(f"{field} must be positive")
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    output=folder/"docked.sdf"
    # The legacy native engine uses narrow-character file I/O. Stage chemistry
    # files in an ASCII temporary path, then copy through Python's Unicode I/O.
    staging=tempfile.TemporaryDirectory(prefix='nile_dock_')
    stage=Path(staging.name)
    if not str(stage).isascii() and os.name=='nt':
        import ctypes
        buffer=ctypes.create_unicode_buffer(32768)
        if ctypes.windll.kernel32.GetShortPathNameW(str(stage),buffer,len(buffer)):stage=Path(buffer.value)
    if not str(stage).isascii():staging.cleanup();raise ValueError('Smina requires an ASCII staging directory; configure Windows TEMP to a writable ASCII path')
    shutil.copy2(receptor,stage/'receptor.pdbqt');shutil.copy2(ligand_sdf,stage/'ligand.sdf')
    args=[smina(),"--receptor",stage/'receptor.pdbqt',"--ligand",stage/'ligand.sdf',"--out",stage/'docked.sdf',"--log",stage/'smina.log']
    for key in ["exhaustiveness","num_modes","seed","cpu","scoring"]: args.extend(["--"+key,str(settings[key])])
    for axis,c,v in zip("xyz",center,size):args.extend(["--center_"+axis,str(c),"--size_"+axis,str(v)])
    try:
        elapsed=runner.run(args,folder/"process.log",timeout=7200)
    finally:
        for name in ['smina.log','docked.sdf']:
            if (stage/name).exists():shutil.copy2(stage/name,folder/name)
        staging.cleanup()
    original=read_sdf(ligand_sdf,removeHs=True)[0]
    if original is None: raise ValueError("Prepared ligand template is invalid")
    results=[]
    for rank,raw in enumerate(read_sdf(output,removeHs=False),1):
        if raw is None:raise ValueError("Smina returned an invalid pose")
        hp=Chem.RemoveHsParameters();hp.removeDefiningBondStereo=True
        heavy=Chem.RemoveHs(raw,hp)
        if Chem.MolToSmiles(heavy,isomericSmiles=False)!=Chem.MolToSmiles(original,isomericSmiles=False):
            raise ValueError("Docked ligand identity differs from prepared template")
        mapping=heavy.GetSubstructMatch(original,useChirality=True)
        if len(mapping)!=original.GetNumAtoms():raise ValueError("Cannot map pose atom identities to original bond-order template")
        pose=Chem.Mol(original);conf=Chem.Conformer(pose.GetNumAtoms())
        for i,j in enumerate(mapping):conf.SetAtomPosition(i,heavy.GetConformer().GetAtomPosition(j))
        pose.RemoveAllConformers();pose.AddConformer(conf)
        pose=Chem.AddHs(pose,addCoords=True)
        raw_heavy=[a.GetIdx() for a in raw.GetAtoms() if a.GetAtomicNum()!=1]
        # Preserve Smina's donor-H coordinates rather than inventing their angles
        # after docking. Remaining nonpolar H coordinates use RDKit geometry.
        for i,j in enumerate(mapping):
            ra=raw.GetAtomWithIdx(raw_heavy[j]);pa=pose.GetAtomWithIdx(i)
            rh=[n.GetIdx() for n in ra.GetNeighbors() if n.GetAtomicNum()==1]
            ph=[n.GetIdx() for n in pa.GetNeighbors() if n.GetAtomicNum()==1]
            if len(rh)>len(ph):raise ValueError('Docked hydrogen count exceeds template chemistry')
            for rhi,phi in zip(rh,ph):pose.GetConformer().SetAtomPosition(phi,raw.GetConformer().GetAtomPosition(rhi))
        score=None
        for prop in ["minimizedAffinity","minimizedAffinity ","affinity"]:
            if raw.HasProp(prop):score=float(raw.GetProp(prop));break
        if score is None or not math.isfinite(score):raise ValueError("Smina output does not contain a finite minimizedAffinity score")
        pose.SetDoubleProp("Smina_score_kcal_mol",score)
        path=folder/f"pose_{rank}.sdf"
        write_sdf(path,pose)
        results.append({"rank":rank,"score":score,"sdf_path":str(path)})
    if not results:raise ValueError("Smina returned no valid docking poses")
    (folder/"run.json").write_text(json.dumps({"arguments":list(map(str,args)),"settings":settings,"receptor_sha256":sha(receptor),"ligand_sha256":sha(ligand_sdf),"output_sha256":sha(output),"elapsed_seconds":elapsed},indent=2),encoding="utf-8")
    return results,elapsed

def complex_pdb(receptor,ligand,output):
    mol=read_sdf(ligand,removeHs=False)[0]
    if mol is None:raise ValueError("Invalid ligand for reconstruction")
    existing=Path(receptor).read_text(encoding="utf-8").splitlines()
    protein=[line for line in existing if line.startswith(("ATOM  ","HETATM","TER"))]
    serials=[int(l[6:11]) for l in protein if l.startswith(("ATOM  ","HETATM"))]
    serial=max(serials,default=0)
    if serial+mol.GetNumAtoms()>99999:raise ValueError("Complex exceeds PDB serial limit; mmCIF export needed")
    # Choose an unused chain and retain original receptor residue/atom labels.
    used={l[21:22] for l in protein};chain=next((x for x in "ZYLXWVUTSRQPONM" if x not in used),None)
    if chain is None:raise ValueError("No unambiguous PDB ligand chain available")
    lines=[]
    for i,a in enumerate(mol.GetAtoms()):
        pos=mol.GetConformer().GetAtomPosition(i);name=(a.GetSymbol()+str(i+1))[:4]
        lines.append(f"HETATM{serial+i+1:5d} {name:<4s} LIG {chain}   1    {pos.x:8.3f}{pos.y:8.3f}{pos.z:8.3f}  1.00  0.00          {a.GetSymbol():>2s}")
    bonds=[]
    for b in mol.GetBonds():bonds.append(f"CONECT{serial+b.GetBeginAtomIdx()+1:5d}{serial+b.GetEndAtomIdx()+1:5d}")
    Path(output).write_text("\n".join(protein+["TER"]+lines+bonds+["END",""]),encoding="utf-8")
    return chain

