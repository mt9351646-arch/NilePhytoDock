"""Functional-centre participation and independent molecular/site similarity."""
import json,hashlib,csv
from pathlib import Path
from collections import defaultdict
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from database.store import rows,insert
from scientific.molecules import read_sdf
from scientific.functional_groups import identify,participating,ontology,VERSION
from scientific.similarity import chemical,interaction,enrichment

def interaction_rows(db,pid,mode='Complete Interaction Table',protein=None,compound=None):
 from scientific.contact_store import ensure_project_contacts
 ensure_project_contacts(db,pid)
 data=rows(db,'SELECT i.*,r.protein_id,t.name AS protein,t.sha256 AS protein_identifier,r.pocket_id,k.rank AS binding_pocket,r.compound_id,c.name AS compound,s.inchikey,p.rank AS docking_pose,p.score AS docking_score,p.sdf_path FROM molecular_interactions i JOIN docking_poses p ON p.id=i.pose_id JOIN docking_runs r ON r.id=p.run_id JOIN protein_targets t ON t.id=r.protein_id JOIN predicted_pockets k ON k.id=r.pocket_id JOIN chemical_compounds c ON c.id=r.compound_id LEFT JOIN compound_structures s ON s.compound_id=c.id WHERE r.project_id=? ORDER BY t.id,r.compound_id,p.score,p.id,i.id',(pid,))
 best={}
 for r in rows(db,'SELECT r.protein_id,r.compound_id,s.inchikey,p.id AS pose_id FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id LEFT JOIN compound_structures s ON s.compound_id=r.compound_id WHERE r.project_id=? ORDER BY p.score,p.id',(pid,)):best.setdefault((r['protein_id'],r['inchikey'] or r['compound_id']),r['pose_id'])
 profiles=json.loads(db.execute('SELECT settings FROM analysis_projects WHERE id=?',(pid,)).fetchone()[0]).get('profiles',[])
 membership=defaultdict(list)
 for r in rows(db,'SELECT DISTINCT pc.compound_id,p.id,p.name FROM profile_compounds pc JOIN oil_profiles p ON p.id=pc.profile_id'):
  if r['id'] in profiles:membership[r['compound_id']].append(r['name'])
 annotations={};result=[]
 for r in data:
  if protein and r['protein_id']!=int(protein) or compound and r['compound_id']!=int(compound):continue
  if mode=='Best Pose Interactions' and best[(r['protein_id'],r['inchikey'] or r['compound_id'])]!=r['pose_id']:continue
  pose=r['pose_id']
  if pose not in annotations:
   path=Path(r['sdf_path']);mol=read_sdf(path,removeHs=False)[0];digest=hashlib.sha256(path.read_bytes()).hexdigest();groups=identify(mol);annotations[pose]=(mol,groups)
   db.execute('INSERT OR REPLACE INTO ligand_functional_annotations(pose_id,ontology_version,sdf_sha256,groups_json) VALUES(?,?,?,?)',(pose,VERSION,digest,json.dumps(groups)))
  mol,groups=annotations[pose];meta=json.loads(r['metadata']);indices=meta['geometry']['ligand_indices'];assigned=participating(mol,groups,indices,r['interaction_type'])
  result.append({**r,'oil_profiles':'; '.join(membership[r['compound_id']]),'residue_name':meta.get('residue_name') or r['residue'][:3],'insertion_code':meta.get('insertion_code',''),'protein_atom_indices':meta['geometry']['protein_indices'],'ligand_atom_indices':indices,'functional_groups':'; '.join(dict.fromkeys(g['name'] for g in assigned)),'functional_group_atoms':assigned,'angle_definition':meta.get('reported_angle_name',''),'distance_unit':'angstrom','angle_unit':'degree','ontology_version':VERSION})
 db.commit();return result

