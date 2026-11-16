"""Draw shared, SMARTS-verified functional centres with actual compound examples."""
import math
import xml.etree.ElementTree as ET
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D
from scientific.functional_groups import identify
from visualization.interaction_diagram import element,NS

TEMPLATES={
 'Carboxylic acid/carboxylate':'*C(=O)O','Ester':'*C(=O)O*','Amide':'*C(=O)N',
 'Aldehyde':'*C=O','Ketone':'*C(=O)*','Phenolic hydroxyl':'Oc1ccccc1',
 'Alcohol hydroxyl':'*CO','Ether':'*O*','Amine':'*N','Sulfonyl':'*S(=O)(=O)*',
 'Sulfoxide':'*S(=O)*','Thiol':'*S','Disulfide/polysulfide':'*SS*','Thioether':'*S*'}

def shared_groups(details):
 groups={}
 for key,d in details.items():
  mol=Chem.MolFromSmiles(d['smiles'])
  for name in {g['name'] for g in identify(mol) if g['domain']=='Functional group'}:
   groups.setdefault(name,[]).append(key)
 return [{'name':name,'identities':keys,'count':len(keys),'total':len(details)} for name,keys in sorted(groups.items(),key=lambda v:(-len(v[1]),v[0])) if len(keys)>=2]

def diagram(details,name):
 shared=next((g for g in shared_groups(details) if g['name']==name),None)
 if shared is None:raise ValueError('This functional group is not shared by two selected structures.')
 template=Chem.MolFromSmiles(TEMPLATES[name])
 for atom in template.GetAtoms():
  if atom.GetAtomicNum()==0:atom.SetProp('atomLabel','R')
 molecules=[template];highlights=[[]];legends=['Illustrative functional group']
 for key in shared['identities'][:5]:
  d=details[key];mol=Chem.MolFromSmiles(d['smiles']);molecules.append(mol)
  highlights.append(sorted({i for g in identify(mol) if g['name']==name for i in g['atoms']}))
  label=d['compound'];legends.append(label[:32]+'…' if len(label)>33 else label)
 rows=math.ceil(len(molecules)/3);height=rows*300+125
 drawer=rdMolDraw2D.MolDraw2DSVG(1200,rows*300,400,300);opts=drawer.drawOptions();opts.fixedFontSize=21;opts.legendFontSize=18;opts.bondLineWidth=2.4;opts.padding=.12
 drawer.DrawMolecules(molecules,legends=legends,highlightAtoms=highlights);drawer.FinishDrawing()
 root=ET.Element('{'+NS+'}svg',{'width':'1200','height':str(height),'viewBox':f'0 0 1200 {height}'})
 element(root,'desc').text=name+'; actual compounds: '+', '.join(details[k]['compound'] for k in shared['identities'][:5])
 element(root,'rect',width=1200,height=height,fill='white')
 text=element(root,'text',x=35,y=34,font_family='Segoe UI,Arial',font_size=24,font_weight=600,fill='#17374e');text.text=name
 text=element(root,'text',x=35,y=61,font_family='Segoe UI,Arial',font_size=16,fill='#486177');text.text=f"Shared by {shared['count']} of {shared['total']} unique structures in this analysis. Up to five actual compounds shown; highlighted atoms are functional centres."
 group=element(root,'g',transform='translate(0,80)')
 for child in ET.fromstring(drawer.GetDrawingText()):group.append(child)
 text=element(root,'text',x=35,y=height-15,font_family='Segoe UI,Arial',font_size=14,fill='#486177');text.text='R = substituent. Group illustration is schematic; substitution and protonation may differ. Presence alone does not establish direct contact or activity.'
 return ET.tostring(root,encoding='unicode'),shared
