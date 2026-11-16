"""Deterministic atom-feature to residue map; distances remain 3D measurements."""
import json,math,textwrap,xml.etree.ElementTree as ET
from collections import defaultdict
from scientific.functional_groups import identify,participating
from scientific.molecules import read_sdf
from visualization.interaction_diagram import element,NS
from visualization.semantics import PALETTE,INTERACTIONS,residue_name,residue_color,residue_legend,CHARGE_NOTE

def diagram(path,contacts,title='',residue_mode='Biochemical class',colors=None,show_distances=True,show_types=True,show_labels=True,line_style='Accessible',show_nodes=True):
 mol=read_sdf(path,removeHs=False)[0];groups=identify(mol);edges=defaultdict(list);features={};residues={};palette={**PALETTE,**(colors or {})}
 for c in contacts:
  meta=json.loads(c['metadata'])
  for group in participating(mol,groups,meta['geometry']['ligand_indices'],c['interaction_type']):
   key=(group['name'],tuple(group['atoms']));features[key]=group;residues[c['residue']]=c;edges[(key,c['residue'],c['interaction_type'])].append(c)
 fs=sorted(features);rs=sorted(residues,key=lambda r:sum(fs.index(key) for key,res,kind in edges if res==r)/sum(1 for key,res,kind in edges if res==r));width=1500;height=max(1050,450+max(len(fs),len(rs))*135);root=ET.Element('{'+NS+'}svg',width=str(width),height=str(height),viewBox=f'0 0 {width} {height}')
 element(root,'rect',width=width,height=height,fill='white');heading=element(root,'text',x=width/2,y=34,text_anchor='middle',font_family='Segoe UI,Arial',font_size=20,fill='#173144');heading.text=title+' | Functional group-residue map'
 left={k:(290,110+i*135) for i,k in enumerate(fs)};right={k:(1220,110+i*135) for i,k in enumerate(rs)}
 labels=[]
 for (key,res,kind),cs in edges.items():
  x,y=left[key];xx,yy=right[res];distance=min(c['distance'] for c in cs);line=element(root,'line',x1=x+210,y1=y,x2=xx-65,y2=yy,stroke=palette.get(kind,'#64748b'),stroke_width=2,stroke_dasharray=INTERACTIONS[kind][2] if line_style=='Accessible' else 'none');t=element(line,'title');t.text=kind+'; '+str(len(cs))+' events; minimum '+str(distance)+' A; ligand source atoms '+str(list(key[1]))
  if show_distances or show_types:
   text=('%.2f A'%distance if show_distances else '')+(' '+kind if show_types else '');labels.append((650+(fs.index(key)%3)*165,y+(yy-y)*.28-8,text,palette.get(kind,'#64748b')))
 placed=[]
 for x,y,text,color in labels:
  label_width=len(text)*6.6+12
  while any(abs(y-yy)<19 and abs(x-xx)<(label_width+ww)/2+4 for xx,yy,ww in placed):y+=20
  placed.append((x,y,label_width))
  # QtSvg does not implement SVG paint-order; separate background and glyphs
  # keep exported PNG labels identical to the readable SVG/browser labels.
  element(root,'rect',x=x-label_width/2,y=y-13,width=label_width,height=18,rx=3,fill='white',fill_opacity=.95)
  label=element(root,'text',x=x,y=y,text_anchor='middle',font_family='Segoe UI,Arial',font_size=12,fill=color);label.text=text
 for key,(x,y) in left.items():
  element(root,'rect',x=x-210,y=y-45,width=420,height=90,rx=12,fill='#e1f2ef',stroke='#218c82');t=element(root,'text',x=x,y=y-14,text_anchor='middle',font_family='Segoe UI,Arial',font_size=16,fill='#173144');t.text=key[0];t=element(root,'text',x=x,y=y+12,text_anchor='middle',font_family='Consolas',font_size=13,fill='#526477');t.text='Source atom indices: '+','.join(map(str,key[1]))
 for res,(x,y) in right.items():
  if show_nodes:element(root,'circle',cx=x,cy=y,r=60,fill=residue_color(residue_name(residues[res]),residue_mode),stroke='#526477')
  if show_nodes and residue_mode=='Interaction participation':
   kinds=sorted({kind for key,residue,kind in edges if residue==res})
   for i,kind in enumerate(kinds):
    circumference=2*math.pi*63;segment=circumference/max(1,len(kinds));element(root,'circle',cx=x,cy=y,r=63,fill='none',stroke=palette[kind],stroke_width=7,stroke_dasharray=f'{segment} {circumference-segment}',stroke_dashoffset=-i*segment,transform=f'rotate(-90 {x} {y})')
  if show_labels:
   t=element(root,'text',x=x,y=y+5,text_anchor='middle',font_family='Segoe UI,Arial',font_size=17,fill='#173144');t.text=res
 kinds=sorted({k for _,_,k in edges})
 for i,kind in enumerate(kinds):
  x=80+(i%5)*285;y=height-330+(i//5)*32;element(root,'line',x1=x,y1=y,x2=x+42,y2=y,stroke=palette.get(kind,'#64748b'),stroke_width=3,stroke_dasharray=INTERACTIONS[kind][2] if line_style=='Accessible' else 'none');t=element(root,'text',x=x+50,y=y+5,font_family='Segoe UI,Arial',font_size=13,fill='#173144');t.text=kind
 t=element(root,'text',x=80,y=height-240,font_family='Segoe UI,Arial',font_size=14,fill='#173144');t.text='Residue fills: '+residue_mode
 for i,(label,fill) in enumerate(residue_legend(residue_mode)):
  x=80+(i%5)*285;y=height-215+(i//5)*28;element(root,'circle',cx=x+8,cy=y,r=7,fill=fill,stroke='#64748b');t=element(root,'text',x=x+22,y=y+5,font_family='Segoe UI,Arial',font_size=12,fill='#173144');t.text=label
 if residue_mode=='Charge':
  for i,line in enumerate(textwrap.wrap(CHARGE_NOTE,175)):
   t=element(root,'text',x=80,y=height-75+i*18,font_family='Segoe UI,Arial',font_size=12,fill='#526477');t.text=line
 note=element(root,'text',x=width/2,y=height-18,text_anchor='middle',font_family='Segoe UI,Arial',font_size=13,fill='#526477');note.text='Atom-centred SMARTS; overlapping molecular features are a separate domain. Link lengths are schematic; distance labels are measured in 3D.'
 return ET.tostring(root,encoding='unicode'),{'width':width,'height':height,'features':len(fs),'residues':len(rs),'contact_count':len(contacts),'style':'Functional group','aggregation':'Feature/residue/category links; all event counts and minimum distances in SVG tooltips'}