def analyze(db,pid,protein=None,pocket=None,limit=150,save=True,compound=None,profile=None,interaction_type=None):
 from scientific.runtime import checkpoint
 checkpoint()
 from scientific.contact_store import ensure_project_contacts
 ensure_project_contacts(db,pid)
 poses=rows(db,"SELECT p.*,r.protein_id,r.pocket_id,r.compound_id,t.name AS protein,c.name AS compound,s.inchikey FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id JOIN protein_targets t ON t.id=r.protein_id JOIN chemical_compounds c ON c.id=r.compound_id LEFT JOIN compound_structures s ON s.compound_id=c.id WHERE r.project_id=? AND r.status IN ('complete','interaction_review','figure_review') ORDER BY p.score,p.id",(pid,))
 poses=[p for p in poses if (not protein or p['protein_id']==int(protein)) and (not pocket or p['pocket_id']==int(pocket))]
 if compound:poses=[p for p in poses if p['compound_id']==int(compound)]
 if profile:
  members=rows(db,'SELECT pc.compound_id,s.inchikey FROM profile_compounds pc LEFT JOIN compound_structures s ON s.compound_id=pc.compound_id WHERE pc.profile_id=?',(profile,));allowed={r['compound_id'] for r in members};keys={r['inchikey'] for r in members if r['inchikey']};poses=[p for p in poses if p['compound_id'] in allowed or p['inchikey'] in keys]
 best={}
 for p in poses:best.setdefault((p['protein_id'],p['pocket_id'],p['inchikey'] or 'compound:'+str(p['compound_id'])),p)
 total_identities=len({k[2] for k in best});identities=sorted({k[2] for k in best})[:limit];best={k:p for k,p in best.items() if k[2] in identities};mols={};details={};frequencies=defaultdict(lambda:{'events':set(),'compounds':set(),'residues':set(),'pairs':set()});cohorts=defaultdict(list);presence=[]
 for (tid,site,identity),p in best.items():
  mol=read_sdf(p['sdf_path'],removeHs=False)[0];groups=identify(mol);mols.setdefault(identity,mol);names={g['name'] for g in groups};involved=set();fingerprint=set()
  contacts=rows(db,'SELECT * FROM molecular_interactions WHERE pose_id=?',(p['id'],))
  if interaction_type:contacts=[c for c in contacts if c['interaction_type']==interaction_type]
  for c in contacts:
   meta=json.loads(c['metadata']);fingerprint.add((c['chain'],c['residue_number'],meta.get('insertion_code',''),c['interaction_type']))
   for g in participating(mol,groups,meta['geometry']['ligand_indices'],c['interaction_type']):
    involved.add(g['name']);key=(tid,site,g['name'],c['interaction_type']);v=frequencies[key];v['events'].add(c['id']);v['compounds'].add(identity);v['residues'].add(c['residue']);v['pairs'].add((identity,c['residue']))
  if save:
   digest=hashlib.sha256(Path(p['sdf_path']).read_bytes()).hexdigest();db.execute('INSERT OR REPLACE INTO ligand_functional_annotations VALUES(?,?,?,?)',(p['id'],VERSION,digest,json.dumps(groups)))
  cohorts[(tid,site)].append({'identity':identity,'compound':p['compound'],'compound_id':p['compound_id'],'pose_id':p['id'],'score':p['score'],'groups':sorted(names),'fingerprint':fingerprint,'protein':p['protein']})
  for group in sorted(names):presence.append({'protein_id':tid,'pocket_id':site,'compound':p['compound'],'identity':identity,'group':group,'present':True,'directly_participating':group in involved,'score':p['score']})
  details[identity]={'compound':p['compound'],'compound_id':p['compound_id'],'smiles':Chem.MolToSmiles(Chem.RemoveHs(mol)),'scaffold':MurckoScaffold.MurckoScaffoldSmiles(mol=mol),'groups':groups}
 ordered=sorted(mols);structural=chemical([mols[k] for k in ordered]);structural.update(identities=ordered,labels=[details[k]['compound'] for k in ordered]);cluster={identity:structural['clusters'][i] for i,identity in enumerate(ordered)}
 for identity in ordered:details[identity]['cluster']=cluster[identity]
 site_results=[]
 for (tid,site),records in cohorts.items():
  records.sort(key=lambda r:r['identity'])
  for r in records:r['cluster']=cluster[r['identity']];r['scaffold']=details[r['identity']]['scaffold']
  fp=interaction([r['fingerprint'] for r in records]);fp.update(labels=[r['compound'] for r in records],identities=[r['identity'] for r in records])
  site_results.append({'protein_id':tid,'pocket_id':site,'protein':records[0]['protein'],'distinct_compounds':len(records),'interaction_similarity':fp,'enrichment':enrichment(records),'ligands':[{k:v for k,v in r.items() if k!='fingerprint'} for r in records]})
 summaries=[{'protein_id':tid,'pocket_id':site,'functional_group':group,'interaction_type':kind,'protein_residues':'; '.join(sorted(v['residues'])),'distinct_compounds':len(v['compounds']),'interaction_events':len(v['events']),'distinct_ligand_residue_pairs':len(v['pairs'])} for (tid,site,group,kind),v in frequencies.items()]
 signature=hashlib.sha256(json.dumps({'poses':[(p['id'],p['score'],hashlib.sha256(Path(p['sdf_path']).read_bytes()).hexdigest()) for p in best.values()],'contacts':[(c['id'],c['metadata']) for c in rows(db,'SELECT i.id,i.metadata FROM molecular_interactions i JOIN docking_poses p ON p.id=i.pose_id JOIN docking_runs r ON r.id=p.run_id WHERE r.project_id=?',(pid,))]},sort_keys=True).encode()).hexdigest()
 result={'version':VERSION,'project_id':pid,'scope':{'protein':protein,'pocket':pocket,'max_unique_structures':limit,'selection':'Lexicographic InChIKey; best energy pose per identity/receptor/pocket','truncated':total_identities>limit},'signature':signature,'ontology':ontology(),'chemical_similarity':structural,'compound_details':details,'functional_group_interactions':summaries,'presence_vs_participation':presence,'site_cohorts':site_results,'interpretation':'These are predicted contact associations. A present functional group may not directly participate. Interaction events, distinct chemical identities and ligand-residue pairs are separate counts. Orthogonal molecular features may overlap conventional functional centres and their counts must not be summed. Similarity does not establish common mechanism or activity.'}
 if save:insert(db,'molecular_analysis_runs',project_id=pid,method_version=VERSION,scope=json.dumps(result['scope']),signature=signature,result=json.dumps(result))
 db.commit();return result

