"""Minimal three-chart workspace: lazy, bounded, asynchronous read-only queries."""
import json,uuid,sqlite3,time
from pathlib import Path
from PySide6.QtCore import QUrl,QObject,Slot,Signal,QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QComboBox,QSpinBox,QLabel,QPushButton,QFileDialog,QInputDialog,QSizePolicy
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from app.flow_layout import FlowLayout
from app.paths import resource,user_data
from database.store import rows
from visualization.release_charts import CHARTS,chart_spec,export_chart

class SelectionBridge(QObject):
 selected=Signal(str)
 @Slot(str)
 def select(self,value):self.selected.emit(value)

class ChartWorkspace(QWidget):
 def __init__(self,window):
  super().__init__();self.window=window;self.project=None;self.project_key=None;self.spec=None;self.updating=False;self.uid=uuid.uuid4().hex;self.generation=0;self.query_count=0
  root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0);bar=FlowLayout();self.kind=QComboBox();self.kind.addItems(CHARTS);self.kind.setMinimumWidth(170);bar.addWidget(self.kind)
  self.protein=QComboBox();self.profile=QComboBox();self.pocket=QComboBox();self.top=QSpinBox();self.top.setRange(5,50);self.top.setValue(20)
  for label,control in [('Protein',self.protein),('Oil',self.profile),('Site',self.pocket),('Rows',self.top)]:
   text=QLabel(label);bar.addWidget(text);bar.addWidget(control)
   if label=='Site':self.site_label=text
   if isinstance(control,QComboBox):control.setMinimumWidth(110);control.setMaximumWidth(230);control.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon);control.setMinimumContentsLength(12)
  self.protein.setFixedWidth(140);self.profile.setFixedWidth(160);self.pocket.setFixedWidth(120);self.top.setFixedWidth(88)
  self.top.setStyleSheet('QSpinBox {padding:6px 24px 6px 8px;}')
  self.export_button=QPushButton('Export');self.export_button.setToolTip('PNG, SVG, PDF, CSV, XLSX and plotted JSON');self.export_button.clicked.connect(self.export);bar.addWidget(self.export_button);root.addLayout(bar)
  self.web=QWebEngineView();self.web.setMinimumSize(320,220);root.addWidget(self.web,1)
  self.notes=QLabel('Open a completed study to view saved results.');self.notes.setWordWrap(True);self.notes.setMaximumHeight(48);self.notes.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Maximum);self.notes.setObjectName('muted');root.addWidget(self.notes)
  self.details=QLabel();self.details.setWordWrap(True);self.details.hide();root.addWidget(self.details)
  self.channel=QWebChannel(self.web.page());self.bridge=SelectionBridge(self);self.channel.registerObject('selectionBridge',self.bridge);self.web.page().setWebChannel(self.channel);self.bridge.selected.connect(lambda text:(self.details.setText(text[:600]),self.details.show()))
  self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(120);self.timer.timeout.connect(self.render)
  self.protein.currentIndexChanged.connect(self.populate_sites)
  for control in [self.kind,self.profile,self.pocket]:control.currentIndexChanged.connect(self.request_render)
  self.top.valueChanged.connect(self.request_render);self.export_button.setEnabled(False)
 def set_project(self,pid,force=False):
  key=(str(self.window.db_path.resolve()),pid)
  if key==self.project_key and not force:self.request_render();return
  self.generation+=1;self.project=pid;self.project_key=key;self.updating=True;self.spec=None
  self.protein.clear();self.profile.clear();self.protein.addItem('All proteins',None);self.profile.addItem('All oils',None)
  if pid:
   for p in rows(self.window.db,'SELECT id,name FROM protein_targets WHERE project_id=? ORDER BY id',(pid,)):self.protein.addItem(p['name'],p['id'])
   project=self.window.db.execute('SELECT settings FROM analysis_projects WHERE id=?',(pid,)).fetchone();selected=json.loads(project[0]).get('profiles',[]) if project else []
   if selected:
    marks=','.join('?' for _ in selected)
    for p in rows(self.window.db,f'SELECT DISTINCT eo.id,COALESCE(eo.common_name,eo.name) AS name FROM oil_profiles op JOIN essential_oils eo ON eo.id=op.oil_id WHERE op.id IN ({marks}) ORDER BY name',selected):self.profile.addItem(p['name'],p['id'])
  self.populate_sites();self.updating=False
  if pid:self.request_render()
  else:self.web.setHtml('<html lang="en"><body style="font:15px Segoe UI;padding:30px">Open a completed study to view charts.</body></html>');self.export_button.setEnabled(False)
 def populate_sites(self,*_):
  was=self.updating;self.updating=True;self.pocket.clear();self.pocket.addItem('Best saved site',None);tid=self.protein.currentData()
  if tid:
   for p in rows(self.window.db,'SELECT id,rank FROM predicted_pockets WHERE protein_id=? ORDER BY rank',(tid,)):self.pocket.addItem('Pocket '+str(p['rank']),p['id'])
  self.pocket.setVisible(tid is not None);self.site_label.setVisible(tid is not None);self.updating=was;self.request_render()
 def change_kind(self,*_):self.request_render()
 def request_render(self,*_):
  if not self.updating:self.generation+=1;self.export_button.setEnabled(False);self.timer.start()
 def render(self,*_):
  if self.updating or not self.project:return
  generation=self.generation;pid=self.project;kind=self.kind.currentText();protein=self.protein.currentData();oil=self.profile.currentData();pocket=self.pocket.currentData();limit=self.top.value();path=self.window.db_path;self.notes.setText('Loading '+kind+'…');self.details.hide();self.spec=None;self.query_count+=1
  def work(emit):
   start=time.perf_counter();db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
   try:result=chart_spec(db,pid,kind,protein,oil,pocket,limit);result['query_seconds']=time.perf_counter()-start;return result
   finally:db.close()
  def done(spec):
   if generation!=self.generation:return
   self.spec=spec;self.notes.setToolTip(spec['notes']);self.notes.setText(spec['notes'][:235]+('…' if len(spec['notes'])>235 else ''));self.export_button.setEnabled(spec['available'])
   if not spec['available']:self.web.setHtml('<html lang="en"><body style="font:15px Segoe UI;padding:30px">No saved results support this selection.</body></html>');return
   payload=json.dumps(spec,ensure_ascii=True).replace('<','\\u003c');plotly=resource('app','resources','plotly.min.js').as_uri()
   html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><script src="'''+plotly+'''"></script><script src="qrc:///qtwebchannel/qwebchannel.js"></script><style>html,body{height:100%;margin:0;overflow:hidden;background:white}#chart{width:100%;height:100%}</style></head><body><div id="chart"></div><script>window.chartReady=false;const spec='''+payload+''';delete spec.layout.height;spec.layout.autosize=true;let bridge=null;new QWebChannel(qt.webChannelTransport,c=>bridge=c.objects.selectionBridge);Plotly.newPlot('chart',spec.data,spec.layout,{responsive:true,displaylogo:false,scrollZoom:false}).then(()=>{window.chartSpec=spec;window.chartReady=true;document.getElementById('chart').on('plotly_click',e=>{const p=e.points[0];if(bridge)bridge.select(JSON.stringify(p.customdata||{x:p.x,y:p.y,value:p.z}))});});new ResizeObserver(()=>window.Plotly&&Plotly.Plots.resize('chart')).observe(document.getElementById('chart'));</script></body></html>'''
   folder=user_data()/'charts';folder.mkdir(exist_ok=True);file=folder/('release_chart_'+self.uid+'.html');file.write_text(html,encoding='utf-8');self.web.load(QUrl.fromLocalFile(str(file)))
  self.window.run_task(work,done)
 def export(self):
  if not self.spec or not self.spec['available']:return
  folder=QFileDialog.getExistingDirectory(self,'Export selected chart and data')
  if not folder:return
  dpi,ok=QInputDialog.getItem(self,'Figure resolution','PNG DPI',['300','600'],0,False)
  if not ok:return
  spec=self.spec;path=Path(folder)/spec['kind'].replace(' ','_');self.window.run_task(lambda emit:str(export_chart(spec,path,int(dpi))),lambda _:self.window.info('Chart and plotted records exported to '+folder))
