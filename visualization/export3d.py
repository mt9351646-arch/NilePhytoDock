"""Coordinate-preserving molecular exports and optional legitimate PyMOL."""
import json,shutil,subprocess
from pathlib import Path
from database.store import rows
from scientific.geometry import viewer_contacts
from visualization.semantics import PALETTE

def export_molecular_files(db,pose_id,folder,session=False):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    p=rows(db,'SELECT p.*,t.prepared_path FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id JOIN protein_targets t ON t.id=r.protein_id WHERE p.id=?',(pose_id,))[0]
    contacts=viewer_contacts(p['prepared_path'],p['sdf_path'],rows(db,'SELECT * FROM molecular_interactions WHERE pose_id=?',(pose_id,)))
    complex_path=folder/('pose_'+str(pose_id)+'_complex.pdb');ligand=folder/('pose_'+str(pose_id)+'_ligand.sdf');shutil.copy2(p['complex_path'],complex_path);shutil.copy2(p['sdf_path'],ligand)
    lines=[f'load "{complex_path.resolve().as_posix()}", complex','hide everything','show cartoon, polymer','show sticks, resn LIG','color cyan, resn LIG','bg_color white']
    for i,c in enumerate(contacts):
        a,b=c['geometry']['protein_anchor'],c['geometry']['ligand_anchor'];color=PALETTE.get(c['interaction_type'],'#64748b');rgb=[int(color[j:j+2],16)/255 for j in [1,3,5]]
        lines += [f'pseudoatom contact_p_{i}, pos={a}',f'pseudoatom contact_l_{i}, pos={b}',f'distance contact_{i}, contact_p_{i}, contact_l_{i}',f'set_color interaction_color_{i}, {rgb}',f'color interaction_color_{i}, contact_{i}',f'show sticks, chain {c["chain"] or "\"\""} and resi {c["residue_number"]}{c.get("insertion_code","")}']
    lines+=['hide labels, contact_*','zoom resn LIG, 8'];script=folder/'view.pml';script.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if session:
        executable=shutil.which('pymol')
        if not executable:raise RuntimeError('PyMOL is not installed; use the exported PML script on a licensed or open-source installation.')
        output=folder/'view.pse';subprocess.run([executable,'-cq',str(script),'-d','save '+str(output)],check=True,timeout=120,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if not output.exists():raise RuntimeError('PyMOL did not create the requested session')
    return [complex_path,ligand,script]
