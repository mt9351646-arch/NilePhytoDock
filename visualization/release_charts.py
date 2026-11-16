"""Bounded, read-only chart queries for the production chart page."""
import json,math
from collections import defaultdict
from database.store import rows
from scientific.result_summary import protocol_key,PROTOCOL_KEYS
from visualization.semantics import stable_color

CHARTS=('Bubble Plot','Docking Heatmap','Interaction Matrix','Docking Network')
def short(value,length=25):return str(value) if len(str(value))<=length else str(value)[:length-1]+'…'
def chart_spec(db,pid,kind,protein=None,oil=None,pocket=None,top_n=20):
 if kind not in CHARTS:raise ValueError('Unknown release chart')
 project=db.execute('SELECT settings FROM analysis_projects WHERE id=?',(pid,)).fetchone()
 empty={'kind':kind,'data':[],'rows':[],'available':False,'notes':'No saved calculations support this selection.','x_label':'','y_label':'','layout':{'height':560},'display_limit':top_n}
 if not project:return empty
 settings=json.loads(project[0]);profiles=settings.get('profiles',[])
 if not profiles:return empty
 params=[pid];where="r.project_id=? AND r.status IN ('complete','interaction_review','figure_review') AND p.score IS NOT NULL"
 if protein:where+=' AND r.protein_id=?';params.append(protein)
 if pocket:where+=' AND r.pocket_id=?';params.append(pocket)
 variants=rows(db,'SELECT DISTINCT r.settings,r.engine_version FROM docking_runs r JOIN docking_poses p ON p.run_id=r.id WHERE '+where,params)
 if not variants:return empty
 def preference(r):
  d=json.loads(r['settings']);return (tuple(d.get(k)!=settings.get(k,'vina' if k=='scoring' else None) for k in PROTOCOL_KEYS if k in settings or k=='scoring'),protocol_key(r['settings'],r['engine_version']))
 chosen=protocol_key(**{'settings':min(variants,key=preference)['settings'],'engine':min(variants,key=preference)['engine_version']});variants=[v for v in variants if protocol_key(v['settings'],v['engine_version'])==chosen]
 clauses=[]
 for v in variants:clauses.append('(r.settings=? AND COALESCE(r.engine_version,\'\')=?)');params += [v['settings'],v['engine_version'] or '']
 where+=' AND ('+' OR '.join(clauses)+')'
 marks=','.join('?' for _ in profiles);member_params=list(profiles)
 membership=f"pc.profile_id IN ({marks}) AND pc.docking_eligible=1 AND s.status='ready' AND (pc.percentage>0 OR pc.reported_value>0 OR pc.value_status IN ('presence_only','trace'))"
 if oil:membership+=' AND op.oil_id=?';member_params.append(oil)
 identity="COALESCE(NULLIF(s.inchikey,''),'compound:'||c.id)"
 sql=f"""WITH allowed AS (SELECT DISTINCT COALESCE(NULLIF(s.inchikey,''),'compound:'||pc.compound_id) AS identity FROM profile_compounds pc JOIN oil_profiles op ON op.id=pc.profile_id LEFT JOIN compound_structures s ON s.compound_id=pc.compound_id WHERE {membership}), ranked AS (SELECT p.id AS pose_id,p.score,p.rank AS pose,r.compound_id,r.protein_id,r.pocket_id,k.rank AS pocket,c.name AS compound,t.name AS protein,{identity} AS identity,ROW_NUMBER() OVER(PARTITION BY r.protein_id,{identity} ORDER BY p.score,p.id) AS n FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id JOIN chemical_compounds c ON c.id=r.compound_id LEFT JOIN compound_structures s ON s.compound_id=c.id JOIN protein_targets t ON t.id=r.protein_id JOIN predicted_pockets k ON k.id=r.pocket_id WHERE {where} AND {identity} IN (SELECT identity FROM allowed)), shortlist AS (SELECT identity,MIN(score) AS best FROM ranked WHERE n=1 GROUP BY identity ORDER BY best,identity LIMIT ?) SELECT * FROM ranked WHERE n=1 AND identity IN (SELECT identity FROM shortlist) ORDER BY score,pose_id"""
 best=rows(db,sql,member_params+params+[int(top_n)]);best=[p for p in best if math.isfinite(p['score'])]
 if not best:return empty
 target_names={p['protein_id']:p['protein'] for p in best}
 target_labels={tid:name+(' [#'+str(tid)+']' if list(target_names.values()).count(name)>1 else '') for tid,name in target_names.items()}
 for p in best:p['protein']=target_labels[p['protein_id']]
 identities=list(dict.fromkeys(p['identity'] for p in best));labels={p['identity']:p['compound'] for p in reversed(best)};names=[labels[k] for k in identities];targets=list(dict.fromkeys(p['protein'] for p in best));traces=[];records=best;label_x='Protein';label_y='Compound';notes='Best saved pose per structure and protein in one docking protocol. Scores are kcal/mol; compare within the same target. Display is limited to '+str(top_n)+' structures; exports contain the plotted records.'
 axis=lambda labels:{'tickmode':'array','tickvals':list(range(len(labels))),'ticktext':[short(s) if len(labels)<=25 or i%2==0 else '' for i,s in enumerate(labels)],'automargin':True,'tickfont':{'size':11},'showgrid':False,'zeroline':False}
 layout={'height':560,'paper_bgcolor':'white','plot_bgcolor':'white','margin':{'l':165,'r':45,'t':15,'b':95},'font':{'family':'Segoe UI, Arial','size':13,'color':'#253b50'},'xaxis':axis(targets),'yaxis':{**axis(names),'autorange':'reversed'},'legend':{'orientation':'h','y':-.16,'x':0,'font':{'size':11},'maxheight':.15},'hovermode':'closest','uirevision':kind}
 if kind=='Docking Heatmap':
  values={(p['protein'],p['identity']):p['score'] for p in best};z=[[values.get((t,k)) for t in targets] for k in identities]
  traces=[{'type':'heatmap','x':list(range(len(targets))),'y':list(range(len(names))),'z':z,'customdata':[[[c,t] for t in targets] for c in names],'colorscale':'Viridis','reversescale':True,'colorbar':{'title':{'text':'kcal/mol'},'thickness':12},'hovertemplate':'%{customdata[0]}<br>%{customdata[1]}<br>Score: %{z:.3f} kcal/mol<extra></extra>'}]
  notes+=' Missing cells are unavailable calculations.'
 elif kind in ('Bubble Plot','Docking Network'):
  label_x='Docking score (kcal/mol)'
  layout['xaxis']={'type':'linear','automargin':True,'tickfont':{'size':11},'showgrid':True,'gridcolor':'#e9eef2','zeroline':False}
  members=rows(db,f"SELECT DISTINCT COALESCE(NULLIF(s.inchikey,''),'compound:'||pc.compound_id) AS identity,op.oil_id,eo.name AS oil FROM profile_compounds pc JOIN oil_profiles op ON op.id=pc.profile_id JOIN essential_oils eo ON eo.id=op.oil_id LEFT JOIN compound_structures s ON s.compound_id=pc.compound_id WHERE {membership}",member_params);groups=defaultdict(list)
  by_identity=defaultdict(list)
  for m in members:by_identity[m['identity']].append(m)
  for p in best:
   for m in by_identity[p['identity']]:groups[m['oil']].append({**p,'oil':m['oil'],'oil_id':m['oil_id']})
  oils=sorted(groups);records=[p for o in oils for p in groups[o]]
  project_oils=rows(db,f'SELECT DISTINCT eo.name FROM essential_oils eo JOIN oil_profiles op ON op.oil_id=eo.id WHERE op.id IN ({marks}) ORDER BY eo.name',profiles)
  palette=['#0072B2','#D55E00','#009E73','#CC79A7','#E69F00','#56B4E9','#332288','#882255','#44AA99','#999933']
  colors={v['name']:palette[i] if i<len(palette) else stable_color(v['name']) for i,v in enumerate(project_oils)}
  for p in records:p['oil_color']=colors[p['oil']]
  if kind=='Docking Network':
   return docking_network(records,chosen,top_n,protein)
  for i,o in enumerate(oils):
   ps=groups[o];offset=(i-(len(oils)-1)/2)*min(.05,.45/max(1,len(oils)))
   traces.append({'type':'scatter','mode':'markers','name':short(o,24),'x':[p['score'] for p in ps],'y':[identities.index(p['identity'])+offset for p in ps],'customdata':[[p['compound'],p['protein'],o,p['score'],p['pocket']] for p in ps],'marker':{'size':17,'color':colors[o],'opacity':.8,'line':{'width':.7,'color':'white'}},'hovertemplate':'%{customdata[0]}<br>Oil: %{customdata[2]}<br>Target: %{customdata[1]} / pocket %{customdata[4]}<br>Score: %{customdata[3]:.3f} kcal/mol<extra></extra>'})
  notes+=' Horizontal position is the unaltered docking score. Color identifies the botanical oil. Shared membership is retained with small vertical offsets. Bubble area is uniform.'
 else:
  ids=[p['pose_id'] for p in best];marks=','.join('?' for _ in ids)
  cells=rows(db,f"SELECT r.protein_id,t.name AS protein,i.residue,i.chain,i.residue_number,i.interaction_type,COUNT(DISTINCT i.pose_id) AS distinct_compounds,COUNT(*) AS contact_events,MIN(i.distance) AS minimum_distance_A FROM molecular_interactions i JOIN docking_poses p ON p.id=i.pose_id JOIN docking_runs r ON r.id=p.run_id JOIN protein_targets t ON t.id=r.protein_id WHERE i.pose_id IN (SELECT value FROM json_each(?)) GROUP BY r.protein_id,i.residue,i.interaction_type",(json.dumps(ids),))
  for r in cells:r['protein']=target_labels[r['protein_id']]
  counts=defaultdict(int)
  for r in cells:counts[r['protein']+' | '+r['residue']]+=r['contact_events']
  residues=sorted(counts,key=lambda k:(-counts[k],k))[:min(30,top_n)];kinds=sorted({r['interaction_type'] for r in cells});records=[r for r in cells if r['protein']+' | '+r['residue'] in residues]
  z=[[next((r['distinct_compounds'] for r in records if r['protein']+' | '+r['residue']==s and r['interaction_type']==k),0) for k in kinds] for s in residues]
  if records:traces=[{'type':'heatmap','x':list(range(len(kinds))),'y':list(range(len(residues))),'z':z,'customdata':[[[s,k] for k in kinds] for s in residues],'colorscale':'YlGnBu','colorbar':{'title':{'text':'Compounds'},'thickness':12},'hovertemplate':'%{customdata[0]}<br>%{customdata[1]}<br>Distinct compounds: %{z}<extra></extra>'}]
  layout['xaxis']=axis(kinds);layout['xaxis']['tickangle']=-25;layout['yaxis']={**axis(residues),'autorange':'reversed'};label_x='Detected interaction type';label_y='Protein / amino acid residue';notes='Detected interaction types in saved best poses. Cells count distinct compounds, not interaction strength. Showing up to '+str(min(30,top_n))+' residues; complete raw interactions remain available in reports.'
 layout['xaxis']['title']={'text':label_x};layout['yaxis']['title']={'text':label_y}
 return {'kind':kind,'data':traces,'rows':records,'available':bool(traces),'notes':notes,'x_label':label_x,'y_label':label_y,'layout':layout,'protocol':json.loads(chosen),'display_limit':top_n}

