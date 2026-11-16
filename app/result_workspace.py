"""Readable oil-first results and a separate functional-group summary."""
from pathlib import Path
from PySide6.QtCore import Qt,QSignalBlocker
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QListWidget,QListWidgetItem,QSplitter,QFileDialog,QHeaderView,QCheckBox
from app.flow_layout import FlowLayout
from database.store import rows,connect

class ResultScope(QWidget):
 def __init__(self,window):
  super().__init__();self.window=window;self.project=None;self.key=None;self.generation=0;self.result=None;root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
  bar=FlowLayout();self.protein=QComboBox();self.pocket=QComboBox();self.protocol=QComboBox()
  self.protein.setMinimumWidth(150);self.pocket.setMinimumWidth(100);self.protocol.setMinimumWidth(220)
  for name,widget in [('Protein',self.protein),('Binding site',self.pocket),('Protocol',self.protocol)]:
   label=QLabel(name);bar.addWidget(label);bar.addWidget(widget)
   if name=='Protocol':self.protocol_label=label
  self.refresh_button=window.button('Refresh results',self.load,bar);root.addLayout(bar)
  self.protein.currentIndexChanged.connect(self.populate_sites);self.pocket.currentIndexChanged.connect(self.scope_changed);self.protocol.currentIndexChanged.connect(self.scope_changed)
 def set_project(self,pid,force=False):
  key=(str(self.window.db_path.resolve()),pid)
  if key==self.key and not force:return
  self.generation+=1;self.key=key;self.project=pid;self.result=None
  with QSignalBlocker(self.protein):
   self.protein.clear()
   if pid:
    for p in rows(self.window.db,'SELECT id,name FROM protein_targets WHERE project_id=? ORDER BY id',(pid,)):self.protein.addItem(p['name'],p['id'])
  self.populate_sites()
 def populate_sites(self,*_):
  with QSignalBlocker(self.pocket):
   self.pocket.clear()
   if self.protein.currentData():
    for p in rows(self.window.db,'SELECT id,rank FROM predicted_pockets WHERE protein_id=? ORDER BY rank',(self.protein.currentData(),)):self.pocket.addItem('Pocket '+str(p['rank']),p['id'])
  with QSignalBlocker(self.protocol):self.protocol.clear()
  self.load()
 def scope_changed(self,*_):self.load()
 def load(self,*_):
  self.generation+=1;generation=self.generation;pid=self.project;protein=self.protein.currentData();pocket=self.pocket.currentData();protocol=self.protocol.currentData();path=self.window.db_path
  if not pid or protein is None or pocket is None:
   self.refresh_button.setEnabled(True);self.result=None;self.clear_result();return
  self.result=None;self.clear_result()
  self.refresh_button.setEnabled(False);self.message.setText('Reading saved results…')
  def work(emit):
   from scientific.result_summary import oil_results
   db=connect(path)
   try:return oil_results(db,pid,protein,pocket,protocol)
   finally:db.close()
  def done(result):
   if generation!=self.generation:return
   self.refresh_button.setEnabled(True);self.result=result
   with QSignalBlocker(self.protocol):
    self.protocol.clear()
    for p in result['protocols']:self.protocol.addItem(p['label'],p['key'])
    for i in range(self.protocol.count()):
     if self.protocol.itemData(i)==result['protocol']:self.protocol.setCurrentIndex(i);break
   self.protocol.setVisible(len(result['protocols'])>1);self.protocol_label.setVisible(len(result['protocols'])>1);self.protocol.setToolTip(result.get('protocol') or '');self.show_result()
  task=self.window.run_task(work,done);task.finished.connect(lambda:self.refresh_button.setEnabled(True) if generation==self.generation else None)
 def clear_result(self):pass
 def show_result(self):pass

