"""Native controls for reproducible functional-group and similarity analysis."""
import json
from pathlib import Path
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QComboBox,QSpinBox,QSplitter,QTextEdit,QFileDialog
from app.flow_layout import FlowLayout
from database.store import rows,connect

class MolecularWorkspace(QWidget):
 def __init__(self,window):
  super().__init__();self.window=window;self.project=None;self.project_key=None;self.generation=0;self.result=None;self.updating=False;root=QVBoxLayout(self);description=QLabel('Molecular Similarity & Functional Group Analysis\nAtom-centred SMARTS and independent structural/site-specific fingerprints from saved poses.');description.setWordWrap(True);root.addWidget(description)
  bar=FlowLayout();self.protein=QComboBox();self.pocket=QComboBox();self.limit=QSpinBox();self.limit.setRange(2,200);self.limit.setValue(100)
  for label,widget in [('Protein',self.protein),('Compatible binding site',self.pocket),('Maximum unique structures',self.limit)]:bar.addWidget(QLabel(label));bar.addWidget(widget)
  window.button('Analyze saved poses',self.run,bar,True);self.export_button=window.button('Export analysis tables',self.export,bar);self.export_button.setEnabled(False);root.addLayout(bar)
  self.view=QComboBox();self.view.addItems(['Shared functional group structures','Functional group-residue associations','Present versus directly participating','Structural clusters','Enrichment (cluster representatives)']);root.addWidget(self.view)
  self.shared=QComboBox();self.shared.currentIndexChanged.connect(self.show_shared_group);root.addWidget(self.shared)
  from app.gui import Table
  from app.diagram_view import DiagramView
  from PySide6.QtWidgets import QStackedWidget
  split=QSplitter();self.canvas=QStackedWidget();self.group_diagram=DiagramView();self.canvas.addWidget(self.group_diagram);self.table=Table();self.canvas.addWidget(self.table);split.addWidget(self.canvas);self.notes=QTextEdit();self.notes.setReadOnly(True);self.notes.setMaximumWidth(300);split.addWidget(self.notes);split.setSizes([1000,250]);root.addWidget(split,1);self.protein.currentIndexChanged.connect(self.populate_sites);self.view.currentIndexChanged.connect(self.show_result);self.pocket.currentIndexChanged.connect(self.invalidate);self.limit.valueChanged.connect(self.invalidate)
 def set_project(self,pid):
  key=(str(self.window.db_path.resolve()),pid)
  if not pid or key==self.project_key:return
  self.project_key=key;self.project=pid;self.invalidate();self.protein.clear()
  for r in rows(self.window.db,'SELECT id,name FROM protein_targets WHERE project_id=?',(pid,)):self.protein.addItem(r['name'],r['id'])
  self.populate_sites()
 def populate_sites(self,*_):
  self.invalidate();self.pocket.clear();tid=self.protein.currentData()
  if tid:
   for r in rows(self.window.db,'SELECT DISTINCT k.id,k.rank FROM predicted_pockets k JOIN docking_runs r ON r.pocket_id=k.id WHERE r.protein_id=? ORDER BY k.rank',(tid,)):self.pocket.addItem('Pocket '+str(r['rank']),r['id'])
 def run(self):
  if not self.project or not self.pocket.currentData():self.window.error('Open a completed project and select a calculated binding site.');return
  self.generation+=1;generation=self.generation;pid,protein,pocket,limit=self.project,self.protein.currentData(),self.pocket.currentData(),self.limit.value()
  def work(emit):
   from scientific.molecular_analysis import analyze
   db=connect(self.window.db_path)
   try:return analyze(db,pid,protein,pocket,limit)
   finally:db.close()
  def done(result):
   if generation!=self.generation:return
   from visualization.shared_groups import shared_groups
   self.result=result;self.export_button.setEnabled(True);self.shared.blockSignals(True);self.shared.clear()
   for group in shared_groups(result['compound_details']):self.shared.addItem(f"{group['name']} — {group['count']} / {group['total']} structures",group['name'])
   if not self.shared.count():self.shared.addItem('No conventional functional group is shared by two selected structures',None)
   self.shared.blockSignals(False);self.show_result()
  self.window.run_task(work,done)
 def invalidate(self,*_):
  self.generation+=1;self.result=None;self.export_button.setEnabled(False);self.table.clearContents();self.table.setRowCount(0);self.group_diagram.scene().clear();self.shared.clear();self.notes.setPlainText('Select the target and binding site, then analyze saved poses.')
 def show_result(self,*_):
  if not self.result:return
  r=self.result;mode=self.view.currentIndex();self.shared.setVisible(mode==0);self.canvas.setCurrentIndex(0 if mode==0 else 1)
  data=r['functional_group_interactions'] if mode==1 else r['presence_vs_participation'] if mode==2 else [{'identity':k,'compound':v['compound'],'cluster':v['cluster'],'scaffold':v['scaffold'],'smiles':v['smiles']} for k,v in r['compound_details'].items()] if mode==3 else [v for s in r['site_cohorts'] for v in s['enrichment']['rows']]
  if mode==0:self.show_shared_group()
  else:self.table.populate(data)
  self.notes.setPlainText(r['interpretation']+'\n\n'+r['chemical_similarity']['method']+'\n\n'+str(r['chemical_similarity']['cluster_count'])+' structural clusters.\n\n'+'\n'.join(s['enrichment']['reason'] for s in r['site_cohorts'])+'\n\nShared-group drawings show conventional functional centres detected in at least two unique structures, not a maximum common substructure or evidence of a shared mechanism. Counts refer to the selected analysis scope.')
 def show_shared_group(self,*_):
  if not self.result:return
  name=self.shared.currentData()
  if not name:
   self.group_diagram.set_svg('<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="400"><text x="35" y="180" font-size="22" font-family="Arial">No shared conventional functional group in this selection.</text></svg>');return
  from visualization.shared_groups import diagram
  self.group_diagram.set_svg(diagram(self.result['compound_details'],name)[0])
 def export(self):
  if not self.result:return
  folder=QFileDialog.getExistingDirectory(self,'Export calculated functional-group and similarity datasets')
  if folder:
   from scientific.molecular_analysis import export_analysis
   try:
    export_analysis(self.result,folder)
    if self.shared.currentData():
     from visualization.shared_groups import diagram
     from visualization.interaction_diagram import save_diagram
     save_diagram(diagram(self.result['compound_details'],self.shared.currentData())[0],Path(folder)/'shared_functional_group',300)
    self.window.info('Molecular analysis exported to '+folder)
   except Exception as error:self.window.error(error)