def export_tables(data,path,title='Interaction Table'):
 """Complete records in CSV/XLSX/DOCX; reject unsupported empty exports."""
 if not data:raise ValueError('No calculated records support this export')
 from openpyxl import Workbook
 from docx import Document
 from docx.shared import Inches,Pt
 from docx.enum.section import WD_ORIENT
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);fields=list(dict.fromkeys(k for r in data for k in r if k!='sdf_path'))
 clean=lambda v:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v
 with path.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.writer(f);writer.writerow(fields);writer.writerows([[clean(r.get(k)) for k in fields] for r in data])
 book=Workbook();ws=book.active;ws.title='Calculated records';ws.append(fields)
 for r in data:ws.append([("'"+v) if isinstance(v:=clean(r.get(k)),str) and v.startswith(('=','+','-','@')) else v for k in fields])
 ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions;book.save(path.with_suffix('.xlsx'))
 doc=Document();doc.core_properties.author='Ahmed G Soliman and Malak Taha';doc.add_heading(title,0);doc.add_paragraph(f'{len(data)} calculated records. Distances in angstrom; angles in degrees. CSV/XLSX preserve all fields and full metadata. Repeated pose identifiers appear once per section in this document; numeric geometry is not rounded.')
 for style in ['Title','Heading 1','Heading 2']:
  from docx.shared import RGBColor
  doc.styles[style].font.color.rgb=RGBColor(0,0,0)
 doc.styles['Normal'].font.size=Pt(9)
 if 'pose_id' in fields and 'interaction_type' in fields:
  sec=doc.sections[0];sec.orientation=WD_ORIENT.LANDSCAPE;sec.page_width=Inches(11.7);sec.page_height=Inches(8.3);sec.left_margin=sec.right_margin=Inches(.55)
  poses={}
  for r in data:poses.setdefault(r['pose_id'],[]).append(r)
  for pose,records in poses.items():
   first=records[0];doc.add_heading(str(first['compound'])+' | '+str(first['protein'])+' | pose '+str(first['docking_pose']),1)
   for line in [f"Protein ID {first['protein_id']}; identifier {first['protein_identifier']}; pocket {first['binding_pocket']} (ID {first['pocket_id']})",f"Compound ID {first['compound_id']}; InChIKey {first['inchikey']}; pose ID {pose}; Smina score {first['docking_score']} kcal/mol",'Source profiles: '+first['oil_profiles']]:doc.add_paragraph(line)
   headers=['Event and residue','Category','Protein atoms and indices','Ligand atoms and indices','Functional groups and atoms','Distance A','Angle degrees and definition','Method'];table=doc.add_table(rows=1,cols=len(headers));table.style='Light Shading Accent 1'
   for cell,text in zip(table.rows[0].cells,headers):cell.text=text
   for r in records:
    values=[f"{r['id']}: {r['residue']} | chain {r['chain']} | insertion {r['insertion_code'] or 'none'}",r['interaction_type'],str(r['protein_atom'])+' '+str(r['protein_atom_indices']),str(r['ligand_atom'])+' '+str(r['ligand_atom_indices']),'; '.join(g['name']+' '+str(g['atoms']) for g in r['functional_group_atoms']),str(r['distance']),str(r['angle'])+' '+r['angle_definition'] if r['angle'] is not None else 'Unavailable',r['method']]
    for cell,value in zip(table.add_row().cells,values):cell.text=value
 elif len(fields)<=8:
  table=doc.add_table(rows=1,cols=len(fields));table.style='Light Shading Accent 1'
  for cell,key in zip(table.rows[0].cells,fields):cell.text=key.replace('_',' ')
  for r in data:
   for cell,key in zip(table.add_row().cells,fields):cell.text=str(clean(r.get(key)) if r.get(key) is not None else 'Unavailable')
 else:
  for index,r in enumerate(data,1):
   doc.add_heading('Record '+str(index),2);table=doc.add_table(rows=0,cols=2);table.style='Light Shading Accent 1'
   for key in fields:
    cells=table.add_row().cells;cells[0].text=key.replace('_',' ');cells[1].text=str(clean(r.get(key)) if r.get(key) is not None else 'Unavailable')
 doc.save(path.with_suffix('.docx'));return path.with_suffix('.csv')

def export_analysis(result,folder):
 folder=Path(folder);folder.mkdir(exist_ok=True,parents=True);(folder/'molecular_analysis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 for key in ['functional_group_interactions','presence_vs_participation']:
  if result[key]:export_tables(result[key],folder/key,key.replace('_',' ').title())
 matrices=[('molecular_similarity',result['chemical_similarity'])]+[(f"interaction_similarity_protein_{s['protein_id']}_pocket_{s['pocket_id']}",s['interaction_similarity']) for s in result['site_cohorts']]
 for name,m in matrices:
  if m['matrix']:export_tables([{'compound':label,**{other:value for other,value in zip(m['labels'],r)}} for label,r in zip(m['labels'],m['matrix'])],folder/name,m['method'])
 cluster_rows=[{'identity':identity,'compound':d['compound'],'cluster':d['cluster'],'scaffold':d['scaffold'],'smiles':d['smiles']} for identity,d in result['compound_details'].items()]
 if cluster_rows:export_tables(cluster_rows,folder/'chemical_clusters','Structural clusters')
 return folder