class OilResults(ResultScope):
 def __init__(self,window):
  super().__init__(window);root=self.layout();self.message=QLabel('Open a completed study to see the best compounds in each oil.');self.message.setWordWrap(True);self.message.setObjectName('muted');root.addWidget(self.message)
  split=QSplitter();self.oils=QListWidget();self.oils.setMinimumWidth(180);self.oils.setMaximumWidth(300);split.addWidget(self.oils)
  right=QWidget();layout=QVBoxLayout(right);layout.setContentsMargins(16,0,0,0);self.title=QLabel('Choose an oil');self.title.setObjectName('sectionTitle');layout.addWidget(self.title)
  self.best=QLabel();self.best.setWordWrap(True);self.best.setObjectName('sectionTitle');layout.addWidget(self.best)
  self.source=QComboBox();self.source.setMinimumWidth(240);self.source.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon);self.source.setMinimumContentsLength(22);self.limit=QComboBox()
  for text,n in [('Best 5 compounds',5),('Best 3 compounds',3),('Best 10 compounds',10),('All calculated compounds',0)]:self.limit.addItem(text,n)
  filters=FlowLayout();filters.addWidget(QLabel('Sample'));filters.addWidget(self.source);filters.addWidget(self.limit);layout.addLayout(filters)
  from app.gui import Table
  self.table=Table();self.table.verticalHeader().setDefaultSectionSize(52);self.table.empty_message='No approved constituents from this oil have saved results for this site.';layout.addWidget(self.table,1)
  actions=FlowLayout();self.open_3d=window.button('Open compound in 3D',lambda:self.open_selected(True),actions,True);window.button('2D interactions',lambda:self.open_selected(False),actions);window.button('Export this oil',self.export,actions);layout.addLayout(actions)
  self.note=QLabel('Lower docking scores indicate better predicted results within this protein, binding site and protocol. Sample abundances are shown separately.');self.note.setObjectName('muted');self.note.setWordWrap(True);layout.addWidget(self.note)
  split.addWidget(right);split.setStretchFactor(1,1);split.setSizes([230,1000]);root.addWidget(split,1)
  self.oils.currentRowChanged.connect(self.select_oil);self.source.currentIndexChanged.connect(self.show_compounds);self.limit.currentIndexChanged.connect(self.show_compounds);self.table.itemDoubleClicked.connect(lambda *_:self.open_selected(True));self.current_oil=None;self.export_rows=[]
 def clear_result(self):
  self.oils.clear();self.table.populate([]);self.best.clear();self.title.setText('Choose an oil');self.message.setText('Open a study and select a protein with a calculated binding site.')
 def show_result(self):
  previous=self.oils.currentItem().data(Qt.ItemDataRole.UserRole) if self.oils.currentItem() else None
  with QSignalBlocker(self.oils):
   self.oils.clear()
   for oil in self.result['oils']:
    count=len(oil['compounds']);item=QListWidgetItem(oil['oil']+'\n'+(str(count)+' calculated compounds' if count else 'No approved results'));item.setData(Qt.ItemDataRole.UserRole,oil['oil_id']);item.setToolTip(oil['botanical']);item.setSizeHint(__import__('PySide6.QtCore',fromlist=['QSize']).QSize(210,70));self.oils.addItem(item)
   available=[o for o in self.result['oils'] if o['compounds']];default=min(available,key=lambda o:o['compounds'][0]['score'])['oil_id'] if available else None
   index=next((i for i in range(self.oils.count()) if self.oils.item(i).data(Qt.ItemDataRole.UserRole)==(previous or default)),0);self.oils.setCurrentRow(index)
  self.message.setText(f"{len(self.result['oils'])} oils / botanical preparations · {len(self.result['compounds'])} distinct calculated structures. One best pose per compound.")
  self.select_oil()
 def select_oil(self,*_):
  item=self.oils.currentItem();self.current_oil=next((o for o in self.result['oils'] if item and o['oil_id']==item.data(Qt.ItemDataRole.UserRole)),None) if self.result else None
  with QSignalBlocker(self.source):
   self.source.clear();self.source.addItem('All studied samples',None)
   if self.current_oil:
    for p in self.current_oil['profiles']:self.source.addItem(p['name'],p['id'])
  self.show_compounds()
 def show_compounds(self,*_):
  self.export_rows=[]
  if not self.current_oil:self.table.populate([]);self.open_3d.setEnabled(False);return
  oil=self.current_oil;self.title.setText(oil['oil']+'  |  '+oil['botanical'] if oil['oil']!=oil['botanical'] else oil['oil']);profile=self.source.currentData();data=[]
  for p in oil['compounds']:
   obs=[o for o in p['observations'] if profile is None or o['profile_id']==profile]
   if not obs:continue
   values=list(dict.fromkeys(str(o['reported_value'])+' '+(o['reported_unit'] or '') if o['reported_value'] is not None else 'Not quantified' for o in obs))
   label=values[0] if len(values)==1 else str(len(obs))+' source observations'
   data.append({**p,'rank':len(data)+1,'reported_abundance':label,'source_details':'\n'.join(o['profile']+': '+str(o['reported_value'])+' '+(o['reported_unit'] or '') for o in obs),'observations':obs})
  n=self.limit.currentData();data=data[:n] if n else data
  self.table.populate(data,['rank','compound','score','reported_abundance']);self.table.setHorizontalHeaderLabels(['Rank','Compound','Score (kcal/mol)','Reported abundance'])
  self.table.sortItems(0,Qt.SortOrder.AscendingOrder)
  h=self.table.horizontalHeader();h.setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents);h.setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch);h.setSectionResizeMode(2,QHeaderView.ResizeMode.ResizeToContents);h.setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch)
  for i,p in enumerate(data):
   self.table.item(i,3).setToolTip(p['source_details'])
   for o in p['observations']:self.export_rows.append({'oil':oil['oil'],'source_profile':o['profile'],'compound':p['compound'],'rank':p['rank'],'score_kcal_mol':p['score'],'protein':self.protein.currentText(),'binding_site':self.pocket.currentText(),'reported_value':o['reported_value'],'reported_unit':o['reported_unit'],'identity':p['identity']})
  self.open_3d.setEnabled(bool(data));self.best.setText((f"Best result: {data[0]['compound']}   ·   {data[0]['score']:.3f} kcal/mol") if data else 'No approved calculated compounds in this sample')
  if data:self.table.selectRow(0)
 def open_selected(self,three_d=True):
  p=self.table.selected()
  if p:
   self.window._open_separate_after_pose=three_d;self.window.show_pose(p,three_d=three_d)
 def export(self):
  if not self.export_rows:self.window.error('No calculated compounds are available for this selection.');return
  folder=QFileDialog.getExistingDirectory(self,'Export selected oil results')
  if folder:
   from scientific.molecular_analysis import export_tables
   export_tables(self.export_rows,Path(folder)/'oil_best_compounds','Best compounds in the selected oil');self.window.info('Oil results exported to '+folder)

