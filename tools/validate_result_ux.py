"""Native visual/interaction checks using real preserved docking results."""
import json,sqlite3,time,os
from pathlib import Path
root=Path('data/validation/result_ux_0_6_1').resolve();root.mkdir(parents=True,exist_ok=True);os.environ['NILEPHYTODOCK_DATA']=str(root/'userdata')
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
from app.gui import Window
source=sqlite3.connect('data/validation/case_study_final/case_study.sqlite');db=sqlite3.connect(root/'study.sqlite');source.backup(db);db.close();source.close()
from database.store import connect
from app.projects import relocate_saved_project
portable=connect(root/'study.sqlite');relocate_saved_project(portable,Path('data/validation/case_study_final/screening/Project_Data/project.nile.sqlite'));portable.close()
app=QApplication([]);w=Window(root/'study.sqlite');w.show();w.resize(1440,960);w.project_id=1
def wait(test,timeout=120):
 until=time.monotonic()+timeout
 while not test():
  app.processEvents();time.sleep(.03)
  if time.monotonic()>until:raise TimeoutError('Result UI check timed out')
def js(view,code):
 result=[];view.page().runJavaScript(code,lambda v:result.append(v));wait(lambda:bool(result),30);return result[0]
def settle():
 end=time.monotonic()+.8
 while time.monotonic()<end:app.processEvents();time.sleep(.025)
wait(lambda:not w.tasks);w.refresh_results();w.nav.setCurrentRow(5);wait(lambda:w.oil_results.result is not None and not w.tasks)
o=w.oil_results;assert len(o.result['oils'])==5 and len(o.result['compounds'])==20
assert o.table.selected() and o.table.selected()['compound']=='Thymol','Default selection must show useful calculated results, not an empty oil.'
index=next(i for i in range(o.oils.count()) if 'Thym' in o.oils.item(i).text());o.oils.setCurrentRow(index);settle();assert o.table.rowCount()>0 and o.table.item(0,0).text()=='1'
selected=o.table.selected();assert selected['compound']=='Thymol';assert not any(k in o.table.keys for k in ['pose_id','error','status'])
w.grab().save(str(root/'oil_results.png'));o.open_selected(True);wait(lambda:js(w.interaction_viewer,'Boolean(window.viewerReady||window.validationError)'))
assert w.nav.currentRow()==12 and w.stack.currentIndex()==12
assert w.interaction_viewer.parentWidget() is not w.diagram.parentWidget()
assert not w.contacts_table.isVisible();settle();w.grab().save(str(root/'dedicated_3d_page.png'))
w.open_three_d_window();child=w.three_d_window;wait(lambda:js(child.viewer,'Boolean(window.viewerReady||window.validationError)'))
state=json.loads(js(child.viewer,'JSON.stringify({error:window.validationError||null,contacts:(window.viewerGeometryAudit||[]).length,canvas:{w:document.getElementById("v").clientWidth,h:document.getElementById("v").clientHeight}})'));assert not state['error'] and state['contacts']>0
assert state['canvas']['w']>child.width()*.9 and state['canvas']['h']>child.height()*.55,state
settle();child.grab().save(str(root/'separate_3d_window.png'));child.activateWindow();child.viewer.setFocus();settle();QTest.keyClick(child.viewer,Qt.Key.Key_F11);settle();assert child.isFullScreen();full=json.loads(js(child.viewer,'JSON.stringify({w:document.getElementById("v").clientWidth,h:document.getElementById("v").clientHeight})'));assert full['h']>=child.height()*.9,full;child.grab().save(str(root/'fullscreen_3d.png'));QTest.keyClick(child.viewer,Qt.Key.Key_Escape);settle();assert not child.isFullScreen();child.close()
w.nav.setCurrentRow(11);wait(lambda:w.functional_results.group_result is not None and not w.tasks);g=w.functional_results;assert g.group_result['cohort_size']>=10 and g.table.rowCount()>0
assert all(r['top_compounds']<=g.group_result['cohort_size'] and r['contacting_compounds']<=r['top_compounds'] for r in g.group_result['groups'])
settle();w.grab().save(str(root/'functional_groups.png'));g.top.setCurrentIndex(1);wait(lambda:g.group_result is not None and not w.tasks);assert g.group_result['top_n']==5
checks={'actual_project':'3PTB final botanical case','oil_count':5,'unique_structures':20,'selected_best_compound':selected['compound'],'separate_3d_canvas_pixels':state['canvas'],'standalone_contacts_verified':state['contacts'],'full_screen_toggle_verified':True,'functional_group_cohort':g.group_result,'new_default_result_pages_verified':True,'sizes':[]}
for width,height in [(1366,768),(1920,1080)]:
 w.resize(width,height);settle()
 for page,name in [(5,'oil_results'),(11,'functional_groups'),(12,'3d_page')]:
  w.nav.setCurrentRow(page);settle();w.grab().save(str(root/f'{name}_{width}.png'));scroll=w.stack.currentWidget();assert scroll.horizontalScrollBar().maximum()==0,(name,width,scroll.horizontalScrollBar().maximum());checks['sizes'].append({'page':name,'width':width,'height':height,'outer_horizontal_overflow':False})
(root/'verification.json').write_text(json.dumps(checks,indent=2),encoding='utf-8');w.close();app.processEvents();print('Oil results, functional-group summary and independent native 3D window passed',flush=True)