def docking_network(records,protocol,limit,protein=None):
 """Radial score map; geometry is a documented score transform, never Å."""
 tid=protein or min(r['protein_id'] for r in records)
 records=[dict(r) for r in records if r['protein_id']==tid]
 records.sort(key=lambda r:(r['score'],r['oil'],r['identity']))
 # Shared oil memberships remain explicit, with a bounded readable view.
 omitted=max(0,len(records)-80);records=records[:80];records.sort(key=lambda r:(r['oil'],r['score'],r['identity']))
 minimum=min(r['score'] for r in records);n=len(records);traces=[];groups=defaultdict(list)
 for i,r in enumerate(records):
  radius=1+r['score']-minimum;angle=2*math.pi*i/n+math.pi/2
  r.update(network_radius=radius,network_x=radius*math.cos(angle),network_y=radius*math.sin(angle),network_reference_score=minimum)
  groups[r['oil']].append(r)
 for oil,ps in sorted(groups.items()):
  color=ps[0].get('oil_color',stable_color(oil))
  traces.append({'type':'scatter','mode':'lines','x':[v for p in ps for v in [0,p['network_x'],None]],'y':[v for p in ps for v in [0,p['network_y'],None]],'line':{'color':color,'width':1.7},'opacity':.45,'showlegend':False,'hoverinfo':'skip'})
  traces.append({'type':'scatter','mode':'markers','name':short(oil,26),'x':[p['network_x'] for p in ps],'y':[p['network_y'] for p in ps],'marker':{'size':14,'color':color,'line':{'width':1.5,'color':'white'}},'customdata':[[p['compound'],oil,p['score'],p['pocket'],p['network_radius']] for p in ps],'hovertemplate':'%{customdata[0]}<br>Oil: %{customdata[1]}<br>Score: %{customdata[2]:.3f} kcal/mol<br>Pocket %{customdata[3]}<br>Display radius: %{customdata[4]:.3f}<extra></extra>'})
 target=records[0]['protein'];maximum=max(r['network_radius'] for r in records);extent=maximum+max(1.5,maximum*.55)
 traces.append({'type':'scatter','mode':'markers','name':target,'x':[0],'y':[0],'marker':{'symbol':'diamond','size':28,'color':'#17374e','line':{'width':2,'color':'white'}},'showlegend':False,'hovertemplate':target+'<extra>Protein target</extra>'})
 guides=[]
 for radius in sorted({1,round((1+maximum)/2,2),round(maximum,2)}):
  guides.append({'type':'circle','x0':-radius,'x1':radius,'y0':-radius,'y1':radius,'line':{'color':'#dfe8ed','width':1,'dash':'dot'},'layer':'below'})
 annotations=[]
 if n<=32:
  for side in (-1,1):
   rail=sorted([r for r in records if (1 if r['network_x']>=0 else -1)==side],key=lambda r:r['network_y'])
   for i,r in enumerate(rail):
    y=(2*i/max(1,len(rail)-1)-1)*maximum if len(rail)>1 else 0
    annotations.append({'x':r['network_x'],'y':r['network_y'],'ax':side*(maximum+.45),'ay':y,'xref':'x','yref':'y','axref':'x','ayref':'y','showarrow':True,'arrowhead':0,'arrowwidth':.8,'arrowcolor':'#bac9d2','text':short(r['compound'],19)+f" · {r['score']:.2f}",'font':{'size':11,'color':r.get('oil_color','#17374e')},'xanchor':'left' if side>0 else 'right','bgcolor':'white','borderpad':2})
 notes=f'Protein: {target}. Radius = 1 + (score − {minimum:.3f}); more negative scores lie closer to the target. Equal scores have equal radius. Geometry represents docking score differences in kcal/mol, not molecular distances or affinity. Each oil membership is a separate colored node; hover for compound, score and pocket. Select a protein to switch target.'
 if omitted:notes+=f' {omitted} additional oil memberships are hidden; filter by oil to inspect them.'
 layout={'height':620,'paper_bgcolor':'white','plot_bgcolor':'white','margin':{'l':140,'r':140,'t':45,'b':65},'font':{'family':'Segoe UI, Arial','size':12,'color':'#253b50'},'title':{'text':short(target,70),'font':{'size':16}},'xaxis':{'range':[-extent,extent],'visible':False,'constrain':'domain','ticktext':[]},'yaxis':{'range':[-extent,extent],'visible':False,'scaleanchor':'x','scaleratio':1,'ticktext':[]},'shapes':guides,'annotations':annotations,'legend':{'orientation':'h','y':-.05,'x':0,'font':{'size':11},'maxheight':.15},'hovermode':'closest','uirevision':'Docking Network'}
 return {'kind':'Docking Network','data':traces,'rows':records,'available':True,'notes':notes,'x_label':'','y_label':'','layout':layout,'protocol':json.loads(protocol),'display_limit':limit,'protein_id':tid,'radius_transform':{'offset':1,'reference_score':minimum,'unit':'score difference (kcal/mol), not angstrom'}}