class FunctionalResults(ResultScope):
 def __init__(self,window):
  super().__init__(window);root=self.layout();bar=FlowLayout();self.oil=QComboBox();self.oil.setMinimumWidth(200);self.oil.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon);self.oil.setMinimumContentsLength(18);self.top=QComboBox()
  for label,n in [('Best 10 compounds',10),('Best 5 compounds',5),('Best 20 compounds',20),('All calculated compounds',0)]:self.top.addItem(label,n)
  self.vdw=QCheckBox('Include van der Waals-only contacts');bar.addWidget(QLabel('Oil'));bar.addWidget(self.oil);bar.addWidget(self.top);bar.addWidget(self.vdw);self.analyze_button=window.button('Update group summary',self.analyze,bar,True);root.addLayout(bar)
  self.message=QLabel('Choose a protein to summarize functional groups in its best-scoring oil compounds.');self.message.setWordWrap(True);self.message.setObjectName('muted');root.addWidget(self.message)
  self.headline=QLabel('Functional groups in the best compounds');self.headline.setObjectName('sectionTitle');self.headline.setWordWrap(True);root.addWidget(self.headline)
  from app.gui import Table
  from PySide6.QtWidgets import QTabWidget
  self.tabs=QTabWidget();self.table=Table();self.features=Table();self.tabs.addTab(self.table,'Functional groups');self.tabs.addTab(self.features,'Molecular features');root.addWidget(self.tabs,3)
  self.table.verticalHeader().setDefaultSectionSize(48);self.features.verticalHeader().setDefaultSectionSize(48)
  root.addWidget(QLabel('Compounds supporting the selected group'))
  self.details=Table();root.addWidget(self.details,2)
  actions=FlowLayout();window.button('Open selected compound in 3D',self.open_selected,actions);window.button('Export group summary',self.export,actions);root.addLayout(actions)
  note=QLabel('Frequency describes the best predicted compounds, not a causal effect on affinity. Presence and verified protein contact are counted separately. Score ties are retained.');note.setObjectName('muted');note.setWordWrap(True);root.addWidget(note)
  self.group_result=None;self.oil.currentIndexChanged.connect(self.analyze);self.top.currentIndexChanged.connect(self.analyze);self.vdw.toggled.connect(self.analyze);self.table.itemSelectionChanged.connect(self.select_group);self.features.itemSelectionChanged.connect(self.select_group);self.tabs.currentChanged.connect(self.select_group);self.details.itemDoubleClicked.connect(lambda *_:self.open_selected())
 def clear_result(self):
  self.group_result=None;self.table.populate([]);self.features.populate([]);self.details.populate([]);self.message.setText('Open a study and choose a protein with calculated results.')
 def show_result(self):
  old=self.oil.currentData()
  with QSignalBlocker(self.oil):
   self.oil.clear();self.oil.addItem('All selected oils',None)
   for o in self.result['oils']:self.oil.addItem(o['oil'],o['oil_id'])
   for i in range(self.oil.count()):
    if self.oil.itemData(i)==old:self.oil.setCurrentIndex(i);break
  self.analyze()
 def analyze(self,*_):
  if not self.result:return
  self.generation+=1;generation=self.generation;pid=self.project;protein=self.protein.currentData();pocket=self.pocket.currentData();protocol=self.protocol.currentData();oil=self.oil.currentData();top=self.top.currentData();vdw=self.vdw.isChecked();path=self.window.db_path
  self.analyze_button.setEnabled(False);self.message.setText('Summarizing groups from actual saved structures and verified contacts…')
  self.group_result=None;self.table.populate([]);self.features.populate([]);self.details.populate([]);self.headline.setText('Calculating functional-group summary…')
  def work(emit):
   from scientific.result_summary import group_results
   db=connect(path)
   try:return group_results(db,pid,protein,pocket,top,oil,protocol,vdw)
   finally:db.close()
  def done(result):
   if generation!=self.generation:return
   self.group_result=result;self.analyze_button.setEnabled(True);n=result['cohort_size'];errors=len(result['contact_errors']);self.message.setText(f"{n} distinct top compounds of {result['available_compounds']} calculated · verified contacts for {n-errors}/{n}. "+('Van der Waals contacts included.' if vdw else 'Contact counts exclude van der Waals-only contacts.'))
   for table,key in [(self.table,'groups'),(self.features,'features')]:
    table.populate(result[key],['group','top_compounds','contacting_compounds','best_score']);table.setHorizontalHeaderLabels(['Group / feature','Top compounds','Direct contacts','Best score']);table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
    for i in [1,2,3]:table.horizontalHeader().setSectionResizeMode(i,QHeaderView.ResizeMode.ResizeToContents)
    table.horizontalHeaderItem(1).setToolTip('Distinct top compounds containing this group');table.horizontalHeaderItem(2).setToolTip('Distinct top compounds with verified direct protein contacts; unavailable contact analyses are reported above');table.horizontalHeaderItem(3).setToolTip('Best saved Smina score in kcal/mol; compare within the selected protein, site and protocol')
   groups=result['groups'];leaders=[g['group'] for g in groups if groups and g['top_compounds']==groups[0]['top_compounds']]
   self.headline.setText(('Most common: '+', '.join(leaders)+f"   ·   {groups[0]['top_compounds']}/{n} top compounds") if leaders else 'No conventional functional groups in this selection; see Molecular features.')
   if groups:self.table.selectRow(0)
   elif result['features']:self.tabs.setCurrentIndex(1);self.features.selectRow(0)
   else:self.details.populate([])
  task=self.window.run_task(work,done);task.finished.connect(lambda:self.analyze_button.setEnabled(True) if generation==self.generation else None)
 def select_group(self,*_):
  table=self.table if self.tabs.currentIndex()==0 else self.features;row=table.selected();data=[d for d in self.group_result['details'] if row and d['group']==row['group']] if self.group_result else [];self.details.populate(data,['compound','oils','score','direct_contact'])
  for i in [0,1]:self.details.horizontalHeader().setSectionResizeMode(i,QHeaderView.ResizeMode.Stretch)
  for i in [2,3]:self.details.horizontalHeader().setSectionResizeMode(i,QHeaderView.ResizeMode.ResizeToContents)
  for i in range(self.details.rowCount()):
   item=self.details.item(i,0);d=item.data(Qt.ItemDataRole.UserRole);item.setToolTip('Verified contacts: '+(d['interaction_types'] or 'None / unavailable')+'\nResidues: '+d['residues'])
  if data:self.details.selectRow(0)
 def open_selected(self):
  row=self.details.selected()
  if row:self.window._open_separate_after_pose=True;self.window.show_pose_id(row['pose_id'],True)
 def export(self):
  if not self.group_result or not self.group_result['cohort_size']:self.window.error('No calculated compounds support this summary.');return
  folder=QFileDialog.getExistingDirectory(self,'Export functional group summary')
  if folder:
   from scientific.molecular_analysis import export_tables
   import json
   for key in ['groups','features','details']:
    if self.group_result[key]:export_tables(self.group_result[key],Path(folder)/('best_compounds_'+key),'Functional groups in best compounds')
   (Path(folder)/'functional_group_scope.json').write_text(json.dumps(self.group_result,indent=2),encoding='utf-8');self.window.info('Group summary exported to '+folder)
