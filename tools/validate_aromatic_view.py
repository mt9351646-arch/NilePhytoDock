"""Verify centroid guides and covalent endpoints on retained real aromatic poses."""
import os,time,json,sqlite3
from pathlib import Path
out=Path('data/validation/v1_0_1_aromatic').resolve();out.mkdir(parents=True,exist_ok=True);os.environ['NILEPHYTODOCK_DATA']=str(out/'userdata')
source=sqlite3.connect('data/validation/v1_0_1_visual/study.sqlite');target=sqlite3.connect(out/'study.sqlite');source.backup(target);source.close();target.close()
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
from app.gui import Window
app=QApplication([]);w=Window(out/'study.sqlite');w.project_id=1;w.show();w.resize(1500,1000)
def wait(test,seconds=90):
 end=time.monotonic()+seconds
 while not test():
  app.processEvents();time.sleep(.01)
  if time.monotonic()>end:raise TimeoutError('Aromatic view timeout')
def js(code):
 result=[];w.interaction_viewer.page().runJavaScript(code,lambda value:result.append(value));wait(lambda:bool(result));return result[0]
try:
 wait(lambda:not w.tasks)
 pose=w.db.execute("SELECT pose_id FROM molecular_interactions WHERE interaction_type='FaceToFace' GROUP BY pose_id ORDER BY count(*) DESC LIMIT 1").fetchone()[0]
 w.show_pose_id(pose,True);wait(lambda:js('!!window.viewerReady'));js('ligandFocus();true')
 audit=json.loads(js('JSON.stringify(window.viewerEndpointAudit)'));assert any(r['proteinFeature']=='ring centroid' or r['ligandFeature']=='ring centroid' for r in audit)
 assert all(r['proteinAtomsVisible'] and r['ligandAtomsVisible'] and r['proteinCovalentContextVisible'] for r in audit)
 saved=[];w.interaction_viewer.export_png(out/'3d-aromatic.png',300,2400,1800,lambda ok:saved.append(ok));wait(lambda:bool(saved));assert saved[0]
 w.grab().save(str(out/'3d-aromatic-workspace.png'));w.nav.setCurrentRow(6);app.processEvents();w.grab().save(str(out/'2d-aromatic-workspace.png'))
 from visualization.interaction_diagram import save_diagram
 svg,layout=w.current_diagram();save_diagram(svg,out/'2d-aromatic',150)
 (out/'verification.json').write_text(json.dumps({'pose_id':pose,'compound':w.viewer_pose['compound'],'contact_endpoint_audit':audit,'2d_layout':layout},indent=2));print('Real aromatic pose, centroid guides, visible covalent endpoints and 2D/3D exports passed',flush=True)
finally:
 while w.tasks:app.processEvents()
 w.close();app.processEvents()
