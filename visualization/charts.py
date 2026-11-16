"""Real project data shared by interactive Plotly views and static exports."""
import json,math,csv,textwrap,hashlib
from collections import defaultdict
from pathlib import Path
import numpy as np
import networkx as nx
from database.store import rows
from scientific.ranking import project_rankings,multi_target
from visualization.semantics import stable_color,INTERACTIONS,PALETTE

CHARTS=['Docking Score Heatmap','Compound-Protein Bubble Plot','Oil-Protein Bubble Plot','Essential Oil Ranking','Compound Ranking','Protein-Ligand Interaction Matrix','Interaction Network','Residue Interaction Frequency','Compound-Oil Relationship Network','Multi-Target Comparison']
ANALYSIS_CHARTS=['Interaction Frequency Heatmap','Functional Group Frequency Plot','Functional Group-Residue Network','Molecular Similarity Heatmap','Interaction Fingerprint Similarity Heatmap','Chemical Diversity Visualization']
CHARTS+=ANALYSIS_CHARTS
SYMBOLS={'HBDonor':'circle','HBAcceptor':'circle','Hydrophobic':'square','Cationic':'diamond','Anionic':'diamond','FaceToFace':'triangle-up','EdgeToFace':'triangle-down','PiCation':'cross','CationPi':'cross','VdWContact':'circle-open','MetalDonor':'star','MetalAcceptor':'star'}
def wrapped(s):return '<br>'.join(textwrap.wrap(str(s),33)[:3])
def project_data(db,pid,protein=None,profile=None,interaction=None,top_n=15,compound=None,pocket=None):
 settings=json.loads(db.execute('SELECT settings FROM analysis_projects WHERE id=?',(pid,)).fetchone()[0]);selected=settings.get('profiles',[])
 profiles={r['id']:r for r in rows(db,'SELECT p.*,o.name AS oil FROM oil_profiles p JOIN essential_oils o ON o.id=p.oil_id') if r['id'] in selected and (not profile or r['id']==int(profile))}
 poses=rows(db,"SELECT p.id AS pose_id,p.rank AS pose,p.score,r.compound_id,r.protein_id,r.pocket_id,c.name AS compound,t.name AS protein,k.rank AS pocket,COALESCE(NULLIF(s.inchikey,''),'compound:'||c.id) AS chemical_identity FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id JOIN chemical_compounds c ON c.id=r.compound_id LEFT JOIN compound_structures s ON s.compound_id=c.id JOIN protein_targets t ON t.id=r.protein_id JOIN predicted_pockets k ON k.id=r.pocket_id WHERE r.project_id=? AND r.status IN ('complete','interaction_review','figure_review') ORDER BY p.score,p.id",(pid,))
 best={}
 for p in poses:
  if protein and p['protein_id']!=int(protein):continue
  if compound and p['compound_id']!=int(compound) or pocket and p['pocket_id']!=int(pocket):continue
  best.setdefault((p['protein_id'],p['chemical_identity']),p)
 candidates=sorted({p['chemical_identity'] for p in best.values()},key=lambda identity:min(p['score'] for p in best.values() if p['chemical_identity']==identity))[:top_n]
 best=[p for p in best.values() if p['chemical_identity'] in candidates]
 composition={}
 for r in rows(db,"SELECT pc.*,c.name AS compound,COALESCE(NULLIF(s.inchikey,''),'compound:'||c.id) AS chemical_identity FROM profile_compounds pc JOIN chemical_compounds c ON c.id=pc.compound_id LEFT JOIN compound_structures s ON s.compound_id=c.id"):
  if r['profile_id'] in profiles:composition.setdefault((r['profile_id'],r['chemical_identity']),[]).append(r)
 associations=[]
 for p in best:
  for (profile_id,identity),obs in composition.items():
   if identity!=p['chemical_identity']:continue
   pr=profiles[profile_id];o=obs[0]
   associations.append({**p,'profile_id':profile_id,'profile':pr['name'],'oil':pr['oil'],'source_names':'; '.join(v['original_name'] for v in obs),'abundance':o['percentage'] if len(obs)==1 and o['docking_eligible'] else None,'reported_value':o['reported_value'] if o['reported_value'] is not None else o['percentage'],'reported_unit':o['reported_unit'] or 'GC peak area %','source_entries':len(obs),'color':stable_color(pr['oil'])})
 allowed={p['pose_id'] for p in best}
 contacts=[r for r in rows(db,'SELECT i.*,p.id AS selected_pose_id,c.name AS compound,t.name AS protein,r.protein_id,r.compound_id,p.rank AS pose FROM molecular_interactions i JOIN docking_poses p ON p.id=i.pose_id JOIN docking_runs r ON r.id=p.run_id JOIN chemical_compounds c ON c.id=r.compound_id JOIN protein_targets t ON t.id=r.protein_id WHERE r.project_id=?',(pid,)) if r['selected_pose_id'] in allowed and (not interaction or r['interaction_type']==interaction)]
 if profile:
  ids={a['compound_id'] for a in associations};best=[p for p in best if p['compound_id'] in ids];contacts=[r for r in contacts if r['compound_id'] in ids]
 return {'best':best,'associations':associations,'contacts':contacts,'profiles':profiles,'settings':settings}

