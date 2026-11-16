import hashlib
import json
import shutil
import traceback
from pathlib import Path
from database.store import rows,insert,log
from scientific.runtime import Runner,Cancelled,sha,smina
from app.paths import resource

DEFAULTS={"exhaustiveness":8,"num_modes":5,"seed":20261029,"cpu":2,"scoring":"vina","box_size":[22,22,22],"pocket_mode":"Automatic","top_n":1,"pocket_rank":1,"keep_waters":False,"remove_heterogens":[],"ph":7.4}
DEFAULTS.update(pocket_margin=6.0,geometric_boxes=True,pocket_selections={})

def ligand_path(path):
    p=Path(path)
    # Seed database stores relocatable paths. User-maintained libraries can be absolute.
    return p if p.is_absolute() else resource(*p.parts)

def create_project(db,name,files,profiles,settings,folder):
    from scientific import proteins
    if not files:raise ValueError("Import at least one protein")
    if not profiles:raise ValueError("Select at least one oil profile")
    settings={**DEFAULTS,**settings,"profiles":profiles}
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    pid=insert(db,"analysis_projects",name=name,status="queued",settings=json.dumps(settings),folder=str(folder))
    for i,f in enumerate(files):
        meta=proteins.inspect(f)
        target_folder=folder/'Proteins'/f"target_{i+1}";target_folder.mkdir(parents=True,exist_ok=True)
        original=target_folder/("original"+Path(f).suffix.lower());shutil.copy2(f,original)
        insert(db,"protein_targets",project_id=pid,name=Path(f).stem,original_path=str(original),sha256=sha(original),metadata=json.dumps(meta),status="imported")
    db.commit();return pid