def export_chart(spec,path,dpi=300):
 """Export only the displayed chart, retaining numeric records at full precision."""
 import csv,textwrap
 from pathlib import Path
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 import numpy as np
 from openpyxl import Workbook
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fig,ax=plt.subplots(figsize=(12,max(6,min(14,len(spec['layout']['yaxis']['ticktext'])*.3+2))))
 for t in spec['data']:
  if t['type']=='heatmap':
   matrix=np.array([[np.nan if v is None else v for v in r] for r in t['z']],float);im=ax.imshow(matrix,aspect='auto',cmap='viridis_r' if spec['kind']=='Docking Heatmap' else 'YlGnBu');fig.colorbar(im,ax=ax,label='kcal/mol' if spec['kind']=='Docking Heatmap' else 'Distinct compounds')
  elif t['mode']=='lines':ax.plot(t['x'],t['y'],color=t['line']['color'],linewidth=1,alpha=.45)
  else:
   ax.scatter(t['x'],t['y'],s=160 if t.get('showlegend') is False else 110,color=t['marker']['color'],label=t['name'] if t.get('showlegend',True) else '_nolegend_',alpha=.9,edgecolor='white',linewidth=.6,marker='D' if t['marker'].get('symbol')=='diamond' else 'o')
   if spec['kind']=='Docking Network':
    for x,y,label in zip(t['x'],t['y'],t.get('text',[])):
     if label:ax.annotate(label.replace('<br>','\n'),(x,y),xytext=(0,10 if y>=0 else -10),textcoords='offset points',ha='center',va='bottom' if y>=0 else 'top',fontsize=9)
 for axis,key in [(ax.xaxis,'xaxis'),(ax.yaxis,'yaxis')]:
  if 'tickvals' in spec['layout'][key]:axis.set_ticks(spec['layout'][key]['tickvals']);axis.set_ticklabels(spec['layout'][key]['ticktext'],fontsize=9)
 if spec['kind']=='Bubble Plot':ax.invert_yaxis();ax.legend(loc='upper center',bbox_to_anchor=(.5,-.18),ncols=min(4,len(spec['data'])),fontsize=8)
 if spec['kind']=='Docking Network':
  from matplotlib.patches import Circle
  for s in spec['layout']['shapes']:ax.add_patch(Circle((0,0),s['x1'],fill=False,color='#dfe8ed',linestyle=':',zorder=0))
  for a in spec['layout'].get('annotations',[]):ax.annotate(a['text'],(a['x'],a['y']),xytext=(a['ax'],a['ay']),ha=a['xanchor'],va='center',fontsize=8,color=a['font']['color'],bbox={'facecolor':'white','edgecolor':'none','pad':1},arrowprops={'arrowstyle':'-','color':'#bac9d2','lw':.6})
  ax.set_xlim(spec['layout']['xaxis']['range']);ax.set_ylim(spec['layout']['yaxis']['range']);ax.set_aspect('equal');ax.axis('off');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.03),ncols=3,fontsize=8)
 plt.setp(ax.get_xticklabels(),rotation=25 if spec['kind']=='Interaction Matrix' else 0,ha='right' if spec['kind']=='Interaction Matrix' else 'center')
 ax.set_title(spec['kind']);ax.set_xlabel(spec['x_label']);ax.set_ylabel(spec['y_label']);fig.subplots_adjust(left=.25,bottom=.27,right=.92,top=.94);fig.text(.02,.015,textwrap.fill(spec['notes'],135),fontsize=8)
 for ext in ['.png','.svg','.pdf']:fig.savefig(path.with_suffix(ext),dpi=dpi,bbox_inches='tight')
 plt.close(fig)
 fields=list(dict.fromkeys(k for row in spec['rows'] for k in row));clean=lambda v:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v
 with path.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.writer(f);writer.writerow(fields);writer.writerows([[clean(r.get(k)) for k in fields] for r in spec['rows']])
 book=Workbook();sheet=book.active;sheet.title='Plotted records';sheet.append(fields)
 for r in spec['rows']:
  values=[clean(r.get(k)) for k in fields];sheet.append(["'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v for v in values])
 sheet.freeze_panes='A2';book.save(path.with_suffix('.xlsx'));path.with_suffix('.json').write_text(json.dumps(spec,indent=2,ensure_ascii=False),encoding='utf-8');return path.with_suffix('.png')
