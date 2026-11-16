"""Independent coordinate checks and real native 3D canvas verification."""
import json,time,sqlite3,sys,math,faulthandler
faulthandler.enable();faulthandler.dump_traceback_later(120,repeat=True)
from pathlib import Path
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEnginePage
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
from app.gui import Window
from database.store import rows
from scientific.contact_store import ensure_pose_contacts
from scientific.geometry import load_receptor,verify_contact
from scientific.molecules import read_sdf
from visualization.interaction_diagram import diagram,save_diagram
from visualization.semantics import MODES

sys.stdout.reconfigure(encoding='utf-8');root=Path('data/validation/comprehensive_geometry');root.mkdir(parents=True,exist_ok=True)
src=sqlite3.connect('data/validation/studio_workflow/screening.sqlite');dst=sqlite3.connect(root/'study.sqlite');src.backup(dst);dst.close();src.close()
app=QApplication([]);w=Window(root/'study.sqlite');w.show();w.resize(1440,950)
class AuditPage(QWebEnginePage):
 def javaScriptConsoleMessage(self,level,message,line,source):print('JS',level,message,line,source,flush=True)
w.interaction_viewer.setPage(AuditPage(w.interaction_viewer))
def wait(test,timeout=120):
 until=time.monotonic()+timeout
 while not test():
  app.processEvents();time.sleep(.025)
  if time.monotonic()>until:raise TimeoutError('Upgrade validation timed out')
def js(code):
 answer=[];w.interaction_viewer.page().runJavaScript(code,lambda v:answer.append(v));wait(lambda:bool(answer),20);return answer[0]
