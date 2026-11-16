"""Check the last SVG refinement and the real native molecular analysis workspace."""
import json,time,xml.etree.ElementTree as ET
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
from app.gui import Window
from database.store import rows
from visualization.functional_map import diagram
from visualization.interaction_diagram import save_diagram
from visualization.semantics import MODES

root=Path('data/validation/final_workspace');root.mkdir(parents=True,exist_ok=True)
app=QApplication([]);w=Window('data/validation/case_study_final/case_study.sqlite');w.show();w.resize(1440,950)
def wait(test):
 end=time.monotonic()+120
 while not test():
  app.processEvents();time.sleep(.025)
  if time.monotonic()>end:raise TimeoutError('Molecular workspace did not finish')
wait(lambda:not w.tasks)
w.project_id=1;w.nav.setCurrentRow(11);m=w.molecular_workspace;m.set_project(1);m.run();wait(lambda:m.result is not None and not w.tasks)
assert len(m.result['compound_details'])==20 and m.export_button.isEnabled()
views=[]
for i in range(4):
 m.view.setCurrentIndex(i);app.processEvents();views.append({'view':m.view.currentText(),'rows':m.table.rowCount()})
assert all(v['rows']>0 for v in views[:3])
m.view.setCurrentIndex(0);app.processEvents();w.grab().save(str(root/'molecular_workspace.png'))
p=rows(w.db,"SELECT p.* FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id JOIN chemical_compounds c ON c.id=r.compound_id WHERE c.name='Thymol' ORDER BY p.score LIMIT 1")[0]
contacts=rows(w.db,'SELECT * FROM molecular_interactions WHERE pose_id=?',(p['id'],));modes=[]
for mode in MODES:
 svg,layout=diagram(p['sdf_path'],contacts,'Thymol | 3PTB | final source',mode)
 parsed=ET.fromstring(svg);assert layout['features'] and layout['residues']
 assert 'Residue fills: '+mode in svg
 if mode=='Interaction participation':
  arcs=[e for e in parsed.iter() if 'stroke-dashoffset' in e.attrib]
  assert arcs and any(float(e.attrib['stroke-dashoffset'])!=0 for e in arcs)
  save_diagram(svg,root/'Functional_group_participation',150)
 modes.append(mode)
(root/'verification.json').write_text(json.dumps({'source':'actual 3PTB final case study','native_worker_analysis_completed':True,'unique_structures':20,'four_views':views,'residue_modes':modes,'segmented_multiple_contact_category_rings':True},indent=2))
w.close();app.processEvents();print('Final functional map and native molecular workspace passed',flush=True)
