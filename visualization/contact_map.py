"""Compact molecular interaction maps with typed residue nodes and real anchors.

Only the layout changes: the saved ProLIF categories, atom indices and measured
3D geometry remain authoritative. Van der Waals nodes deliberately omit links.
"""
import json,math,re
import xml.etree.ElementTree as ET
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D
from scientific.molecules import read_sdf
from visualization.semantics import PALETTE,INTERACTIONS,residue_color,residue_name,residue_legend
from visualization.interaction_diagram import NS,element,ligand_indices

def tint(color,white=.72):
 rgb=[int(color[i:i+2],16) for i in (1,3,5)]
 return '#'+''.join(f'{round(v*(1-white)+255*white):02x}' for v in rgb)

def diagram(path,contacts,title='',distances=True,types=False,labels=True,residue_mode='Interaction participation',line_style='Accessible',show_residues=True,colors=None):
 palette={**PALETTE,**(colors or {})};original=read_sdf(path,removeHs=False)[0]
 if original is None:raise ValueError('A valid saved ligand is required')
 for atom in original.GetAtoms():atom.SetIntProp('_source_index',atom.GetIdx())
 mol=Chem.RemoveHs(original);rdDepictor.Compute2DCoords(mol)
 mapping={a.GetIntProp('_source_index'):a.GetIdx() for a in mol.GetAtoms()}
 for atom in original.GetAtoms():
  if atom.GetAtomicNum()==1:
   heavy=next((a.GetIdx() for a in atom.GetNeighbors() if a.GetAtomicNum()!=1),None)
   if heavy in mapping:mapping[atom.GetIdx()]=mapping[heavy]
 drawer=rdMolDraw2D.MolDraw2DSVG(760,480);options=drawer.drawOptions();options.clearBackground=False;options.fixedFontSize=25;options.bondLineWidth=2.6;options.padding=.12
 drawer.DrawMolecule(mol);drawer.FinishDrawing()
 coords=np.array([(drawer.GetDrawCoords(i).x,drawer.GetDrawCoords(i).y) for i in range(mol.GetNumAtoms())]);origin=(coords.min(0)+coords.max(0))/2;coords-=origin
 groups={}
 for contact in contacts if show_residues else []:
  indices=tuple(dict.fromkeys(mapping[i] for i in ligand_indices(contact,original.GetNumAtoms()) if i in mapping))
  if indices:groups.setdefault(contact['residue'],[]).append((contact,indices))
 priority={'HBDonor':0,'HBAcceptor':0,'Cationic':1,'Anionic':1,'MetalDonor':2,'MetalAcceptor':2,'FaceToFace':3,'EdgeToFace':3,'PiCation':3,'CationPi':3,'Hydrophobic':4,'VdWContact':5}
 records=[]
 for residue,items in groups.items():
  representatives={}
  for contact,indices in items:
   kind=contact['interaction_type'];previous=representatives.get(kind)
   if previous is None or (contact.get('distance') if contact.get('distance') is not None else math.inf)<(previous[0].get('distance') if previous[0].get('distance') is not None else math.inf):representatives[kind]=(contact,indices)
  anchor=np.mean([coords[list(indices)].mean(0) for _,indices in representatives.values()],axis=0)
  records.append({'residue':residue,'items':items,'representatives':representatives,'anchor':anchor,'priority':min(priority.get(k,6) for k in representatives)})
 records.sort(key=lambda r:(r['priority'],math.atan2(r['anchor'][1],r['anchor'][0]),r['residue']))
 # Search outward from the real contact anchor. Hard constraints keep nodes
 # away from the molecular skeleton and from each other; the cost discourages
 # crossing links. This is a drawing layout, not a projection of protein atoms.
 bonds=[(coords[b.GetBeginAtomIdx()],coords[b.GetEndAtomIdx()]) for b in mol.GetBonds()]
 radius=48.;node_w=108.;node_h=102.;placed=[];segments=[]
 def segment_distance(point,a,b):
  v=b-a;t=np.clip(np.dot(point-a,v)/(np.dot(v,v) or 1),0,1);return np.linalg.norm(point-(a+t*v))
 def cross(a,b,c,d):
  turn=lambda x,y,z:float((y[0]-x[0])*(z[1]-x[1])-(y[1]-x[1])*(z[0]-x[0]))
  return turn(a,b,c)*turn(a,b,d)<0 and turn(c,d,a)*turn(c,d,b)<0
 for record in records:
  anchor=record['anchor'];preferred=math.atan2(anchor[1],anchor[0]) if np.linalg.norm(anchor)>15 else (sum(map(ord,record['residue']))%360)*math.pi/180
  best=None
  for distance in [125,165,205,250,305,370,445,530,630,750,900,1100,1350]:
   for step in range(64):
    angle=preferred+step*math.pi/32;point=anchor+distance*np.array([math.cos(angle),math.sin(angle)])
    if any(abs(point[0]-p[0])<node_w+13 and abs(point[1]-p[1])<node_h+13 for p in placed):continue
    if any(segment_distance(point,a,b)<radius+20 for a,b in bonds) or min(np.linalg.norm(coords-point,axis=1))<radius+25:continue
    penalty=distance+45*(1-math.cos(angle-preferred))
    if record['priority']<5:penalty+=100*sum(cross(anchor,point,a,b) for a,b in segments)+90*sum(cross(anchor,point,a,b) for a,b in bonds)
    if best is None or penalty<best[0]:best=(penalty,point)
   if best is not None and best[0]<distance+90:break
  if best is None:raise ValueError('Cannot place the residue map without overlap')
  record['position']=best[1];placed.append(best[1])
  if record['priority']<5:segments.append((anchor,best[1]))
 bounds=np.vstack([coords]+[np.array([p+[-node_w/2,-node_h/2],p+[node_w/2,node_h/2]]) for p in placed]);lo=bounds.min(0);hi=bounds.max(0)
 categories=list(dict.fromkeys((INTERACTIONS[k][0],palette[k]) for r in records for k in sorted(r['representatives'],key=lambda k:priority.get(k,6))))
 legend_height=85+35*math.ceil(len(categories)/4)+(90 if residue_mode!='Interaction participation' else 0)
 width=math.ceil(max(1000,hi[0]-lo[0]+140));height=math.ceil(max(690,hi[1]-lo[1]+140+legend_height));offset=np.array([(width-lo[0]-hi[0])/2,70-lo[1]])
 # Centre the content vertically when the ligand/contact footprint is small.
 offset[1]+=max(0,(height-legend_height-(hi[1]-lo[1])-140)/2)
 root=ET.Element('{'+NS+'}svg',{'width':str(width),'height':str(height),'viewBox':f'0 0 {width} {height}'});element(root,'rect',width=width,height=height,fill='white')
 heading=element(root,'text',x=width/2,y=30,text_anchor='middle',font_family='Arial',font_size=19,font_weight=600,fill='#183247');heading.text=title[:115];element(heading,'title').text=title
 defs=element(root,'defs');anchors=[];boxes=[];distance_boxes=[]
 # Draw links underneath the molecule and labels. VdW contacts use node-only
 # encoding, matching the legend; their full atom anchors remain in metadata.
 for index,record in enumerate(records):
  node=record['position']+offset;representatives=record['representatives']
  for j,(kind,(contact,indices)) in enumerate(sorted(representatives.items(),key=lambda v:priority.get(v[0],6))):
   anchor=coords[list(indices)].mean(0)+offset;vector=anchor-node;end=node+vector/(np.linalg.norm(vector) or 1)*radius;color=palette.get(kind,'#64748b');visible=kind!='VdWContact'
   anchors.append({'residue':record['residue'],'kind':kind,'ligand_atom_indices':list(indices),'anchor':anchor.tolist(),'distance':contact.get('distance'),'visible_link':visible})
   if not visible:continue
   line=element(root,'line',x1=anchor[0],y1=anchor[1],x2=end[0],y2=end[1],stroke=color,stroke_width=3.5,stroke_dasharray=INTERACTIONS.get(kind,('','','6 4',''))[2] if line_style=='Accessible' else '',stroke_linecap='round')
   element(line,'title').text='; '.join(f"{c.get('protein_atom','')} – {c.get('ligand_atom','')}: {c.get('distance')} Å" for c,_ in record['items'] if c['interaction_type']==kind)
   element(root,'circle',cx=anchor[0],cy=anchor[1],r=4.5,fill=color,stroke='white',stroke_width=1)
   text=(INTERACTIONS.get(kind,(kind,'','',kind))[3] if types else '')+(f" {contact['distance']:.2f} Å" if distances and contact.get('distance') is not None else '')
   if text:
    point=anchor*.35+end*.65+np.array([0,(j-(len(representatives)-1)/2)*22]);text_width=len(text)*7.4+12
    # Keep numeric labels legible even when two interaction categories share
    # an anchor. They are annotations; endpoint positions never change.
    while any(abs(point[0]-p[0])<(text_width+w)/2 and abs(point[1]-p[1])<24 for p,w in distance_boxes):point[1]+=24
    distance_boxes.append((point.copy(),text_width));element(root,'rect',x=point[0]-text_width/2,y=point[1]-12,width=text_width,height=23,rx=4,fill='white',opacity=.94)
    label=element(root,'text',x=point[0],y=point[1]+5,text_anchor='middle',font_family='Arial',font_size=15,fill='#263d4b');label.text=text.strip()
 ligand_group=element(root,'g',transform=f'translate({offset[0]-origin[0]},{offset[1]-origin[1]})')
 for child in ET.fromstring(drawer.GetDrawingText()):ligand_group.append(child)
 for index,record in enumerate(records):
  node=record['position']+offset;kinds=sorted(record['representatives'],key=lambda k:priority.get(k,6));primary=palette.get(kinds[0],'#64748b');fill=tint(primary)
  if residue_mode!='Interaction participation':
   first=record['items'][0][0];metadata=json.loads(first.get('metadata') or '{}');fill=residue_color(residue_name(first),residue_mode,metadata.get('residue_formal_charge'))
  gradient=element(defs,'radialGradient',id='residue_'+str(index),cx='.35',cy='.3',r='.75');element(gradient,'stop',offset='0%',stop_color='#ffffff');element(gradient,'stop',offset='100%',stop_color=fill)
  node_group=element(root,'g');element(node_group,'circle',cx=node[0],cy=node[1],r=radius,fill='url(#residue_'+str(index)+')',stroke=tint(primary,.4),stroke_width=1.3)
  meaningful=[k for k in kinds if k!='VdWContact'] or kinds
  if len({INTERACTIONS.get(k,(k,))[0] for k in meaningful})>1:
   for j,kind in enumerate(meaningful):
    start=2*math.pi*j/len(meaningful)-math.pi/2;end=start+2*math.pi/len(meaningful)-.08;r=radius+3
    element(node_group,'path',d=f'M {node[0]+r*math.cos(start)} {node[1]+r*math.sin(start)} A {r} {r} 0 {int(end-start>math.pi)} 1 {node[0]+r*math.cos(end)} {node[1]+r*math.sin(end)}',stroke=palette.get(kind,primary),stroke_width=3,fill='none')
  element(node_group,'title').text=record['residue']+'; '+ '; '.join(f"{kind}: {contact.get('distance')} Å" for kind,(contact,_) in record['representatives'].items())
  if labels:
   contact=record['items'][0][0];name=residue_name(contact);number=str(contact.get('residue_number') or re.sub(r'^\D+','',record['residue']).split('.')[0]);chain=contact.get('chain') or (record['residue'].split('.')[-1] if '.' in record['residue'] else '')
   label=element(node_group,'text',x=node[0],y=node[1]-5,text_anchor='middle',font_family='Arial',font_size=22,font_weight=600,fill='#253d47');label.text=name
   label=element(node_group,'text',x=node[0],y=node[1]+21,text_anchor='middle',font_family='Arial',font_size=18,fill='#253d47');label.text=(chain+':' if chain else '')+number
  boxes.append([float(node[0]-node_w/2),float(node[1]-node_h/2),node_w,node_h])
 legend_y=height-legend_height+20
 for i,(category,color) in enumerate(categories):
  x=45+(i%4)*(width-90)/4;y=legend_y+(i//4)*35;element(root,'circle',cx=x+10,cy=y-4,r=9,fill=tint(color,.5),stroke=color)
  label=element(root,'text',x=x+28,y=y+2,font_family='Arial',font_size=16,fill='#263d4b');label.text=category
 if residue_mode!='Interaction participation':
  y=legend_y+math.ceil(len(categories)/4)*35+13
  label=element(root,'text',x=45,y=y,font_family='Arial',font_size=14,fill='#526777');label.text='Residue fill: '+residue_mode+'; link colors identify interaction category.'
  for i,(name,color) in enumerate(residue_legend(residue_mode)):
   x=45+(i%6)*(width-90)/6;yy=y+25+(i//6)*22;element(root,'circle',cx=x+5,cy=yy-4,r=5,fill=color);label=element(root,'text',x=x+16,y=yy,font_family='Arial',font_size=12,fill='#526777');label.text=name
 note=element(root,'text',x=width/2,y=height-24,text_anchor='middle',font_family='Arial',font_size=13,fill='#526777');note.text='Schematic layout. VdW contacts: residue nodes only. Other links: one per residue/category; values are minimum measured 3D separations (Å).'
 if not records:note.text='No classified contacts with mappable ligand atoms for this pose.'
 return ET.tostring(root,encoding='unicode'),{'width':width,'height':height,'anchors':anchors,'residue_boxes':boxes,'residues':len(records),'style':'Interaction map','residue_mode':residue_mode,'line_style':line_style,'contact_count':len(contacts),'aggregation':'Minimum-distance link per residue/category. Van der Waals contacts use node-only encoding; every mapped source contact remains in metadata/tooltips and source tables.'}
