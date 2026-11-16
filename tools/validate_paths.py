import json,shutil
from pathlib import Path
from Bio.PDB import PDBParser,MMCIFIO
from scientific.proteins import inspect,prepare
from scientific.pockets import predict
from scientific.docking import dock
from scientific.pipeline import DEFAULTS
from scientific.runtime import Runner

def main():
    folder=Path('data/validation/مسارات 蛋白 paths').resolve()/('long_output_'+'x'*80)/('long_output_'+'y'*80);folder.mkdir(parents=True,exist_ok=True)
    pdb=folder/'بروتين 蛋白.pdb';shutil.copy2('tests/fixtures/3PTB.pdb',pdb)
    cif=folder/'بروتين 蛋白.cif';io=MMCIFIO();io.set_structure(PDBParser(QUIET=True).get_structure('3PTB',str(pdb)));io.save(str(cif))
    meta=inspect(cif);assert meta['chains']==1 and meta['residues']==223
    receptor,pdbqt,preparation=prepare(cif,folder/'prepared receptor',remove_heterogens=['BEN A:1'])
    ps=predict(receptor,folder/'predicted pockets',Runner(),1)
    ligand=folder/'リガンド مركب.sdf';shutil.copy2('data/compound_library/compound_9.sdf',ligand)
    poses,elapsed=dock(pdbqt,ligand,ps[0]['center'],ps[0]['size'],{**DEFAULTS,'cpu':1,'exhaustiveness':1,'num_modes':1},folder/'docking results',Runner())
    report={'unicode_and_space_paths':True,'mmcif_import_and_preparation':True,'p2rank_completed':True,'smina_completed':True,'score':poses[0]['score'],'elapsed_seconds':elapsed,'folder':str(folder),'example_result_path_characters':len(str(poses[0]['sdf_path']))}
    Path('data/validation/path_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=True))

if __name__=='__main__':main()