def chart_spec(db,pid,kind,protein=None,profile=None,interaction=None,top_n=15,size_variable='Uniform',compound=None,pocket=None):
 if kind not in CHARTS:raise ValueError('Unknown chart type')
 if kind in ANALYSIS_CHARTS:return analysis_spec(db,pid,kind,protein,pocket,profile,compound,interaction,top_n)
 data=project_data(db,pid,protein,profile,interaction,top_n,compound,pocket);best=data['best'];assoc=data['associations'];contacts=data['contacts'];traces=[];records=[];notes=['Only saved calculations are shown. Display filters do not recompute or change the original screening index.'];xlabel='';ylabel='';title=kind
 target_names={r['id']:r['name'] for r in rows(db,'SELECT id,name FROM protein_targets WHERE project_id=?',(pid,))}
 ranks=project_rankings(db,pid);oilrows=[]
 for tid,rs in ranks.items():
  if protein and tid!=int(protein):continue
  for r in rs:
   if r['profile_id'] in data['profiles'] and r['index'] is not None:
    p=data['profiles'][r['profile_id']];oilrows.append({'protein':target_names[tid],'protein_id':tid,'profile':p['name'],'profile_id':p['id'],'oil':p['oil'],**r,'color':stable_color(p['oil'])})
 def trace_scatter(points,x,y,group,size=None,label=None):
  global_max=max((p[size] for p in points),default=1) if size else 18
  for key in dict.fromkeys(p[group] for p in points):
   ps=[p for p in points if p[group]==key];values=[p[size] for p in ps] if size else [18]*len(ps)
   hover=[]
   for p in ps:
    fields=[('Compound',p.get('compound')),('Protein',p.get('protein')),('Pocket',p.get('pocket')),('Source profile',p.get('profile')),('Smina (kcal/mol)',p.get('score')),('Oil index',p.get('index')),('Screened GC area (%)',p.get('screened_peak_area_percent')),('Reported value',str(p.get('reported_value'))+' '+str(p.get('reported_unit')) if p.get('reported_value') is not None else None),('Residue',p.get('residue')),('Distinct poses',p.get('poses'))]
    hover.append('<br>'.join(k+': '+wrapped(str(round(v,4) if isinstance(v,float) else v)) for k,v in fields if v is not None))
   symbol=['circle','square','diamond','triangle-up','triangle-down','pentagon','hexagon','star','cross','x'][hashlib.sha256(str(key).encode()).digest()[0]%10]
   traces.append({'type':'scatter','mode':'markers','name':str(key),'x':[p[x] for p in ps],'y':[wrapped(p[y]) for p in ps],'text':hover,'hovertemplate':'%{text}<extra></extra>','marker':{'color':ps[0].get('color',stable_color(key)),'symbol':symbol,'size':values,'sizemode':'area','sizeref':2*(global_max or 1)/1600,'sizemin':4,'opacity':.8,'line':{'color':'#243447','width':.6}}})
 if kind=='Docking Score Heatmap':
  records=best;xs=list(dict.fromkeys(p['protein'] for p in best));ys=list(dict.fromkeys(p['compound'] for p in best));matrix=[[next((p['score'] for p in best if p['protein']==x and p['compound']==y),None) for x in xs] for y in ys]
  if records:traces=[{'type':'heatmap','x':xs,'y':[wrapped(y) for y in ys],'z':matrix,'colorscale':'Viridis','reversescale':True,'colorbar':{'title':{'text':'kcal/mol'}},'hovertemplate':'Protein: %{x}<br>Compound: %{y}<br>Smina: %{z:.3f} kcal/mol<extra></extra>'}]
  xlabel='Protein target';ylabel='Compound';notes.append('Missing cells represent unavailable calculations.')
 elif kind=='Compound-Protein Bubble Plot':
  records=assoc
  if size_variable=='GC peak area (%)':records=[r for r in records if r['abundance'] is not None and r['abundance']>0];notes.append('Bubble area = original GC peak area (%). Other units and ambiguous duplicate observations are excluded from this size mode.')
  else:notes.append('Bubble area is uniform. Reported abundance and its original unit appear in each tooltip.')
  for r in records:r['compound_profile']=r['compound']+' | '+r['profile'];r['bubble_area']=r['abundance'] if size_variable=='GC peak area (%)' else 1.
  trace_scatter(records,'protein','compound_profile','oil','bubble_area');xlabel='Protein target';ylabel='Compound and source profile';notes.append('Separate profile-specific points preserve multiple oil membership. Color and marker = botanical oil identity. One shared size scale is used across all oils; minimum marker diameter is 4 pixels.')
 elif kind=='Oil-Protein Bubble Plot':
  records=oilrows;metric='screened_peak_area_percent' if size_variable=='Screened GC peak area (%)' else 'index'
  for r in records:r['bubble_area']=r[metric]
  trace_scatter(records,'protein','profile','oil','bubble_area');xlabel='Protein target';ylabel='Essential-oil source profile';notes.append('Bubble area = '+('screened original GC peak area (%)' if metric!='index' else 'normalized oil screening index (0-1)')+'. Color = botanical oil identity. Non-rankable extracts are absent.')
 elif kind=='Essential Oil Ranking':
  records=sorted(oilrows,key=lambda r:r['index'],reverse=True)[:top_n]
  for r in records:r['label']=r['profile']+' | '+r['protein']
  trace_scatter(records,'index','label','oil');xlabel='Composition-informed screening index (0-1)';ylabel='Source profile and target';notes.append('Coverage and uncertainty accompany the index in the tooltip. This is not an efficacy ranking.')
 elif kind=='Compound Ranking':
  records=sorted(best,key=lambda r:r['score'])[:top_n]
  for r in records:r['label']=r['compound']+' | '+r['protein'];r['color']=stable_color(r['protein'])
  trace_scatter(records,'score','label','protein');xlabel='Smina docking score (kcal/mol)';ylabel='Compound and target';notes.append('Lower scores are favored within the same target and protocol; cross-target energy differences do not establish selectivity.')
 elif kind=='Protein-Ligand Interaction Matrix':
  records=contacts;xs=list(dict.fromkeys(c['compound']+' | '+c['protein']+' | pose '+str(c['pose']) for c in contacts));ys=list(dict.fromkeys(c['protein']+' | '+c['residue'] for c in contacts));kinds=list(dict.fromkeys(c['interaction_type'] for c in contacts))
  for j,k in enumerate(kinds):
   ps=[p for p in contacts if p['interaction_type']==k];pairs={}
   for p in ps:pairs.setdefault((p['compound']+' | '+p['protein']+' | pose '+str(p['pose']),p['protein']+' | '+p['residue']),[]).append(p)
   traces.append({'type':'scatter','mode':'markers','name':k,'x':[xs.index(x)+(j-(len(kinds)-1)/2)*.045 for x,y in pairs],'y':[ys.index(y) for x,y in pairs],'text':['<br>'.join(f"{r['residue']} {k}: {r['distance']:.3f} A; {r['protein_atom']} to {r['ligand_atom']}" for r in rs) for rs in pairs.values()],'hovertemplate':'%{text}<extra></extra>','marker':{'color':PALETTE[k],'symbol':SYMBOLS[k],'size':11}})
  xlabel='Calculated ligand pose';ylabel='Protein and residue';notes.append('Each category has its own marker. Multiple interaction categories in one ligand-residue cell are retained with small horizontal offsets; cells are not affinity measurements.')
 elif kind=='Residue Interaction Frequency':
  counts={}
  for r in contacts:counts.setdefault((r['protein'],r['residue'],r['interaction_type']),set()).add(r['pose_id'])
  records=[{'protein':p,'residue':r,'interaction_type':k,'poses':len(ids),'label':p+' | '+r,'color':PALETTE[k]} for (p,r,k),ids in counts.items()]
  for r in records:r['interaction_type']=r['interaction_type']
  trace_scatter(records,'poses','label','interaction_type');xlabel='Distinct saved poses with this interaction';ylabel='Protein and residue';notes.append('Counts refer to distinct selected best poses and do not measure interaction strength.')
 elif kind in ['Interaction Network','Compound-Oil Relationship Network']:
  graph=nx.MultiGraph();records=contacts if kind=='Interaction Network' else assoc
  if kind=='Interaction Network':
   freq={}
   for c in contacts:freq[(c['protein'],c['residue'])]=freq.get((c['protein'],c['residue']),0)+1
   keep=set(sorted(freq,key=freq.get,reverse=True)[:max(10,min(30,top_n*2))]);records=[c for c in contacts if (c['protein'],c['residue']) in keep]
   for c in records:
    a='Ligand: '+c['compound'];b=c['protein']+' | '+c['residue'];p='Protein: '+c['protein'];graph.add_node(a,group='Ligand',label=c['compound']);graph.add_node(b,group='Residue',label=b);graph.add_node(p,group='Protein',label=c['protein']);graph.add_edge(a,b,kind=c['interaction_type']);graph.add_edge(p,b,kind='Residue membership')
   notes.append('Network is limited to the most frequent residues in the filtered best poses. Multiple edge categories are preserved; residue-membership edges are structural associations.')
  else:
   for c in records:
    a='Oil: '+c['profile'];b='Ligand: '+c['compound'];graph.add_node(a,group=c['oil'],label=c['profile']);graph.add_node(b,group='Ligand',label=c['compound']);graph.add_edge(a,b,kind='Reported constituent')
   notes.append('Edges represent documented source membership for screened compounds, not molecular binding or biological efficacy.')
  if graph:
   simple=nx.Graph(graph);pos=nx.spring_layout(simple,seed=20261029,k=2/max(2,math.sqrt(len(graph))),iterations=180)
   # Expand colliding node centers deterministically without moving data anchors.
   for _ in range(80):
    for i,a in enumerate(pos):
     for b in list(pos)[i+1:]:
      v=pos[a]-pos[b];d=float(np.linalg.norm(v))
      if d<.17:
       v=v/(d or .001)*(.17-d)*.08;pos[a]+=v;pos[b]-=v
   edge_pairs={}
   for a,b,v in graph.edges(data=True):edge_pairs.setdefault(tuple(sorted([a,b])),set()).add(v['kind'])
   for (a,b),ks in edge_pairs.items():
    for j,k in enumerate(sorted(ks)):
     v=pos[b]-pos[a];normal=np.array([-v[1],v[0]])/(np.linalg.norm(v) or 1);mid=(pos[a]+pos[b])/2+normal*(j-(len(ks)-1)/2)*.045
     traces.append({'type':'scatter','mode':'lines','name':k,'legendgroup':k,'showlegend':not any(t.get('name')==k for t in traces),'x':[float(pos[a][0]),float(mid[0]),float(pos[b][0])],'y':[float(pos[a][1]),float(mid[1]),float(pos[b][1])],'text':[a+' to '+b+': '+k]*3,'hovertemplate':'%{text}<extra></extra>','line':{'color':PALETTE.get(k,'#a1aebd'),'width':1.5}})
   for group in dict.fromkeys(nx.get_node_attributes(graph,'group').values()):
    ns=[n for n in graph if graph.nodes[n]['group']==group];traces.append({'type':'scatter','mode':'markers+text','name':group,'x':[float(pos[n][0]) for n in ns],'y':[float(pos[n][1]) for n in ns],'text':[wrapped(graph.nodes[n]['label']) for n in ns],'textposition':'top center','hovertext':ns,'hovertemplate':'%{hovertext}<extra></extra>','marker':{'size':16,'color':stable_color(group),'symbol':'diamond' if group=='Protein' else 'circle'}})
  xlabel='';ylabel=''
 elif kind=='Multi-Target Comparison':
  if len(target_names)>1:
   records=oilrows;xs=list(dict.fromkeys(r['protein'] for r in records));ys=list(dict.fromkeys(r['profile'] for r in records));matrix=[[next((r['index'] for r in records if r['protein']==x and r['profile']==y),None) for x in xs] for y in ys]
   if records:traces=[{'type':'heatmap','x':xs,'y':[wrapped(y) for y in ys],'z':matrix,'zmin':0,'zmax':1,'colorscale':'YlGnBu','colorbar':{'title':{'text':'Index (0-1)'}},'hovertemplate':'%{y}<br>%{x}<br>Index %{z:.3f}<extra></extra>'}]
  xlabel='Protein target';ylabel='Essential-oil source profile';notes.append('One matrix cell per source profile and target. Missing targets remain unavailable and are not silently reweighted.')
 row_count=len({r.get('compound_profile',r.get('label',r.get('residue',r.get('compound',r.get('profile',''))))) for r in records})
 if kind=='Protein-Ligand Interaction Matrix':row_count=len(ys)
 layout={'title':{'text':title,'x':.03},'xaxis':{'title':{'text':xlabel},'automargin':True},'yaxis':{'title':{'text':ylabel},'automargin':True},'font':{'family':'Segoe UI,Arial','size':12},'paper_bgcolor':'#ffffff','plot_bgcolor':'#f6f9fc','margin':{'l':180,'r':35,'t':60,'b':100},'legend':{'orientation':'h','y':-0.22},'hovermode':'closest','height':max(560,min(10000,240+row_count*36))}
 if kind=='Protein-Ligand Interaction Matrix':layout['xaxis'].update(tickmode='array',tickvals=list(range(len(xs))),ticktext=[v.replace(' | ','<br>') for v in xs],tickangle=-55);layout['yaxis'].update(tickmode='array',tickvals=list(range(len(ys))),ticktext=[wrapped(v) for v in ys])
 if 'Network' in kind:layout['xaxis'].update(visible=False);layout['yaxis'].update(visible=False);layout['showlegend']=True;layout['margin']['l']=25
 return {'kind':kind,'available':bool(records and traces),'rows':records,'data':traces,'layout':layout,'notes':' '.join(notes),'x_label':xlabel,'y_label':ylabel}

