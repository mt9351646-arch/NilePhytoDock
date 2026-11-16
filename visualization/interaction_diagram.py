"""Vector, atom-anchored schematic. Display lengths are not physical distances."""
import json,math,re,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D
from scientific.molecules import read_sdf

from visualization.semantics import PALETTE,INTERACTIONS,residue_name,residue_color,residue_legend,CHARGE_NOTE
NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS)
def element(parent,tag,**attrs):return ET.SubElement(parent,'{'+NS+'}'+tag,{k.replace('_','-'):str(v) for k,v in attrs.items()})

def ligand_indices(contact,n):
    data=json.loads(contact.get('metadata') or '{}');indices=data.get('geometry',{}).get('ligand_indices') or data.get('parent_indices',data.get('indices',{})).get('ligand',[])
    indices=[int(i) for i in indices if 0<=int(i)<n]
    if not indices:indices=[int(i)-1 for i in re.findall(r'[A-Za-z]+(\d+)',contact.get('ligand_atom','')) if 0<int(i)<=n]
    return tuple(dict.fromkeys(indices))

def diagram(molecule_path,contacts,title='',distances=True,types=True,labels=True,style='Interaction map',residue_mode='Interaction participation',line_style='Accessible',show_residues=True,colors=None):
    if style=='Interaction map':
        from visualization.contact_map import diagram as contact_map
        return contact_map(molecule_path,contacts,title,distances,types,labels,residue_mode,line_style,show_residues,colors)
    palette={**PALETTE,**(colors or {})}
    original=read_sdf(molecule_path,removeHs=False)[0]
    if original is None:raise ValueError('Invalid ligand diagram template')
    for atom in original.GetAtoms():atom.SetIntProp('_source_index',atom.GetIdx())
    mol=Chem.RemoveHs(original)
    if mol is None:raise ValueError('Invalid ligand diagram template')
    mol=Chem.Mol(mol);AllChem.Compute2DCoords(mol)
    grouped={}
    for c in contacts:
        mapping={a.GetIntProp('_source_index'):a.GetIdx() for a in mol.GetAtoms()}
        for a in original.GetAtoms():
            if a.GetAtomicNum()==1:
                heavy=next((v.GetIdx() for v in a.GetNeighbors() if v.GetAtomicNum()!=1),None)
                if heavy in mapping:mapping[a.GetIdx()]=mapping[heavy]
        indices=tuple(mapping[i] for i in ligand_indices(c,original.GetNumAtoms()) if i in mapping)
        if indices:grouped.setdefault(c['residue'],[]).append((c,indices))
    if not show_residues:grouped={}
    n=len(grouped);width=max(1280,1000+n*10);height=max(860,620+n*22);legend_height=235 if residue_mode!='Amino acid identity' else 340
    mh=350;mw=510;content_height=height-legend_height;ox=(width-mw)/2;oy=(content_height-mh)/2+45
    drawer=rdMolDraw2D.MolDraw2DSVG(mw,mh);opts=drawer.drawOptions();opts.clearBackground=False;opts.padding=.14;opts.fixedFontSize=25;opts.bondLineWidth=2.6;opts.setBackgroundColour((1,1,1,0))
    drawer.DrawMolecule(mol);drawer.FinishDrawing()
    coords=np.array([(drawer.GetDrawCoords(i).x+ox,drawer.GetDrawCoords(i).y+oy) for i in range(mol.GetNumAtoms())]);center=np.array([width/2,oy+mh/2])
    root=ET.Element('{'+NS+'}svg',{'width':str(width),'height':str(height),'viewBox':f'0 0 {width} {height}'})
    element(root,'rect',width=width,height=height,fill='#ffffff')
    heading=element(root,'text',x=width/2,y=35,text_anchor='middle',font_family='Segoe UI,Arial',font_size=20,font_weight=600,fill='#102a43');heading.text=title
    arranged=[]
    for residue,items in grouped.items():
        anchor=np.mean([coords[list(indices)].mean(0) for _,indices in items],axis=0)
        arranged.append((math.atan2(anchor[1]-center[1],anchor[0]-center[0]),residue,items))
    arranged.sort()
    if n:
        angles=np.array([a for a,_,_ in arranged]);base=np.arange(n)*2*np.pi/n
        offsets=np.linspace(-np.pi,np.pi,720)
        offset=min(offsets,key=lambda o:np.sum(1-np.cos(base+o-angles)))
    # Resolve label collisions in two ordered rails. The preferred side follows
    # the real 2D contact anchor; vertical ordering limits line crossings.
    placements={};rails={-1:[],1:[]}
    for angle,residue,items in arranged:
        side=1 if math.cos(angle)>=0 else -1
        kinds={c['interaction_type'] for c,_ in items};boxh=43+19*len(kinds)
        anchor=np.mean([coords[list(indices)].mean(0) for _,indices in items],axis=0)
        rails[side].append((anchor[1],residue,boxh))
    required_height=max([sum(h for _,_,h in rail)+18*max(0,len(rail)-1)+140+legend_height for rail in rails.values()]+[height])
    if required_height>height:
        shift=(required_height-height)/2;coords[:,1]+=shift;center[1]+=shift;oy+=shift;height=required_height
        root.set('height',str(height));root.set('viewBox',f'0 0 {width} {height}');root[0].set('height',str(height))
    for side,rail in rails.items():
        rail.sort();total=sum(h for _,_,h in rail)+18*max(0,len(rail)-1);y=(height-legend_height-total)/2+35
        for _,residue,h in rail:
            placements[residue]=np.array([width/2+side*(mw/2+135),y+h/2]);y+=h+18
    radii={residue:max(90,(31+19*len({c['interaction_type'] for c,_ in items}))*.75) for _,residue,items in arranged}
    if style=='Circular' and n:
        rx,ry=mw/2+165,mh/2+150
        for _ in range(120):
            proposed={residue:np.array([rx*math.cos(base[i]+offset),ry*math.sin(base[i]+offset)]) for i,(_,residue,_) in enumerate(arranged)}
            def overlap(a,b,ra,rb):return abs(a[0]-b[0])<ra+rb+18 and abs(a[1]-b[1])<ra+rb+18
            collision=any(overlap(proposed[a],proposed[b],radii[a],radii[b]) for i,a in enumerate(proposed) for b in list(proposed)[i+1:])
            collision=collision or any(abs(v[0])<mw/2+radii[k]+20 and abs(v[1])<mh/2+radii[k]+20 for k,v in proposed.items())
            if not collision:break
            rx*=1.045;ry*=1.045
        minx=min([-mw/2]+[v[0]-radii[k] for k,v in proposed.items()]);maxx=max([mw/2]+[v[0]+radii[k] for k,v in proposed.items()]);miny=min([-mh/2]+[v[1]-radii[k] for k,v in proposed.items()]);maxy=max([mh/2]+[v[1]+radii[k] for k,v in proposed.items()]);width=math.ceil(max(1180,maxx-minx+80));height=math.ceil(max(650,maxy-miny+140+legend_height));new_center=np.array([width/2-(minx+maxx)/2,70-miny]);delta=new_center-center;coords+=delta;ox+=delta[0];oy+=delta[1];center=new_center
        placements={k:v+center for k,v in proposed.items()};root.set('width',str(width));root.set('height',str(height));root.set('viewBox',f'0 0 {width} {height}');root[0].set('width',str(width));root[0].set('height',str(height));heading.set('x',str(width/2))
    anchors=[];boxes=[]
    for index,(_,residue,items) in enumerate(arranged):
        node=placements[residue]
        representative={}
        for c,indices in items:
            kind=c['interaction_type'];prior=representative.get(kind)
            if prior is None or (c.get('distance') or 999)<(prior[0].get('distance') or 999):representative[kind]=(c,indices)
        kinds=list(representative);boxh=43+19*len(kinds);boxw=228
        if style=='Circular':boxw=boxh=2*radii[residue]
        boxes.append([float(node[0]-boxw/2),float(node[1]-boxh/2),boxw,boxh])
        for j,(kind,(c,indices)) in enumerate(representative.items()):
            anchor=coords[list(indices)].mean(0);target=node+np.array([0,(j-(len(kinds)-1)/2)*18])
            vector=anchor-target;target=target+vector/(np.linalg.norm(vector) or 1)*(radii[residue] if style=='Circular' else min(boxw/2,72))
            color=palette.get(kind,'#88959d')
            pattern=INTERACTIONS.get(kind,('','','2 3',''))[2] if line_style=='Accessible' else ''
            if style=='Circular':
                line=element(root,'line',x1=anchor[0],y1=anchor[1],x2=target[0],y2=target[1],stroke=color,stroke_width=3.4,stroke_dasharray=pattern,opacity=.9)
            else:
                side=1 if node[0]>center[0] else -1;target=np.array([node[0]-side*boxw/2,node[1]+(j-(len(kinds)-1)/2)*18]);bend=(anchor[0]+target[0])/2
                line=element(root,'path',d=f'M {anchor[0]} {anchor[1]} C {bend} {anchor[1]}, {bend} {target[1]}, {target[0]} {target[1]}',fill='none',stroke=color,stroke_width=3.4,stroke_dasharray=pattern,stroke_linecap='round',opacity=.9)
            detail=element(line,'title');detail.text='; '.join(f"{v.get('protein_atom')} to {v.get('ligand_atom')}: {v.get('distance')} A" for v,_ in items if v['interaction_type']==kind)
            element(root,'circle',cx=anchor[0],cy=anchor[1],r=4.2,fill=color,stroke='white',stroke_width=1)
            anchors.append({'residue':residue,'kind':kind,'ligand_atom_indices':list(indices),'anchor':anchor.tolist(),'distance':c.get('distance')})
        first=items[0][0];metadata=json.loads(first.get('metadata') or '{}');fill=residue_color(residue_name(first),residue_mode,metadata.get('residue_formal_charge'))
        if style=='Circular':element(root,'circle',cx=node[0],cy=node[1],r=radii[residue],fill=fill,stroke='#526477',stroke_width=1.4)
        else:
            element(root,'rect',x=node[0]-boxw/2+2,y=node[1]-boxh/2+4,width=boxw,height=boxh,rx=13,fill='#e5eaf0',opacity=.65)
            element(root,'rect',x=node[0]-boxw/2,y=node[1]-boxh/2,width=boxw,height=boxh,rx=13,fill=fill,stroke='#b4c4ce',stroke_width=1.4)
        if residue_mode=='Interaction participation':
            ring_colors=list(dict.fromkeys(palette[k] for k in kinds))
            for k,color in enumerate(ring_colors):
                if style=='Circular':
                    radius=radii[residue]+3;start=2*math.pi*k/len(ring_colors)-math.pi/2;end=2*math.pi*(k+1)/len(ring_colors)-math.pi/2-.03
                    path=f'M {node[0]+radius*math.cos(start)} {node[1]+radius*math.sin(start)} A {radius} {radius} 0 {int(end-start>math.pi)} 1 {node[0]+radius*math.cos(end)} {node[1]+radius*math.sin(end)}';element(root,'path',d=path,fill='none',stroke=color,stroke_width=6)
                else:element(root,'rect',x=node[0]-boxw/2+k*boxw/len(ring_colors),y=node[1]+boxh/2-5,width=boxw/len(ring_colors),height=5,fill=color)
        if labels:
            label_top=node[1]-(31+19*len(kinds))/2 if style=='Circular' else node[1]-boxh/2
            text=element(root,'text',x=node[0],y=label_top+21,text_anchor='middle',font_family='Segoe UI,Arial',font_size=17,font_weight='600',fill='#102a43');text.text=residue
        for j,(kind,(c,indices)) in enumerate(representative.items()):
            label_top=node[1]-(31+19*len(kinds))/2 if style=='Circular' else node[1]-boxh/2
            text=element(root,'text',x=node[0],y=label_top+42+19*j,text_anchor='middle',font_family='Segoe UI,Arial',font_size=14,fill='#203449')
            count=sum(v['interaction_type']==kind for v,_ in items)
            label=INTERACTIONS.get(kind,(kind,'','',kind))[3]
            if style=='Circular' and kind=='VdWContact':label='VdW'
            text.text=(label if types else '')+(f"  {c['distance']:.2f} Å" if distances and c.get('distance') is not None else '')+(f' ({count})' if count>1 else '')
    group=element(root,'g',transform=f'translate({ox},{oy})')
    molecule=ET.fromstring(drawer.GetDrawingText())
    for child in molecule:group.append(child)
    legend_y=height-legend_height+30
    text=element(root,'text',x=35,y=legend_y,font_family='Segoe UI,Arial',font_size=15,font_weight=600,fill='#102a43');text.text='Interaction lines'
    present={a['kind'] for a in anchors};legend=list(dict.fromkeys((v[0],palette[k],v[2]) for k,v in INTERACTIONS.items() if k in present))
    for i,(label,color,pattern) in enumerate(legend):
        x=35+(i%3)*(width-70)/3;y=legend_y+28+(i//3)*25;element(root,'line',x1=x,y1=y-4,x2=x+36,y2=y-4,stroke=color,stroke_width=3,stroke_dasharray=pattern if line_style=='Accessible' else '');text=element(root,'text',x=x+45,y=y,font_family='Segoe UI,Arial',font_size=13,fill='#203449');text.text=label
    y=legend_y+115;text=element(root,'text',x=35,y=y,font_family='Segoe UI,Arial',font_size=15,font_weight=600,fill='#102a43');text.text='Residue fill: '+residue_mode+' (independent of line color)'
    for i,(label,color) in enumerate(residue_legend(residue_mode)):
        columns=5 if residue_mode=='Amino acid identity' else 4;x=35+(i%columns)*(width-70)/columns;yy=y+25+(i//columns)*23;element(root,'circle',cx=x+6,cy=yy-4,r=6,fill=color,stroke='#526477');text=element(root,'text',x=x+18,y=yy,font_family='Segoe UI,Arial',font_size=12,fill='#203449');text.text=label
    note=element(root,'text',x=width/2,y=height-28,text_anchor='middle',font_family='Segoe UI,Arial',font_size=12,fill='#64748b')
    note.text='One link per residue/type; parentheses count contacts; distance is the minimum measured 3D distance. Drawing lengths are schematic.'
    if not n:
        note.text='No classified contacts with mappable ligand atoms for this pose.'
    if residue_mode=='Charge':
        note=element(root,'text',x=width/2,y=height-10,text_anchor='middle',font_family='Segoe UI,Arial',font_size=10,fill='#64748b');note.text=CHARGE_NOTE
    return ET.tostring(root,encoding='unicode'),{'width':width,'height':height,'anchors':anchors,'residue_boxes':boxes,'residues':n,'style':style,'residue_mode':residue_mode,'line_style':line_style,'contact_count':len(contacts),'aggregation':'Minimum-distance connection per residue and interaction type; all contacts retained in SVG tooltips and source table.'}

def save_diagram(svg,path,dpi=300):
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtGui import QImage,QPainter,QGuiApplication
    from PySide6.QtCore import QByteArray,Qt
    global _render_app
    if QGuiApplication.instance() is None:
        _render_app=QGuiApplication([])
        from app.branding import configure_fonts
        configure_fonts()
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.with_suffix('.svg').write_text(svg,encoding='utf-8')
    renderer=QSvgRenderer(QByteArray(svg.encode('utf-8')))
    if not renderer.isValid():raise ValueError('Generated interaction SVG is invalid')
    size=renderer.defaultSize();scale=dpi/96
    image=QImage(round(size.width()*scale),round(size.height()*scale),QImage.Format.Format_ARGB32);image.fill(Qt.GlobalColor.white)
    image.setDotsPerMeterX(round(dpi/0.0254));image.setDotsPerMeterY(round(dpi/0.0254))
    painter=QPainter(image);renderer.render(painter);painter.end()
    if not image.save(str(path.with_suffix('.png'))):raise OSError('Interaction PNG could not be saved')
    return path.with_suffix('.png')
