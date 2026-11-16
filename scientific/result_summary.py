"""Oil-first, identity-deduplicated summaries of actual saved docking poses."""
import json,math
from collections import defaultdict
from database.store import rows

PROTOCOL_KEYS=('scoring','exhaustiveness','num_modes','seed','cpu','ph','keep_waters','remove_heterogens')
def protocol_key(settings,engine=''):
 s=json.loads(settings or '{}');return json.dumps({'engine':engine,**{k:s.get(k) for k in PROTOCOL_KEYS}},sort_keys=True)
def oil_results(db,pid,protein,pocket,protocol=None):
 project=db.execute('SELECT settings FROM analysis_projects WHERE id=?',(pid,)).fetchone()
 if not project:return {'oils':[],'protocols':[],'protein_id':protein,'pocket_id':pocket,'compounds':[]}
 selected=set(json.loads(project[0]).get('profiles',[]));members=defaultdict(list);oils={}
 for r in rows(db,'SELECT op.id AS profile_id,op.name AS profile,op.origin,op.quantitation_basis,op.oil_id,eo.name AS botanical,eo.common_name,pc.compound_id,pc.reported_value,pc.reported_unit,pc.percentage,pc.value_status,pc.docking_eligible,s.inchikey,s.status AS structure_status FROM oil_profiles op JOIN essential_oils eo ON eo.id=op.oil_id LEFT JOIN profile_compounds pc ON pc.profile_id=op.id LEFT JOIN compound_structures s ON s.compound_id=pc.compound_id'):
  if r['profile_id'] not in selected:continue
  oil=oils.setdefault(r['oil_id'],{'oil_id':r['oil_id'],'oil':r['common_name'] or r['botanical'],'botanical':r['botanical'],'profiles':{},'compounds':[]})
  oil['profiles'][r['profile_id']]={'id':r['profile_id'],'name':r['profile'],'origin':r['origin'],'basis':r['quantitation_basis']}
  present=(r['reported_value'] is not None and r['reported_value']>0) or (r['percentage'] is not None and r['percentage']>0) or r['value_status'] in ('presence_only','trace')
  if r['docking_eligible'] and r['structure_status']=='ready' and present:members[r['inchikey'] or 'compound:'+str(r['compound_id'])].append(r)
 poses=rows(db,"SELECT p.id AS pose_id,p.rank AS pose,p.score,p.sdf_path,p.complex_path,r.compound_id,r.settings,r.engine_version,r.status,t.name AS protein,t.prepared_path,k.rank AS pocket,s.inchikey,c.name AS compound FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id JOIN protein_targets t ON t.id=r.protein_id JOIN predicted_pockets k ON k.id=r.pocket_id JOIN chemical_compounds c ON c.id=r.compound_id LEFT JOIN compound_structures s ON s.compound_id=c.id WHERE r.project_id=? AND r.protein_id=? AND r.pocket_id=? AND r.status IN ('complete','interaction_review','figure_review') ORDER BY p.score,p.id",(pid,protein,pocket))
 protocols={}
 for p in poses:
  key=protocol_key(p['settings'],p['engine_version']);s=json.loads(p['settings']);protocols[key]=f"{s.get('scoring','Vina').title()} | effort {s.get('exhaustiveness','?')} | seed {s.get('seed','?')}"
 declared=json.loads(project[0])
 def preference(key):
  candidate=json.loads(key);return (tuple(candidate.get(k)!=declared.get(k,'vina' if k=='scoring' else None) for k in PROTOCOL_KEYS if k in declared or k=='scoring'),key)
 protocol=protocol if protocol in protocols else min(protocols,key=preference) if protocols else None;best={}
 for p in poses:
  identity=p['inchikey'] or 'compound:'+str(p['compound_id'])
  if protocol_key(p['settings'],p['engine_version'])!=protocol or identity not in members or p['score'] is None or not math.isfinite(p['score']):continue
  best.setdefault(identity,{**p,'identity':identity})
 for identity,p in best.items():
  by_oil=defaultdict(list)
  for m in members[identity]:by_oil[m['oil_id']].append(m)
  for oid,observations in by_oil.items():
   unique={(r['profile_id'],r['reported_value'],r['reported_unit']):r for r in observations}
   oils[oid]['compounds'].append({**p,'observations':list(unique.values())})
 for oil in oils.values():
  oil['profiles']=list(oil['profiles'].values());oil['compounds'].sort(key=lambda p:(p['score'],p['compound'].casefold(),p['identity']))
  for i,p in enumerate(oil['compounds'],1):p['rank']=i
 return {'oils':sorted(oils.values(),key=lambda o:o['oil'].casefold()),'protocols':[{'key':k,'label':v} for k,v in protocols.items()],'protocol':protocol,'protein_id':protein,'pocket_id':pocket,'compounds':list(best.values()),'method':'Best saved pose per distinct InChIKey, within one receptor, pocket and docking protocol. Membership requires a selected source observation eligible for native-molecule docking. Source percentages are never pooled or averaged.'}

