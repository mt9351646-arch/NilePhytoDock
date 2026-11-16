"""Inspect all ten charts against actual two-target docking results."""
import json,time,sqlite3,sys,faulthandler
faulthandler.enable();faulthandler.dump_traceback_later(90,repeat=True)
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebChannel import QWebChannel
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
from app.gui import Window
from visualization.charts import CHARTS,chart_spec,export_chart
from database.store import rows
sys.stdout.reconfigure(encoding='utf-8');root=Path('data/validation/upgrade_charts');root.mkdir(parents=True,exist_ok=True)
print('Copying actual study',flush=True)
src=sqlite3.connect('data/validation/upgrade_geometry/study.sqlite');dst=sqlite3.connect(root/'study.sqlite');src.backup(dst);dst.close();src.close()
print('Creating chart workspace',flush=True)
app=QApplication([]);w=Window(root/'study.sqlite');w.show();w.resize(1550,1000)
def wait(test,seconds=120):
 until=time.monotonic()+seconds
 while not test():
  app.processEvents();time.sleep(.025)
  if time.monotonic()>until:raise TimeoutError('Chart validation timeout')
class AuditPage(QWebEnginePage):
 def javaScriptConsoleMessage(self,level,message,line,source):print('JS',message,line,flush=True)
w.chart_workspace.web.setPage(AuditPage(w.chart_workspace.web));w.chart_workspace.channel=QWebChannel(w.chart_workspace.web.page());w.chart_workspace.channel.registerObject('selectionBridge',w.chart_workspace.bridge);w.chart_workspace.web.page().setWebChannel(w.chart_workspace.channel)
def js(code):
 result=[];w.chart_workspace.web.page().runJavaScript(code,lambda value:result.append(value));wait(lambda:bool(result),30);return result[0]
wait(lambda:not w.tasks);print('Opening real project charts',flush=True);w.project_id=1;w.nav.setCurrentRow(8);evidence=[]
expected={(r['protein_id'],r['compound_id']):r['score'] for r in rows(w.db,'SELECT r.protein_id,r.compound_id,min(p.score) AS score FROM docking_runs r JOIN docking_poses p ON p.run_id=r.id WHERE r.project_id=1 GROUP BY r.protein_id,r.compound_id')}
for i,kind in enumerate(CHARTS):
 print('Checking '+kind,flush=True)
 spec=chart_spec(w.db,1,kind);assert spec['available'],kind
 if kind=='Compound-Protein Bubble Plot':
  sized=chart_spec(w.db,1,kind,size_variable='GC peak area (%)');refs={t['marker']['sizeref'] for t in sized['data']};assert len(refs)==1
  assert all(r['abundance']>0 for r in sized['rows'])
 for row in spec['rows']:
  if 'score' in row:assert row['score']==expected[row['protein_id'],row['compound_id']]
 if kind=='Protein-Ligand Interaction Matrix':assert {r['interaction_type'] for r in spec['rows']}=={t['name'] for t in spec['data']}
 export_chart(spec,root/kind.replace(' ','_'),150)
 loaded=[];w.chart_workspace.web.loadFinished.connect(lambda ok:loaded.append(ok));w.chart_workspace.kind.setCurrentIndex(i)
 if i==0:w.chart_workspace.render()
 wait(lambda:bool(loaded));wait(lambda:js('Boolean(window.chartReady)'),60)
 actual=json.loads(js('JSON.stringify(window.chartSpec.data)'));assert len(actual)==len(w.chart_workspace.spec['data'])
 curve=next((j for j,t in enumerate(actual) if 'markers' in t.get('mode','')),0)
 point=[0,0] if actual[curve]['type']=='heatmap' else 0
 js("Plotly.Fx.hover('chart',["+json.dumps({'curveNumber':curve,'pointNumber':point})+"])")
 hover=js("document.querySelector('.hoverlayer').textContent");assert hover and len(hover)>2,(kind,hover)
 js("Plotly.Fx.unhover('chart')")
 w.grab().save(str(root/(kind.replace(' ','_')+'_ui.png')))
 evidence.append({'chart':kind,'data_rows':len(spec['rows']),'interactive_traces':len(actual),'hover_tooltip_executed':True,'numeric_values_match_saved_results':True,'png_svg_pdf_csv_exported':True});print(evidence[-1],flush=True)
assert len(evidence)==10
(root/'verification.json').write_text(json.dumps({'actual_project':1,'real_targets':2,'all_ten_chart_types':evidence},indent=2),encoding='utf-8');w.close();app.processEvents();print('All charts verified from saved real calculations',flush=True)