wait(lambda:not w.tasks);evidence=[];total=0;aromatic=0;seen_targets=set();selected=[]
poses=rows(w.db,'SELECT p.*,t.id AS protein_id,t.prepared_path,t.name AS protein,c.name AS compound FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id JOIN protein_targets t ON t.id=r.protein_id JOIN chemical_compounds c ON c.id=r.compound_id ORDER BY t.id,p.id')
for tid in dict.fromkeys(p['protein_id'] for p in poses):selected += [p for p in poses if p['protein_id']==tid][:3]
assert len(selected)>=6
for pose in selected:
 print('Checking actual pose',pose['id'],flush=True)
 contacts=ensure_pose_contacts(w.db,pose['id'],True);protein=load_receptor(pose['prepared_path']);ligand=read_sdf(pose['sdf_path'],removeHs=False)[0];checked=0
 for contact in contacts:
  meta=json.loads(contact['metadata']);pi=meta['geometry']['protein_indices'];li=meta['geometry']['ligand_indices'];pa=np.mean(protein.GetConformer().GetPositions()[pi],axis=0);la=np.mean(ligand.GetConformer().GetPositions()[li],axis=0);dist=float(np.linalg.norm(pa-la));assert abs(dist-contact['distance'])<.003
  assert np.allclose(pa,meta['geometry']['protein_anchor'],atol=.003,rtol=0) and np.allclose(la,meta['geometry']['ligand_anchor'],atol=.003,rtol=0)
  if len(pi)>1 or len(li)>1:aromatic+=1
  if contact['interaction_type'] in ['HBDonor','HBAcceptor']:
   lp=meta['parent_indices']['ligand'];pp=meta['parent_indices']['protein'];donor,di,acceptor,ai=(ligand,lp,protein,pp) if contact['interaction_type']=='HBDonor' else (protein,pp,ligand,lp);d,h=donor.GetConformer().GetPositions()[di[:2]];a=acceptor.GetConformer().GetPositions()[ai[0]];u,v=d-h,a-h;angle=float(np.degrees(np.arccos(np.clip(np.dot(u,v)/np.linalg.norm(u)/np.linalg.norm(v),-1,1))));assert abs(angle-meta['DHA_angle'])<.05
  bad={**contact,'distance':contact['distance']+.2}
  try:verify_contact(protein,ligand,bad)
  except ValueError:pass
  else:raise AssertionError('Distance corruption was accepted')
  changed=__import__('rdkit').Chem.Mol(ligand);changed.GetConformer().SetAtomPosition(li[0],changed.GetConformer().GetAtomPosition(li[0])+__import__('rdkit').Geometry.Point3D(.4,0,0))
  try:verify_contact(protein,changed,contact)
  except ValueError:pass
  else:raise AssertionError('Coordinate corruption was accepted')
  checked+=1
 # Complex reconstruction uses the identical docked heavy-atom coordinates.
 pdb_lig=[line for line in Path(pose['complex_path']).read_text().splitlines() if line.startswith('HETATM') and line[17:20]=='LIG'];assert len(pdb_lig)==ligand.GetNumAtoms()
 assert np.allclose([[float(line[k:k+8]) for k in [30,38,46]] for line in pdb_lig],ligand.GetConformer().GetPositions(),atol=.002,rtol=0)
 print('Coordinate checks passed; loading 3D',len(contacts),flush=True);w.nav.setCurrentRow(6);app.processEvents();loaded=[];w.interaction_viewer.loadFinished.connect(lambda ok:loaded.append(ok));w.interaction_viewer.display(pose['prepared_path'],pose['sdf_path'],contacts=contacts,context={'protein':pose['protein'],'ligand':pose['compound'],'pose':pose['id']});wait(lambda:bool(loaded));print('3D page loaded',loaded,flush=True);wait(lambda:js('Boolean(window.viewerReady || window.validationError)'),90);actual=json.loads(js('JSON.stringify({error:window.validationError||null,audit:window.viewerGeometryAudit,state:window.currentViewerState})'));assert not actual['error'],actual;assert len(actual['audit'])==len(contacts);print('3D coordinates verified',flush=True)
 for a,c in zip(actual['audit'],contacts):assert abs(a['distance']-c['distance'])<.003
 for style in ['Classic','Circular','Functional group']:
  for mode in MODES:
   if style=='Functional group':
    from visualization.functional_map import diagram as fg_diagram
    svg,layout=fg_diagram(pose['sdf_path'],contacts,pose['compound'],mode);boxes=[]
   else:
    svg,layout=diagram(pose['sdf_path'],contacts,pose['compound']+' | '+pose['protein'],style=style,residue_mode=mode);boxes=layout['residue_boxes']
   for i,(x,y,ww,hh) in enumerate(boxes):
    assert x>=0 and y>=45 and x+ww<=layout['width'] and y+hh<=layout['height']-100
    for xx,yy,www,hhh in boxes[i+1:]:assert x+ww<=xx or xx+www<=x or y+hh<=yy or yy+hhh<=y
   if mode=='Biochemical class':save_diagram(svg,root/f'pose_{pose["id"]}_{style}',150)
 if not evidence:
  for preset in ['Scientific Classic','High Contrast','Publication Quality']:
   state=json.loads(js('JSON.stringify(window.setViewerOption("preset",'+json.dumps(preset)+'))'));assert state['preset']==preset and state['proteinOpacity']>=.85
   w.interaction_viewer.grab().save(str(root/('preset_'+preset.replace(' ','_')+'.png')))
  js('window.setViewerOption("preset","Scientific Classic")')
  for representation in ['Cartoon','Ribbon','Backbone','Sticks','Ball and Stick','Lines','Surface','Transparent Surface','Molecular Spheres']:
   print('3D representation',representation,flush=True)
   state=json.loads(js('JSON.stringify(window.setViewerOption("representation",'+json.dumps(representation)+'))'));assert state['representation']==representation
   wait(lambda:js('!window.pendingSurfaces || Boolean(window.validationError)'),60);assert not js('window.validationError||null')
  js('window.setViewerOption("representation","Cartoon")')
  for mode in ['Chain','Secondary structure','Amino acid identity','Polarity','Charge','Hydrophobicity','Interaction participation','B factor']:
   print('3D color',mode,flush=True)
   state=json.loads(js('JSON.stringify(window.setViewerOption("colorMode",'+json.dumps(mode)+'))'));assert state['colorMode']==mode
  assert js('document.getElementById("confidenceOption").disabled')
  for style in ['Sticks','Ball and Stick','Spheres']:assert json.loads(js('JSON.stringify(window.setViewerOption("ligandStyle",'+json.dumps(style)+'))'))['ligandStyle']==style
  js('window.setViewerOption("representation","Cartoon");window.setViewerOption("colorMode","Chain");window.setViewerOption("ligandStyle","Sticks")')
  exported=[];w.interaction_viewer.export_png(root/'real_3d_view.png',300,1600,1200,lambda ok:exported.append(ok));wait(lambda:bool(exported));assert exported[0]
 evidence.append({'pose_id':pose['id'],'protein':pose['protein'],'compound':pose['compound'],'verified_contacts':checked,'renderer_atom_and_feature_coordinates_match':True,'complex_reconstruction_matches_pose':True});total+=checked;print(evidence[-1],flush=True)
assert aromatic>0
result={'real_poses':len(evidence),'real_targets':len({p['protein'] for p in evidence}),'verified_contacts':total,'ring_feature_contacts':aromatic,'negative_coordinate_and_distance_checks':True,'three_diagram_styles_seven_residue_modes_per_pose':True,'three_native_appearance_presets':True,'nine_protein_representations_eight_color_modes_three_ligand_representations':True,'confidence_requires_explicit_source_confirmation':True,'poses':evidence}
(root/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');w.close();app.processEvents();print('Real geometry validation complete',total,flush=True)
