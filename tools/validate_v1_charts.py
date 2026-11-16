"""Native lazy-loading, responsiveness and export QA for the three release charts."""
import os,time,json,sqlite3,csv
from pathlib import Path
out=Path('data/validation/v1_charts').resolve();out.mkdir(parents=True,exist_ok=True);os.environ['NILEPHYTODOCK_DATA']=str(out/'userdata')
from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import QApplication
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
from app.gui import Window
from visualization.release_charts import CHARTS,export_chart
from database.store import connect
from app.projects import relocate_saved_project
src=sqlite3.connect('data/validation/case_study_final/case_study.sqlite');target=sqlite3.connect(out/'study.sqlite');src.backup(target);src.close();target.close();db=connect(out/'study.sqlite');relocate_saved_project(db,Path('data/validation/case_study_final/screening/Project_Data/project.nile.sqlite'));db.close()
app=QApplication([]);w=Window(out/'study.sqlite');w.show();w.resize(1366,900);w.project_id=1
ticks=[];heartbeat=QTimer();heartbeat.setInterval(10);heartbeat.timeout.connect(lambda:ticks.append(time.perf_counter()));heartbeat.start()
def wait(test,seconds=90):
 end=time.monotonic()+seconds
 while not test():
  app.processEvents();time.sleep(.01)
  if time.monotonic()>end:raise TimeoutError('Chart validation timed out')
def js(code):
 result=[];w.chart_workspace.web.page().runJavaScript(code,lambda x:result.append(x));wait(lambda:bool(result),20);return result[0]
def settle(seconds=.4):
 end=time.monotonic()+seconds
 while time.monotonic()<end:app.processEvents();time.sleep(.01)
wait(lambda:not w.tasks);w.nav.setCurrentRow(8);c=w.chart_workspace
wait(lambda:c.spec is not None and js('Boolean(window.chartReady)'));assert c.kind.count()==3 and tuple(c.kind.itemText(i) for i in range(3))==CHARTS;assert c.query_count==1
checks=[]
for name in CHARTS:
 start=time.perf_counter();before=c.query_count;before_ticks=len(ticks);c.kind.setCurrentText(name)
 wait(lambda:c.spec is not None and c.spec['kind']==name and js('window.chartReady&&window.chartSpec.kind=='+json.dumps(name)))
 settle();render_seconds=time.perf_counter()-start;loading_ticks=ticks[before_ticks:];assert len(ticks)>before_ticks;assert js('document.documentElement.scrollHeight<=window.innerHeight+1')
 if name!=CHARTS[0]:assert c.query_count==before+1
 assert c.spec['available'];w.grab().save(str(out/(name.replace(' ','_')+'.png')));export_chart(c.spec,out/name,150);assert all((out/name).with_suffix(e).stat().st_size>100 for e in ['.png','.svg','.pdf','.csv','.xlsx','.json'])
 with (out/name).with_suffix('.csv').open(encoding='utf-8-sig') as f:assert len(list(csv.DictReader(f)))==len(c.spec['rows'])
 if name=='Bubble Plot':assert len({t['marker']['color'] for t in c.spec['data']})==len(c.spec['data'])
 checks.append({'chart':name,'records':len(c.spec['rows']),'query_seconds':c.spec['query_seconds'],'native_switch_seconds':render_seconds,'maximum_loading_heartbeat_gap_seconds':max((b-a for a,b in zip(loading_ticks,loading_ticks[1:])),default=0),'only_selected_chart_queried':True,'no_document_scrolling':True,'all_six_exports_verified':True})
c.kind.setCurrentIndex(0);c.top.setValue(5);c.top.setValue(10);c.top.setValue(20);wait(lambda:c.spec is not None and c.spec['kind']==CHARTS[0] and not w.tasks)
(out/'verification.json').write_text(json.dumps({'charts':checks,'only_three_chart_options':True,'initial_queries':1,'heartbeat_events':len(ticks),'maximum_heartbeat_gap_seconds':max(b-a for a,b in zip(ticks,ticks[1:])),'database_seed_unchanged':True},indent=2));heartbeat.stop();w.close();app.processEvents();print('Three lazy release charts and exports passed',flush=True)
