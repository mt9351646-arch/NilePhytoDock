"""Native WebGL preset and exported-frame checks on a real saved pose."""
import json,time
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
from visualization.viewer import MolecularViewer
from database.store import connect,rows
from scientific.contact_store import ensure_pose_contacts
from PIL import Image
root=Path('data/validation/comprehensive_appearance');root.mkdir(parents=True,exist_ok=True)
app=QApplication([]);view=MolecularViewer();view.resize(1100,850);view.show();db=connect('data/validation/comprehensive_geometry/study.sqlite');pose=rows(db,'SELECT p.*,t.prepared_path FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id JOIN protein_targets t ON t.id=r.protein_id ORDER BY p.id LIMIT 1')[0];contacts=ensure_pose_contacts(db,pose['id']);view.display(pose['prepared_path'],pose['sdf_path'],contacts=contacts,context={'protein':'3PTB','ligand':'Myrcene'})
def wait(test,timeout=90):
 end=time.monotonic()+timeout
 while not test():
  app.processEvents();time.sleep(.025)
  if time.monotonic()>end:raise TimeoutError('Native appearance check timed out')
def settle(seconds=.7):
 end=time.monotonic()+seconds
 while time.monotonic()<end:app.processEvents();time.sleep(.025)
def js(code):
 result=[];view.page().runJavaScript(code,lambda v:result.append(v));wait(lambda:bool(result),20);return result[0]
wait(lambda:bool(js('window.viewerReady')));checks=[]
for preset,background in [('Scientific Classic','#edf3f5'),('High Contrast','#091827'),('Publication Quality','#ffffff')]:
 state=json.loads(js('JSON.stringify(window.setViewerOption("preset",'+json.dumps(preset)+'))'));assert state['background']==background and state['proteinOpacity']>=.85
 assert js("protein.selectedAtoms({}).some(a=>a.style.cartoon && a.style.cartoon.opacity==="+str(state['proteinOpacity'])+")")
 settle();view.grab().save(str(root/(preset.replace(' ','_')+'_controls.png')));saved=[];path=root/(preset.replace(' ','_')+'.png');view.export_png(path,300,1600,1200,lambda ok:saved.append(ok));wait(lambda:bool(saved));assert saved[0]
 im=Image.open(path).convert('RGB');rgb=tuple(int(background[i:i+2],16) for i in (1,3,5));pixels=sum(1 for p in im.getdata() if all(abs(a-b)<3 for a,b in zip(p,rgb)));assert pixels>im.width*im.height*.1
 checks.append({'preset':preset,'actual_style_opacity':state['proteinOpacity'],'background_pixels':pixels,'export_pixels':list(im.size),'state':state});print(preset,'verified',flush=True)
state=json.loads(js('JSON.stringify(window.setViewerOption("proteinOpacity",0.65))'));assert state['proteinOpacity']==.65
js('window.setViewerOption("preset","Scientific Classic");window.setViewerOption("fixedProteinColor",true);window.setViewerOption("cartoonColor","#1a8b90")');assert js("protein.selectedAtoms({})[0].style.cartoon.colorfunc(protein.selectedAtoms({})[0])")=='#1a8b90'
assert not js('window.validationError||null');(root/'verification.json').write_text(json.dumps({'native_presets':checks,'opacity_and_custom_color_apply_to_model':True,'atom_mapping_verified':len(contacts)},indent=2),encoding='utf-8');view.close();db.close();app.processEvents()