def export_chart(spec,path,dpi=300):
 """Matplotlib export of the same plotted arrays; CSV is the actual data."""
 if not spec['available']:raise ValueError('No scientific data supports this chart')
 import matplotlib
 matplotlib.use('Agg')
 from matplotlib import pyplot as plt
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fig,ax=plt.subplots(figsize=(max(10,min(20,6+len(spec['data'])*.3)),max(6,min(22,spec['layout']['height']/90))))
 if spec['kind']=='Protein-Ligand Interaction Matrix':fig.set_size_inches(max(12,len(spec['layout']['xaxis']['tickvals'])*.95+5),fig.get_figheight())
 numeric_y=spec['kind']=='Protein-Ligand Interaction Matrix' or 'Network' in spec['kind'] or spec['kind']=='Chemical Diversity Visualization';cats=[]
 all_sizes=[v for t in spec['data'] if isinstance(t.get('marker',{}).get('size'),list) for v in t['marker']['size']];global_max=max(all_sizes,default=1) or 1
 for t in spec['data']:
  if t['type']=='heatmap':
   matrix=np.array([[np.nan if x is None else x for x in row] for row in t['z']],float);im=ax.imshow(matrix,aspect='auto',cmap='viridis_r' if spec['kind']=='Docking Score Heatmap' else 'YlGnBu');ax.set_xticks(range(len(t['x'])),[s.replace('<br>','\n') for s in t['x']],rotation=55,ha='right',fontsize=8);ax.set_yticks(range(len(t['y'])),[s.replace('<br>','\n') for s in t['y']],fontsize=8);fig.colorbar(im,ax=ax,label='Smina score (kcal/mol)' if spec['kind']=='Docking Score Heatmap' else 'Contact events' if spec['kind']=='Interaction Frequency Heatmap' else 'Tanimoto / Jaccard' if 'Similarity' in spec['kind'] else 'Screening index (0-1)');continue
  yy=t['y']
  if not numeric_y:
   for y in yy:
    if y not in cats:cats.append(y)
   yy=[cats.index(y) for y in yy]
  if 'lines' in t.get('mode',''):ax.plot(t['x'],yy,color=t.get('line',{}).get('color','#778899'),linewidth=1,alpha=.7);continue
  marker={'circle':'o','square':'s','diamond':'D','triangle-up':'^','triangle-down':'v','cross':'P','circle-open':'o','star':'*','pentagon':'p','hexagon':'h','x':'X'}.get(t.get('marker',{}).get('symbol'),'o');sizes=t.get('marker',{}).get('size',18)
  if isinstance(sizes,list):sizes=[max(10,350*v/global_max) for v in sizes]
  else:sizes=70
  ax.scatter(t['x'],yy,s=sizes,color=t.get('marker',{}).get('color','#17867e'),marker=marker,label=t['name'],alpha=.8,edgecolors='#263749',linewidths=.3)
  if 'text' in t.get('mode',''):
   for x,y,txt in zip(t['x'],yy,t['text']):ax.annotate(txt.replace('<br>','\n'),(x,y),xytext=(0,9),textcoords='offset points',ha='center',fontsize=7)
 if cats:ax.set_yticks(range(len(cats)),[s.replace('<br>','\n') for s in cats],fontsize=8)
 if spec['kind']=='Protein-Ligand Interaction Matrix':
  for axis,key in [(ax.xaxis,'xaxis'),(ax.yaxis,'yaxis')]:
   axis.set_ticks(spec['layout'][key]['tickvals']);axis.set_ticklabels([s.replace('<br>','\n') for s in spec['layout'][key]['ticktext']],fontsize=7)
  plt.setp(ax.get_xticklabels(),rotation=55,ha='right',rotation_mode='anchor')
 if 'Network' in spec['kind']:ax.axis('off')
 ax.set_title(spec['kind']);ax.set_xlabel(spec['x_label']);ax.set_ylabel(spec['y_label'])
 handles,labels=ax.get_legend_handles_labels()
 if handles:ax.legend(loc='upper left',bbox_to_anchor=(1.02,1),fontsize=8)
 fig.text(.02,.015,textwrap.fill(spec['notes'],125),fontsize=8);fig.subplots_adjust(left=.25,bottom=.22,right=.78,top=.92)
 for suffix in ['.png','.svg','.pdf']:fig.savefig(path.with_suffix(suffix),dpi=dpi,bbox_inches='tight')
 plt.close(fig)
 fields=list(dict.fromkeys(k for r in spec['rows'] for k in r))
 with path.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in spec['rows'])
 from openpyxl import Workbook
 workbook=Workbook();sheet=workbook.active;sheet.title='Plotted records';sheet.append(fields)
 for r in spec['rows']:
  values=[json.dumps(r.get(k)) if isinstance(r.get(k),(list,dict)) else r.get(k) for k in fields];sheet.append(["'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v for v in values])
 sheet.freeze_panes='A2';workbook.save(path.with_suffix('.xlsx'))
 path.with_suffix('.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8');return path.with_suffix('.png')

def analysis_spec(db,pid,kind,protein=None,pocket=None,profile=None,compound=None,interaction_type=None,top_n=15,precomputed=None):
 from scientific.molecular_analysis import analyze
 result=precomputed if precomputed is not None else analyze(db,pid,protein,pocket,max(2,top_n),save=False,compound=compound,profile=profile,interaction_type=interaction_type);traces=[];records=[];note=result['interpretation']+(' Contact categories restricted to '+interaction_type+'.' if interaction_type else '');x_label=y_label='';matrix=None;labels=[]
 if kind=='Molecular Similarity Heatmap':
  s=result['chemical_similarity'];matrix=s['matrix'];labels=s['labels'];note+=' '+s['method']
  if len(labels)<2:matrix=None
 elif kind=='Interaction Fingerprint Similarity Heatmap':
  cohorts=result['site_cohorts'];s=cohorts[0]['interaction_similarity'] if cohorts else None
  if s and len(s['labels'])>=2:matrix=s['matrix'];labels=s['labels'];note+=f" Cohort: {cohorts[0]['protein']}, pocket ID {cohorts[0]['pocket_id']}. "+s['method']
  if len(cohorts)>1:note+=' Select a protein and binding site to inspect another compatible cohort; no cross-site fingerprint averaging is performed.'
 elif kind=='Interaction Frequency Heatmap':
  source=result['functional_group_interactions'];source=[r for r in source if not interaction_type or r['interaction_type']==interaction_type];xs=sorted({r['functional_group'] for r in source});ys=sorted({str(r['protein_id'])+' | '+r['interaction_type'] for r in source});matrix=[[sum(r['interaction_events'] for r in source if r['functional_group']==x and str(r['protein_id'])+' | '+r['interaction_type']==y) for x in xs] for y in ys]
  if source:traces=[{'type':'heatmap','x':[wrapped(v) for v in xs],'y':ys,'z':matrix,'colorscale':'YlGnBu','hovertemplate':'Feature: %{x}<br>Protein/category: %{y}<br>Contact events: %{z}<extra></extra>'}];records=source
  matrix=None;x_label='Functional centre / molecular feature';y_label='Protein identifier and category';note+=' Frequencies are contact events and may overlap across orthogonal feature domains.'
 elif kind=='Functional Group Frequency Plot':
  groups=defaultdict(lambda:{'present':set(),'involved':set()})
  for r in result['presence_vs_participation']:
   key=(r['protein_id'],r['pocket_id'],r['identity']);groups[r['group']]['present'].add(key)
   if r['directly_participating']:groups[r['group']]['involved'].add(key)
  records=[{'group':g,'present_compound_site_pairs':len(v['present']),'participating_compound_site_pairs':len(v['involved'])} for g,v in groups.items()];ys=[r['group'] for r in records]
  for field,color,label in [('present_compound_site_pairs','#94a3b8','Present'),('participating_compound_site_pairs','#158a80','Directly participating')]:traces.append({'type':'scatter','mode':'markers','x':[r[field] for r in records],'y':ys,'name':label,'marker':{'color':color,'size':14},'hovertemplate':'%{y}<br>'+label+': %{x} distinct chemical-identity/site pairs<extra></extra>'})
  x_label='Distinct chemical-identity and binding-site pairs';y_label='Functional centre / molecular feature'
 elif kind=='Functional Group-Residue Network':
  records=[r for r in result['functional_group_interactions'] if not interaction_type or r['interaction_type']==interaction_type];g=nx.Graph()
  for r in records:
   for residue in r['protein_residues'].split('; '):g.add_edge('Group: '+r['functional_group'],f"Protein {r['protein_id']} | {residue}")
  if g:
   pos=nx.bipartite_layout(g,[n for n in g if n.startswith('Group:')]);edge_x=[];edge_y=[]
   for a,b in g.edges:edge_x += [float(pos[a][0]),float(pos[b][0]),None];edge_y += [float(pos[a][1]),float(pos[b][1]),None]
   traces.append({'type':'scatter','mode':'lines','name':'Observed group-residue association','x':edge_x,'y':edge_y,'hoverinfo':'skip','line':{'color':'#94a3b8','width':1}})
   for group in ['Group:','Protein']:
    ns=[n for n in g if n.startswith(group)];traces.append({'type':'scatter','mode':'markers+text','name':group.rstrip(':'),'x':[float(pos[n][0]) for n in ns],'y':[float(pos[n][1]) for n in ns],'text':[wrapped(n) for n in ns],'textposition':'middle right' if group=='Group:' else 'middle left','hovertemplate':'%{text}<extra></extra>','marker':{'color':'#168a80' if group=='Group:' else '#7c3aed','size':12}})
 elif kind=='Chemical Diversity Visualization':
  s=result['chemical_similarity'];m=np.asarray(s['matrix']);ids=s['identities']
  if len(ids)>=2:
   # Classical metric MDS of Morgan/Tanimoto dissimilarities; no energy input.
   dist=1-m;j=np.eye(len(ids))-np.ones_like(m)/len(ids);b=-.5*j@(dist**2)@j;values,vectors=np.linalg.eigh(b);order=np.argsort(values)[::-1][:2];coordinates=vectors[:,order]*np.sqrt(np.maximum(values[order],0));coordinates=np.pad(coordinates,((0,0),(0,max(0,2-coordinates.shape[1]))))
   records=[{'identity':identity,'compound':result['compound_details'][identity]['compound'],'cluster':result['compound_details'][identity]['cluster'],'dimension_1':float(coordinates[i,0]),'dimension_2':float(coordinates[i,1])} for i,identity in enumerate(ids)]
   for cluster in sorted({r['cluster'] for r in records}):
    rr=[r for r in records if r['cluster']==cluster];traces.append({'type':'scatter','mode':'markers+text','name':'Cluster '+str(cluster),'x':[r['dimension_1'] for r in rr],'y':[r['dimension_2'] for r in rr],'text':[r['compound'] for r in rr],'textposition':'top center','hovertemplate':'%{text}<extra></extra>','marker':{'color':stable_color(cluster),'size':13}})
   x_label='Classical MDS coordinate 1';y_label='Classical MDS coordinate 2';note+=' Classical MDS on 1−Tanimoto distances; negative eigenvalues are omitted. Display coordinates are approximate; the complete similarity matrix is authoritative.'
 if matrix is not None:
  traces=[{'type':'heatmap','x':[wrapped(s) for s in labels],'y':[wrapped(s) for s in labels],'z':matrix,'zmin':0,'zmax':1,'colorscale':'Viridis','hovertemplate':'%{x}<br>%{y}<br>Tanimoto/Jaccard: %{z:.4f}<extra></extra>'}];records=[{'compound':a,**{b:v for b,v in zip(labels,r)}} for a,r in zip(labels,matrix)];x_label=y_label='Chemical identity (compound label)'
 layout={'title':{'text':kind,'x':.03},'height':max(600,min(8000,280+len(records)*30)),'xaxis':{'title':{'text':x_label},'automargin':True,'tickangle':-40 if 'Heatmap' in kind else 0},'yaxis':{'title':{'text':y_label},'automargin':True},'margin':{'l':200,'r':45,'b':140,'t':65},'legend':{'orientation':'h','y':-0.2},'paper_bgcolor':'white','plot_bgcolor':'#f6f9fc'}
 if 'Network' in kind:layout['xaxis']['visible']=False;layout['yaxis']['visible']=False;layout['margin']['l']=25
 return {'kind':kind,'available':bool(records and traces),'rows':records,'data':traces,'layout':layout,'notes':note,'x_label':x_label,'y_label':y_label}