def group_results(db,pid,protein,pocket,top_n=10,oil_id=None,protocol=None,include_vdw=False):
 from scientific.functional_groups import identify,participating
 from scientific.molecules import read_sdf
 from scientific.contact_store import ensure_pose_contacts
 summary=oil_results(db,pid,protein,pocket,protocol)
 pool=summary['compounds'] if oil_id is None else next((o['compounds'] for o in summary['oils'] if o['oil_id']==oil_id),[])
 ordered=sorted(pool,key=lambda p:(p['score'],p['identity']));cutoff=ordered[min(top_n,len(ordered))-1]['score'] if top_n and ordered else None
 cohort=[p for p in ordered if cutoff is None or p['score']<=cutoff];groups={};details=[];errors=[]
 memberships=defaultdict(set)
 for oil in summary['oils']:
  for p in oil['compounds']:memberships[p['identity']].add(oil['oil'])
 for p in cohort:
  mol=read_sdf(p['sdf_path'],removeHs=False)[0];annotations=identify(mol);by_name={g['name']:g['domain'] for g in annotations};direct=defaultdict(set);kinds=defaultdict(set)
  try:
   contacts=ensure_pose_contacts(db,p['pose_id']);verified=True
  except Exception as error:
   errors.append({'compound':p['compound'],'error':str(error)});contacts=[];verified=False
  for c in contacts:
   if not include_vdw and c['interaction_type']=='VdWContact':continue
   meta=json.loads(c['metadata'])
   for g in participating(mol,annotations,meta['geometry']['ligand_indices'],c['interaction_type']):
    if g['name'] not in by_name:continue
    direct[g['name']].add(c['residue']);kinds[g['name']].add(c['interaction_type'])
  for name,domain in by_name.items():
   g=groups.setdefault(name,{'group':name,'domain':domain,'identities':set(),'contacting':set(),'best_score':p['score'],'compounds':set(),'residues':set()});g['identities'].add(p['identity']);g['compounds'].add(p['compound']);g['best_score']=min(g['best_score'],p['score'])
   if direct[name]:g['contacting'].add(p['identity']);g['residues'].update(direct[name])
   details.append({'group':name,'domain':domain,'compound':p['compound'],'oils':'; '.join(sorted(memberships[p['identity']])),'score':p['score'],'direct_contact':'Yes' if direct[name] else 'No' if verified else 'Unavailable','interaction_types':'; '.join(sorted(kinds[name])),'residues':'; '.join(sorted(direct[name])),'pose_id':p['pose_id'],'identity':p['identity']})
 table=[{'group':g['group'],'domain':g['domain'],'top_compounds':len(g['identities']),'contacting_compounds':len(g['contacting']),'best_score':g['best_score'],'examples':'; '.join(sorted(g['compounds'])),'residues':'; '.join(sorted(g['residues']))} for g in groups.values()]
 table.sort(key=lambda g:(-g['top_compounds'],-g['contacting_compounds'],g['best_score'],g['group']))
 return {'groups':[g for g in table if g['domain']=='Functional group'],'features':[g for g in table if g['domain']=='Molecular feature'],'details':details,'cohort_size':len(cohort),'available_compounds':len(ordered),'cutoff':cutoff,'top_n':top_n,'contact_errors':errors,'include_vdw':include_vdw,'protocol':summary['protocol'],'method':'Distinct chemical identities among the best-scoring compounds; score ties at the cutoff are retained. Presence and direct participation are separate counts. Molecular features are separate from conventional functional groups. Group frequency is descriptive and does not establish causation or measured affinity.'}
