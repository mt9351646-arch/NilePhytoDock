import csv
import json
from pathlib import Path
import numpy as np
import functools
import hashlib
import shutil
from app.paths import resource
from scientific.runtime import p2rank_args, sha,ascii_workdir
from scientific.proteins import load

@functools.lru_cache(maxsize=1)
def engine_signature():
    h=hashlib.sha256();root=resource('external_tools','p2rank')
    for part in ['bin','models','config']:
        for p in sorted((root/part).rglob('*')):
            if p.is_file():h.update(str(p.relative_to(root)).encode());h.update(bytes.fromhex(sha(p)))
    return h.hexdigest()

def predict(protein,folder,runner,threads=2,size=None,margin=6.0):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    key=sha(protein);manifest=folder/"cache.json";signature=engine_signature()
    cached=json.loads(manifest.read_text()) if manifest.exists() else {}
    predictions=list(folder.glob('*_predictions.csv'))
    valid=bool(predictions) and cached.get('sha256')==key and cached.get('engine_sha256')==signature and cached.get('output_sha256')==sha(predictions[0])
    if not valid:
        # Java 17's Windows argument decoding loses some non-ACP characters.
        # Run the unchanged P2Rank engine on identical input bytes in ASCII
        # staging; Python copies all prediction outputs to the Unicode project.
        with ascii_workdir('nile_pockets_') as stage:
            staged=stage/'prepared.pdb';shutil.copy2(protein,staged);out=stage/'predictions'
            try:runner.run(p2rank_args()+["predict","-f",staged,"-o",out,"-threads",str(threads)],folder/"p2rank.log",timeout=1200)
            finally:
                if out.exists():shutil.copytree(out,folder,dirs_exist_ok=True)
        predictions=list(folder.glob('*_predictions.csv'))
        manifest.write_text(json.dumps({"sha256":key,"engine_sha256":signature,"output_sha256":sha(predictions[0]) if predictions else None,"engine":"P2Rank 2.5.1","threads":threads}),encoding="utf-8")
    files=list(folder.glob("*_predictions.csv"))
    if len(files)!=1: raise ValueError("P2Rank did not produce one unambiguous predictions CSV")
    result=[]
    with files[0].open(encoding="utf-8-sig") as f:
        for raw in csv.DictReader(f):
            r={k.strip():v.strip() for k,v in raw.items()}
            center=[float(r['center_'+a]) for a in 'xyz']
            if not np.isfinite(center).all():raise ValueError('P2Rank pocket has non-finite coordinates')
            dimensions=list(size) if size is not None else residue_box(protein,center,r.get('residue_ids',''),margin)
            validate_box(center,dimensions)
            result.append({"rank":int(r["rank"]),"score":float(r["score"]),"center":center,"size":dimensions,"residues":r.get("residue_ids",""),"method":"P2Rank 2.5.1","provenance":str(files[0]),"name":r.get('name',''),"probability":float(r['probability']) if r.get('probability') else None})
    if not result: raise ValueError("P2Rank found no pockets; use an explicitly defined custom/reference box")
    return result

def residue_box(protein,center,residue_ids,margin=6.0):
    """Symmetric box covering associated residue heavy atoms plus a margin."""
    if not 0<=margin<=30:raise ValueError('Pocket margin must be 0–30 Å')
    structure=load(protein);wanted=set(residue_ids.split());points=[]
    for residue in structure.get_residues():
        key=f'{residue.parent.id}_{residue.id[1]}{residue.id[2].strip()}'
        if key in wanted:
            points.extend(a.coord for a in residue if a.element not in {'H','D'})
    if not points:raise ValueError('P2Rank pocket residues could not be mapped to the prepared receptor; inspect predictions or use a custom box')
    size=np.maximum(12,2*(np.max(np.abs(np.asarray(points)-np.asarray(center)),axis=0)+margin))
    if np.any(size>126):raise ValueError('Pocket residue extent exceeds supported Smina box size; select a smaller/custom region')
    return np.round(size,3).tolist()

def validate_box(center,size):
    if len(center)!=3 or len(size)!=3 or not np.isfinite(center+size).all():raise ValueError("Box coordinates must contain six finite numbers")
    if any(v<4 or v>126 for v in size): raise ValueError("Each docking box dimension must be 4–126 Å")