def run_project(db,pid,runner=None,progress=lambda text,done,total:None):
    from scientific import proteins,pockets,docking,interactions
    runner=runner or Runner()
    project=dict(db.execute("SELECT * FROM analysis_projects WHERE id=?",(pid,)).fetchone());settings=json.loads(project["settings"])
    placeholders=','.join('?' for _ in settings['profiles'])
    ligands=rows(db,f"SELECT DISTINCT c.id,c.name,s.sdf_path FROM chemical_compounds c JOIN compound_structures s ON s.compound_id=c.id JOIN profile_compounds pc ON pc.compound_id=c.id WHERE pc.profile_id IN ({placeholders}) AND pc.docking_eligible=1 AND (pc.percentage>0 OR pc.reported_value>0 OR pc.value_status IN ('presence_only','trace')) AND s.status='ready'",settings['profiles'])
    if not ligands:raise ValueError("Selected profiles have no locally prepared, identity-verified ligands. Open Settings to maintain the library.")
    version=__import__('subprocess').check_output([str(smina()),'--version'],text=True,creationflags=__import__('subprocess').CREATE_NO_WINDOW).strip()
    db.execute("UPDATE analysis_projects SET status='running' WHERE id=?",(pid,));db.commit()
    targets=rows(db,"SELECT * FROM protein_targets WHERE project_id=?",(pid,));done=0;total=len(ligands)*len(targets)*max(1,settings['top_n'] if settings['pocket_mode']=='Top N' else 1)
    failures=0;calculated=0;reused=0;resumed=0
    try:
        for target in targets:
            runner.checkpoint();tid=target['id'];folder=Path(project['folder'])/'Prepared_Proteins'/f"protein_{tid}";folder.mkdir(parents=True,exist_ok=True)
            try:
                progress(f"Preparing {target['name']}",done,total)
                pdb,pdbqt,meta=proteins.prepare(target['original_path'],folder,settings['keep_waters'],settings.get('remove_heterogens',[]),settings['ph'])
                db.execute("UPDATE protein_targets SET prepared_path=?,pdbqt_path=?,metadata=?,status='prepared',error=NULL WHERE id=?",(str(pdb),str(pdbqt),json.dumps(meta),tid));db.commit()
                mode=settings['pocket_mode']
                if mode=='Custom box':
                    pocket_data=[dict(rank=1,score=None,center=settings['center'],size=settings['box_size'],residues='',method='User custom box',provenance='User-defined')]
                elif mode=='Reference ligand':
                    center,size=proteins.reference_box(target['original_path'],settings['reference_ligand'])
                    pocket_data=[dict(rank=1,score=None,center=center,size=size,residues=settings['reference_ligand'],method='Experimental reference ligand box',provenance=target['original_path'])]
                else:
                    progress(f"P2Rank: {target['name']}",done,total)
                    pocket_data=pockets.predict(pdb,Path(project['folder'])/'P2Rank'/f'protein_{tid}',runner,settings['cpu'],None if settings.get('geometric_boxes') else settings['box_size'],settings.get('pocket_margin',6))
                    override=settings.get('pocket_selections',{}).get(target['sha256'])
                    if override and mode in ['Automatic','Manual pocket']:
                        selected_rank=override['rank']
                        match=next((p for p in pocket_data if p['rank']==selected_rank),None)
                        if match is None or max(abs(a-b) for a,b in zip(match['center'],override['center']))>0.001:raise ValueError('Selected pocket differs from current prepared receptor predictions; predict again')
                        match['size']=override['size'];pockets.validate_box(match['center'],match['size'])
                for pocket in pocket_data:
                    existing=db.execute("SELECT id FROM predicted_pockets WHERE protein_id=? AND rank=? AND method=?",(tid,pocket['rank'],pocket['method'])).fetchone()
                    if existing: pocket['id']=existing[0]
                    else:pocket['id']=insert(db,'predicted_pockets',protein_id=tid,**{k:json.dumps(v) if k in ['center','size'] else v for k,v in pocket.items() if k!='id'})
                db.commit()
                if mode=='Top N': selected=pocket_data[:settings['top_n']]
                elif mode=='Manual pocket' or (mode=='Automatic' and settings.get('pocket_selections',{}).get(target['sha256'])):
                    rank=settings.get('pocket_selections',{}).get(target['sha256'],{}).get('rank',settings['pocket_rank'])
                    selected=[p for p in pocket_data if p['rank']==rank]
                    if not selected:raise ValueError('Requested P2Rank pocket rank is unavailable')
                else:selected=pocket_data[:1]
                for pocket in selected:
                    for ligand in ligands:
                        runner.checkpoint();progress(f"{target['name']} · pocket {pocket['rank']} · {ligand['name']}",done,total)
                        sdf=ligand_path(ligand['sdf_path'])
                        scientific_settings={k:settings[k] for k in ['exhaustiveness','num_modes','seed','cpu','scoring']}
                        core={'receptor':sha(pdbqt),'receptor_graph':sha(Path(pdb).with_suffix('.sdf')),'receptor_labels':sha(pdb),'ligand':sha(sdf),'settings':scientific_settings,'center':pocket['center'],'size':pocket['size'],'version':version,'engine_hash':sha(smina()),'interaction_engine':__import__('prolif').__version__,'interaction_types':interactions.TYPES,'geometry_version':interactions.GEOMETRY_VERSION,'interaction_parameters':interactions.detection_parameters()}
                        science_key=hashlib.sha256(json.dumps(core,sort_keys=True).encode()).hexdigest()
                        key=f'{pid}:{tid}:{pocket["id"]}:{ligand["id"]}:{science_key}'
                        prior=db.execute('SELECT * FROM docking_runs WHERE cache_key=?',(key,)).fetchone()
                        if prior and prior['status'] in ['complete','interaction_review']:
                            paths=rows(db,'SELECT sdf_path,complex_path FROM docking_poses WHERE run_id=?',(prior['id'],))
                            manifest=Path(prior['folder'])/'cache_manifest.json'
                            if paths and manifest.exists():
                                saved=json.loads(manifest.read_text())
                                if all((manifest.parent/p).exists() and sha(manifest.parent/p)==h for p,h in saved.items()):
                                    done+=1;resumed+=1;progress(f"Resume: retained verified completed result for {ligand['name']}",done,total);continue
                        runfolder=Path(project['folder'])/'Docking'/f"protein_{tid}"/f"pocket_{pocket['rank']}"/f"compound_{ligand['id']}";runfolder.mkdir(parents=True,exist_ok=True)
                        if prior:
                            rid=prior['id']
                            db.execute('DELETE FROM ligand_functional_annotations WHERE pose_id IN (SELECT id FROM docking_poses WHERE run_id=?)',(rid,))
                            # Keep prior analysis evidence if calculated pose rows must be replaced.
                            archived=rows(db,'SELECT a.* FROM interaction_reanalyses a JOIN docking_poses p ON p.id=a.pose_id WHERE p.run_id=?',(rid,))
                            if archived:
                                log(db,pid,'Archived interaction reanalysis history before replacing failed/corrupt run: '+json.dumps(archived))
                                db.execute('DELETE FROM interaction_reanalyses WHERE pose_id IN (SELECT id FROM docking_poses WHERE run_id=?)',(rid,))
                            db.execute('DELETE FROM molecular_interactions WHERE pose_id IN (SELECT id FROM docking_poses WHERE run_id=?)',(rid,));db.execute('DELETE FROM docking_poses WHERE run_id=?',(rid,));db.execute("UPDATE docking_runs SET status='running',error=NULL WHERE id=?",(rid,))
                        else:rid=insert(db,'docking_runs',project_id=pid,protein_id=tid,pocket_id=pocket['id'],compound_id=ligand['id'],cache_key=key,settings=json.dumps(settings),status='running',engine_version=version,folder=str(runfolder),log_path=str(runfolder/'smina.log'))
                        db.commit()
                        try:
                            cached=db.execute('SELECT * FROM calculation_cache WHERE signature=?',(science_key,)).fetchone()
                            valid_cache=False
                            if cached and settings.get('reuse_calculations',True):
                                checks=json.loads(cached['manifest']);valid_cache=bool(checks) and all(Path(p).exists() and sha(p)==h for p,h in checks.items())
                            if valid_cache:
                                reused+=1;progress(f"Cache: reused verified result for {ligand['name']}",done,total)
                                poses=[]
                                for pose in json.loads(cached['poses']):
                                    dest=runfolder/Path(pose['sdf_path']).name;shutil.copy2(pose['sdf_path'],dest);poses.append({**pose,'sdf_path':str(dest)})
                                for name in ['smina.log','process.log','run.json','docked.sdf']:
                                    src=Path(cached['folder'])/name
                                    if src.exists():shutil.copy2(src,runfolder/name)
                                elapsed=0.;log(db,pid,f"Reused hash-verified Smina calculation for {ligand['name']}")
                            else:
                                calculated+=1;progress(f"Smina: fresh calculation for {ligand['name']} (seed {settings['seed']})",done,total)
                                poses,elapsed=docking.dock(pdbqt,sdf,pocket['center'],pocket['size'],settings,runfolder,runner)
                                checks={p['sdf_path']:sha(p['sdf_path']) for p in poses}
                                db.execute('INSERT OR REPLACE INTO calculation_cache(signature,folder,poses,manifest) VALUES (?,?,?,?)',(science_key,str(runfolder),json.dumps(poses),json.dumps(checks)));db.commit()
                            interaction_errors=[]
                            for pose in poses:
                                runner.checkpoint()
                                complex_path=runfolder/f"complex_{pose['rank']}.pdb";docking.complex_pdb(pdb,pose['sdf_path'],complex_path)
                                pose_id=insert(db,'docking_poses',run_id=rid,complex_path=str(complex_path),**pose)
                                try:
                                    for contact in interactions.analyze(pdb,pose['sdf_path'],protein_identifier=f"{tid}:{target['name']}"):insert(db,'molecular_interactions',pose_id=pose_id,**contact)
                                except Cancelled:raise
                                except Exception as e:interaction_errors.append(f"Pose {pose['rank']}: {e}")
                            status='interaction_review' if interaction_errors else 'complete'
                            db.execute('UPDATE docking_runs SET status=?,elapsed=?,error=? WHERE id=?',(status,elapsed,'; '.join(interaction_errors) or None,rid));db.commit()
                            from visualization.figures import export_pose
                            try:
                                export_pose(db,rows(db,'SELECT id FROM docking_poses WHERE run_id=? ORDER BY rank LIMIT 1',(rid,))[0]['id'],runfolder)
                            except Cancelled:raise
                            except Exception as e:
                                failures+=1;db.execute("UPDATE docking_runs SET status='figure_review',error=? WHERE id=?",(f'Figure generation failed: {e}',rid));log(db,pid,f'Figure generation failed for {ligand["name"]}: {e}','ERROR')
                            cached_files=[Path(p['sdf_path']) for p in poses]+list(runfolder.glob('complex_*.pdb'))
                            (runfolder/'cache_manifest.json').write_text(json.dumps({p.name:sha(p) for p in cached_files},indent=2),encoding='utf-8')
                        except Cancelled:
                            db.execute("UPDATE docking_runs SET status='cancelled',error='Cancelled by user' WHERE id=?",(rid,));db.commit();raise
                        except Exception as e:
                            failures+=1;db.execute("UPDATE docking_runs SET status='failed',error=? WHERE id=?",(str(e),rid));log(db,pid,f"{ligand['name']}: {e}",'ERROR')
                        done+=1;progress(f"Saved {done} calculations",done,total)
            except Cancelled:raise
            except Exception as e:
                failures+=1;db.execute("UPDATE protein_targets SET status='failed',error=? WHERE id=?",(str(e),tid));log(db,pid,f"{target['name']}: {e}",'ERROR')
        db.execute('UPDATE analysis_projects SET status=? WHERE id=?',('completed_with_errors' if failures else 'complete',pid));db.commit()
    except Cancelled:
        db.execute("UPDATE analysis_projects SET status='cancelled' WHERE id=?",(pid,));db.commit();raise
    except Exception:
        db.execute("UPDATE analysis_projects SET status='failed' WHERE id=?",(pid,));db.commit();raise
    log(db,pid,f"Screening finished: {done} jobs processed; {failures} failures")
    progress('Publishing reports and project files',done,total)
    try:
        from scientific.project_outputs import publish
        publish(db,pid)
        runner.checkpoint()
    except Cancelled:
        db.execute("UPDATE analysis_projects SET status='cancelled' WHERE id=?",(pid,));db.commit();raise
    except Exception as e:
        failures+=1;log(db,pid,'Project publication failed: '+str(e),'ERROR')
        db.execute("UPDATE analysis_projects SET status='completed_with_errors' WHERE id=?",(pid,));db.commit()
    return {'processed':done,'failures':failures,'calculated':calculated,'reused':reused,'resumed':resumed}
