"""Runs real native engines; output is evidence, never bundled screening data."""
import json
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import rdMolAlign
from database.store import connect,rows
from scientific.proteins import inspect,prepare,reference_box
from scientific.ligands import prepare as prepare_ligand
from scientific.pockets import predict
from scientific.docking import dock,complex_pdb
from scientific.interactions import analyze
from scientific.runtime import Runner,health
from scientific.pipeline import DEFAULTS

def main():
    out=Path('data/validation/science');out.mkdir(parents=True,exist_ok=True)
    print(inspect('tests/fixtures/3PTB.pdb'),flush=True)
    pdb,pdbqt,meta=prepare('tests/fixtures/3PTB.pdb',out/'3PTB',remove_heterogens=['BEN A:1'])
    runner=Runner()
    pockets=predict(pdb,out/'3PTB/pockets',runner,2)
    print('POCKETS',pockets[:3],flush=True)
    center,size=reference_box('tests/fixtures/3PTB.pdb','BEN A:1')
    experimental=Chem.SDMolSupplier('tests/fixtures/3PTB_BEN_reference.sdf',removeHs=True)[0]
    smi=Chem.MolToSmiles(experimental)
    sdf,_,props=prepare_ligand(smi,out/'benchmark_ligand','BEN')
    print('Reference ligand SMILES:',smi,flush=True)
    poses,elapsed=dock(pdbqt,sdf,center,size,{**DEFAULTS,'exhaustiveness':16,'num_modes':5},out/'redocking',runner)
    rmsds=[]
    for p in poses:
        pose=Chem.SDMolSupplier(p['sdf_path'],removeHs=True)[0]
        # CalcRMS does not align coordinates: symmetry-corrected docking-frame RMSD.
        rmsds.append({'pose':p['rank'],'score':p['score'],'rmsd_A':rdMolAlign.CalcRMS(pose,experimental)})
    print('REDOCKING',rmsds,flush=True)
    db=connect('data/nilephytodock.sqlite');ligand=rows(db,"SELECT c.id,c.name,s.sdf_path FROM chemical_compounds c JOIN compound_structures s ON s.compound_id=c.id WHERE c.name='Eucalyptol' AND s.status='ready'")
    if not ligand:raise ValueError('Verified source-library Eucalyptol is not ready')
    poses,elapsed=dock(pdbqt,ligand[0]['sdf_path'],pockets[0]['center'],pockets[0]['size'],{**DEFAULTS,'exhaustiveness':4,'num_modes':2},out/'source_library_docking',runner)
    cp=out/'source_library_docking/complex.pdb';complex_pdb(pdb,poses[0]['sdf_path'],cp)
    contacts=analyze(pdb,poses[0]['sdf_path'])
    reference_center=__import__('numpy').array(center)
    distance=float(__import__('numpy').linalg.norm(__import__('numpy').array(pockets[0]['center'])-reference_center))
    report={'engines':health(),'protein':'3PTB','preparation':meta,'reference_ligand':'BEN A:1; separate benchmark ligand, not inserted into oil library','pockets':pockets,'top_pocket_to_experimental_ligand_centroid_A':distance,'redocking':rmsds,'redocking_top_pose_meets_2A':rmsds[0]['rmsd_A']<=2,'source_library_ligand':ligand[0],'source_library_poses':poses,'interactions':contacts}
    (out/'validation_results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('INTERACTIONS',len(contacts),flush=True);print('Evidence saved',out,flush=True)

if __name__=='__main__':main()
