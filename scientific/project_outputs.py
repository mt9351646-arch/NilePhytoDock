"""Publish persistent, organized files alongside the actual calculation tree."""
import json,shutil
from pathlib import Path
from database.store import rows
from app.outputs import FOLDERS

def publish(db,pid):
    from scientific.runtime import checkpoint
    checkpoint();root=Path(db.execute('SELECT folder FROM analysis_projects WHERE id=?',(pid,)).fetchone()[0])
    for part in FOLDERS:(root/part).mkdir(parents=True,exist_ok=True)
    records=rows(db,'SELECT p.*,r.protein_id,r.compound_id,r.pocket_id,r.folder FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id WHERE r.project_id=?',(pid,))
    manifest=[]
    for p in records:
        checkpoint()
        prefix=f"protein_{p['protein_id']}_compound_{p['compound_id']}_pocket_{p['pocket_id']}_pose_{p['rank']}"
        for field,part in [('sdf_path','Docked_Ligands'),('complex_path','Complexes')]:
            source=Path(p[field]);target=root/part/(prefix+source.suffix);shutil.copy2(source,target);manifest.append({'pose_id':p['id'],'kind':part,'file':str(target.relative_to(root)),'original':str(source)})
        contacts=rows(db,'SELECT * FROM molecular_interactions WHERE pose_id=?',(p['id'],));(root/'Interactions'/(prefix+'.json')).write_text(json.dumps(contacts,ensure_ascii=False,indent=2),encoding='utf-8')
        for image in Path(p['folder']).glob(f"interactions_pose_{p['rank']}.*"):
            shutil.copy2(image,root/'2D_Figures'/(prefix+''.join(image.suffixes)))
    for r in rows(db,'SELECT id,folder FROM docking_runs WHERE project_id=?',(pid,)):
        for source in Path(r['folder']).glob('*.log'):shutil.copy2(source,root/'Logs'/(f"run_{r['id']}_"+source.name))
    from reporting.export import export_all
    export_all(db,pid,root/'Reports');checkpoint()
    for source in (root/'Reports').glob('*ranking.csv'):shutil.copy2(source,root/'Rankings'/source.name)
    for source in (root/'Reports'/'figures').glob('*heatmap.*'):shutil.copy2(source,root/'Heatmaps'/source.name)
    (root/'Project_Data'/'files.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    import sqlite3
    snapshot=sqlite3.connect(root/'Project_Data'/'project.nile.sqlite');db.backup(snapshot);snapshot.close()
    return root
