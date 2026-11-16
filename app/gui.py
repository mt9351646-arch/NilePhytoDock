import json
import os
import sys
import threading
import time
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QUrl,QSize
from PySide6.QtGui import QColor,QDesktopServices,QPixmap,QFont
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QPushButton,QListWidget,QStackedWidget,QTableWidget,QTableWidgetItem,QFileDialog,QMessageBox,QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QProgressBar,QSplitter,QTextEdit,QCheckBox,QGroupBox,QScrollArea,QInputDialog,QDialog,QDialogButtonBox,QAbstractItemView)
from app.flow_layout import FlowLayout
from app.paths import user_data,resource
from app.workers import Task
from database.store import connect,rows,counts
from scientific.pipeline import DEFAULTS
from scientific.runtime import Runner
from visualization.viewer import MolecularViewer

NAV=['Dashboard','Essential Oil Library','Protein Manager','Binding Site Explorer','Docking Workspace','Oil Results','2D Interactions','Oil Ranking','Analysis & Visualization','Reports','Settings','Functional Groups','3D Viewer']

class FitImage(QLabel):
    def __init__(self,text=''):
        super().__init__(text);self.original_pixmap=None;self.setMinimumSize(260,180);self.setAlignment(Qt.AlignmentFlag.AlignCenter)
    def setPixmap(self,pixmap):
        self.original_pixmap=pixmap;self.fit()
    def fit(self):
        if self.original_pixmap and not self.original_pixmap.isNull():super().setPixmap(self.original_pixmap.scaled(self.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
    def resizeEvent(self,event):super().resizeEvent(event);self.fit()
    def sizeHint(self):return QSize(480,350)

class Table(QTableWidget):
    def __init__(self):
        super().__init__();self.records=[];self.setAlternatingRowColors(True);self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);self.setSortingEnabled(True);self.verticalHeader().hide();self.setWordWrap(False)
        self.setShowGrid(False);self.verticalHeader().setDefaultSectionSize(38);self.empty_message='No records to display.';self.empty_label=QLabel(self.viewport());self.empty_label.setObjectName('tableEmpty');self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter);self.empty_label.setWordWrap(True);self.empty_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents);self.update_empty_state()
    def populate(self,records,columns=None):
        self.setUpdatesEnabled(False);self.blockSignals(True);self.setSortingEnabled(False);self.clear();self.records=records
        self.keys=columns or (list(records[0]) if records else [])
        self.setColumnCount(len(self.keys));self.setHorizontalHeaderLabels([k.replace('_',' ').title() for k in self.keys]);self.setRowCount(len(records))
        for i,row in enumerate(records):
            for j,k in enumerate(self.keys):
                v=row.get(k);item=QTableWidgetItem()
                if isinstance(v,(float,int)):item.setData(Qt.ItemDataRole.DisplayRole,round(v,5) if isinstance(v,float) else v)
                else:item.setText(str(v if v is not None else '—'))
                if j==0:item.setData(Qt.ItemDataRole.UserRole,row)
                item.setToolTip(str(v if v is not None else 'Not available'));self.setItem(i,j,item)
        self.resizeColumnsToContents()
        for c in range(self.columnCount()):self.setColumnWidth(c,min(380,max(85,self.columnWidth(c))))
        self.setSortingEnabled(True);self.blockSignals(False);self.setUpdatesEnabled(True)
        self.update_empty_state()
    def update_empty_state(self):
        self.empty_label.setText(self.empty_message);self.empty_label.setGeometry(20,max(20,self.viewport().height()//2-50),max(50,self.viewport().width()-40),100);self.empty_label.setVisible(self.rowCount()==0)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'empty_label'):self.update_empty_state()
    def selected(self):
        item=self.item(self.currentRow(),0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

class BaseWindow(QMainWindow):
    def __init__(self,db_path=None):
        super().__init__();self.db_path=Path(db_path) if db_path else user_data()/'nilephytodock.sqlite';self.db=connect(db_path);self.protein_files=[];self.project_id=None;self.tasks=[];self.runner=None;self.busy=False;self.health_data={};self.preview_pockets=[];self.preview_protein=None
        self._closing=False;self._pending_tasks=[];self._active_task=None;self._results_revision=None;self._results_loading=False
        self.setWindowTitle('NilePhytoDock');self.resize(1480,940);self.setMinimumSize(640,360);self.setAcceptDrops(True)
        central=QWidget();self.setCentralWidget(central);root=QHBoxLayout(central);root.setContentsMargins(0,0,0,0);root.setSpacing(0)
        sidebar=QWidget();sidebar.setObjectName('sidebar');sidebar.setFixedWidth(250);sl=QVBoxLayout(sidebar);sl.setContentsMargins(16,18,16,16)
        self.sidebar=sidebar
        logo=QLabel();logo.setAlignment(Qt.AlignmentFlag.AlignCenter);logo.setPixmap(QPixmap(str(resource('app','resources','brand','NilePhytoDock-logo.png'))).scaled(150,115,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));sl.addWidget(logo)
        self.sidebar_logo=logo
        brand=QLabel('NilePhytoDock');brand.setObjectName('brand');sl.addWidget(brand);sub=QLabel('MOLECULAR DISCOVERY\nEgyptian essential oils');sub.setObjectName('subbrand');sl.addWidget(sub);sl.addSpacing(12)
        self.sidebar_brand=brand;self.sidebar_subtitle=sub
        self.nav=QListWidget();self.nav.setWordWrap(True);self.nav.setTextElideMode(Qt.TextElideMode.ElideNone);self.nav.addItems(NAV);self.nav.currentRowChanged.connect(self.navigate);sl.addWidget(self.nav);credit=QLabel('Ahmed G Soliman\nMalak Taha\nv0.2.0');credit.setObjectName('subbrand');sl.addWidget(credit)
        self.sidebar_credit=credit
        root.addWidget(sidebar);content=QWidget();root.addWidget(content,1);layout=QVBoxLayout(content);layout.setContentsMargins(30,22,30,20)
        top=QHBoxLayout();self.page_title=QLabel(NAV[0]);self.page_title.setObjectName('pageTitle');top.addWidget(self.page_title);top.addStretch();self.health_label=QLabel('Checking scientific engines…');top.addWidget(self.health_label);layout.addLayout(top)
        self.stack=QStackedWidget();layout.addWidget(self.stack)
        for build in [self.dashboard,self.library,self.proteins,self.pocket_page,self.workspace,self.results,self.interaction_page,self.ranking_page,self.analysis_page,self.reports,self.settings_page,self.molecular_page,self.three_d_page]:
            page=build()
            if build in (self.analysis_page,self.interaction_page,self.molecular_page,self.three_d_page):
                # Visual workspaces fit the available viewport. Their canvases
                # zoom/pan and tables scroll independently.
                self.stack.addWidget(page)
            else:
                page.setMinimumWidth(790);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(page);self.stack.addWidget(scroll)
        self.nav.setCurrentRow(0);self.theme(False);self.refresh()
        self.run_task(lambda emit:__import__('scientific.runtime',fromlist=['health']).health(),self.health_done)
        self.statusBar().showMessage('Published analytical values retain their original units. Docking results are predictions.')
        self.timer=QTimer(self);self.timer.timeout.connect(self.refresh_live);self.timer.start(2500)

    def page(self,description=''):
        w=QWidget();l=QVBoxLayout(w);l.setContentsMargins(0,12,0,0)
        if description:
            label=QLabel(description);label.setWordWrap(True);label.setObjectName('description');l.addWidget(label)
        return w,l
    def button(self,text,fn,layout,primary=False):
        b=QPushButton(text);b.clicked.connect(fn)
        if primary:b.setObjectName('primary')
        layout.addWidget(b);return b
    def navigate(self,i):
        if i<0:return
        self.stack.setCurrentIndex(i);self.page_title.setText(NAV[i])
        if i in [5,7]:self.refresh_results()
    def error(self,text):QMessageBox.warning(self,'NilePhytoDock',str(text))
    def info(self,text):QMessageBox.information(self,'NilePhytoDock',str(text))
    def run_task(self,fn,callback=None,runner=None):
        if self._closing:return None
        task=Task(fn,self,runner);self.tasks.append(task);task.message.connect(self.progress)
        if callback:task.succeeded.connect(lambda result:callback(result) if not self._closing else None)
        task.failed.connect(self.task_failed);task.cancelled.connect(self.task_cancelled);task.finished.connect(lambda:self.task_finished(task))
        self._pending_tasks.append(task);self._start_next_task();return task
    def _start_next_task(self):
        if not self._active_task and self._pending_tasks and not self._closing:
            self._active_task=self._pending_tasks.pop(0);self._active_task.start()
    def task_finished(self,task):
        if task in self.tasks:self.tasks.remove(task)
        if self._active_task is task:self._active_task=None
        task.deleteLater()
        if self._closing:
            if not self.tasks:QTimer.singleShot(0,self.close)
        else:self._start_next_task()
    def task_cancelled(self):
        if self._closing:return
        self.busy=False;self.job_label.setText('Calculation cancelled. Saved results are retained.');self.update_start_state()
    def task_failed(self,text):
        if self._closing:return
        self.busy=False;self.start_button.setEnabled(True);self.error(text);self.refresh()
    def progress(self,text,done,total):
        if self._closing:return
        self.job_label.setText(text);self.job_progress.setRange(0,total or 1);self.job_progress.setValue(done);self.log_view.append(text);self.statusBar().showMessage(text)
    def health_done(self,data):
        self.health_data=data;ok=all(v['ok'] for v in data.values());self.health_label.setText('Engines available' if ok else 'Engine check failed — see Settings');self.health_table.populate([{'component':k,**v} for k,v in data.items()]);self.start_button.setEnabled(ok and not self.busy)

    def dashboard(self):
        w,l=self.page('Egyptian Essential Oils — Automated Molecular Docking and Interaction Analysis')
        self.metrics=QLabel();self.metrics.setObjectName('metrics');self.metrics.setWordWrap(True);l.addWidget(self.metrics)
        intro=QLabel('Screen documented constituents against your protein targets.\n\n1  Select oil profiles in the library.\n2  Import and inspect protein structures.\n3  Configure a binding site and start screening.');intro.setWordWrap(True);l.addWidget(intro)
        bar=FlowLayout();self.button('Open saved project',self.open_project,bar);self.button('View data validation audit',lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(resource('data','validation','database_validation.json')))),bar);bar.addStretch();l.addLayout(bar)
        l.addWidget(QLabel('Previous analyses'));self.projects_table=Table();self.projects_table.itemDoubleClicked.connect(self.select_project);l.addWidget(self.projects_table)
        return w

    def library(self):
        w,l=self.page('Each commercial sample, geographical condition, plant part and analysis method is a separate profile. Headspace profiles are labelled explicitly.')
        bar=FlowLayout();self.search=QLineEdit();self.search.setPlaceholderText('Search species, profile, compound or source');self.search.textChanged.connect(self.filter_library);bar.addWidget(self.search);self.button('Select all profiles',lambda:self.set_all_profiles(True),bar);self.button('Clear selection',lambda:self.set_all_profiles(False),bar);l.addLayout(bar)
        splitter=QSplitter();self.profile_list=QListWidget();self.profile_list.setMinimumWidth(360);self.profile_list.itemChanged.connect(self.update_selection);splitter.addWidget(self.profile_list);self.library_table=Table();splitter.addWidget(self.library_table);splitter.setStretchFactor(1,3);l.addWidget(splitter,1)
        self.library_note=QLabel();self.library_note.setWordWrap(True);l.addWidget(self.library_note);return w
    def selected_profiles(self):return [self.profile_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.profile_list.count()) if self.profile_list.item(i).checkState()==Qt.CheckState.Checked]
    def set_all_profiles(self,selected):
        self.profile_list.blockSignals(True)
        for i in range(self.profile_list.count()):self.profile_list.item(i).setCheckState(Qt.CheckState.Checked if selected else Qt.CheckState.Unchecked)
        self.profile_list.blockSignals(False);self.update_selection()
    def update_selection(self):
        selected=self.selected_profiles();self.selection_label.setText(f'{len(selected)} oil profiles selected · {len(self.protein_files)} proteins imported')
        self.library_note.setText(f'{len(selected)} selected. Published values retain their original units. Headspace, extracts and fatty-acid pools have no oil index. Unresolved structures are excluded from docking.')
    def filter_library(self):
        text=self.search.text().lower()
        self.library_table.populate([r for r in self.library_records if text in ' '.join(str(v) for v in r.values()).lower()],['original_name','reported_value','reported_unit','docking_status','profile','profile_type','species','method','plant_part','sd','value_status','origin','geography_status','annotation_level','structure_status','identity_notes','source_document'])

    def proteins(self):
        w,l=self.page('Drop PDB or mmCIF files here, or import several at once. Original structures are copied unchanged into each screening project.')
        bar=FlowLayout();self.button('Import proteins',self.import_proteins,bar,True);self.button('Retrieve PDB ID',self.retrieve_pdb,bar);self.button('Remove selected',self.remove_protein,bar);self.button('Inspect preparation',self.prepare_preview,bar);bar.addStretch();l.addLayout(bar)
        self.protein_table=Table();self.protein_table.itemSelectionChanged.connect(self.show_protein);l.addWidget(self.protein_table)
        split=QSplitter();self.protein_viewer=MolecularViewer();split.addWidget(self.protein_viewer);self.protein_info=QTextEdit();self.protein_info.setReadOnly(True);split.addWidget(self.protein_info);l.addWidget(split,2);return w
    def import_proteins(self):
        files,_=QFileDialog.getOpenFileNames(self,'Import protein structures','','Proteins (*.pdb *.cif *.mmcif)');self.add_proteins(files)
    def add_proteins(self,files):
        from scientific.proteins import inspect
        errors=[]
        for f in files:
            try:
                inspect(f)
                if str(Path(f).resolve()) not in self.protein_files:self.protein_files.append(str(Path(f).resolve()))
            except Exception as e:errors.append(Path(f).name+': '+str(e))
        self.refresh_proteins();self.update_selection()
        if errors:self.error('\n'.join(errors))
    def refresh_proteins(self):
        from scientific.proteins import inspect
        data=[]
        for f in self.protein_files:
            try:data.append({'filename':Path(f).name,'path':f,**inspect(f)})
            except Exception as e:data.append({'filename':Path(f).name,'path':f,'integrity':str(e)})
        self.protein_table.populate(data,['filename','chains','residues','integrity','ligands','metals'])
    def show_protein(self):
        r=self.protein_table.selected()
        if r:
            self.protein_info.setPlainText(json.dumps(r,ensure_ascii=False,indent=2))
            self.protein_viewer.display(r['path'])
    def remove_protein(self):
        r=self.protein_table.selected()
        if r and r['path'] in self.protein_files:self.protein_files.remove(r['path']);self.refresh_proteins();self.update_selection()
    def retrieve_pdb(self):
        ident,ok=QInputDialog.getText(self,'Retrieve structure','PDB identifier (requires internet):')
        if not ok:return
        from scientific.pdb_retrieval import normalize_id,retrieve
        try:ident=normalize_id(ident)
        except ValueError as error:self.error(error);return
        def get(emit):return retrieve(ident,user_data()/'downloads',emit)
        self.run_task(get,lambda f:self.add_proteins([f]))
    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls():event.acceptProposedAction()
    def dropEvent(self,event):self.add_proteins([u.toLocalFile() for u in event.mimeData().urls() if Path(u.toLocalFile()).suffix.lower() in ['.pdb','.cif','.mmcif']])

    def pocket_page(self):
        w,l=self.page('Inspect real P2Rank predictions. Box dimensions are user-configurable and do not represent measured cavity volumes.')
        bar=FlowLayout();self.button('Predict for selected protein',self.predict_preview,bar,True);self.button('Use selected pocket rank',self.use_pocket,bar);self.button('Export 3D view',lambda:self.export_view(self.pocket_viewer),bar);bar.addStretch();l.addLayout(bar)
        self.pocket_table=Table();self.pocket_table.itemSelectionChanged.connect(self.show_pocket);l.addWidget(self.pocket_table);self.pocket_viewer=MolecularViewer();l.addWidget(self.pocket_viewer,2);return w
    def prepare_preview(self,predict=False):
        r=self.protein_table.selected()
        if not r:self.error('Select a protein in Protein Manager first');return
        settings=self.get_settings()
        def fn(emit):
            from scientific.proteins import prepare
            from scientific.pockets import predict as predict_fn
            folder=user_data()/'previews'/__import__('hashlib').sha256(Path(r['path']).read_bytes()).hexdigest()[:16]
            pdb,pdbqt,meta=prepare(r['path'],folder,settings['keep_waters'],settings['remove_heterogens'],settings['ph'])
            pockets=predict_fn(pdb,folder/'pockets',Runner(),settings['cpu'],settings['box_size']) if predict else []
            return str(pdb),meta,pockets
        self.run_task(fn,self.preview_done)
    def predict_preview(self):self.prepare_preview(True)
    def preview_done(self,result):
        pdb,meta,ps=result;self.preview_protein=pdb;self.preview_pockets=ps;self.protein_viewer.display(pdb);self.protein_info.setPlainText(json.dumps(meta,ensure_ascii=False,indent=2))
        if ps:self.pocket_table.populate(ps,['rank','score','center','size','residues','method']);self.pocket_viewer.display(pdb,pockets=ps);self.nav.setCurrentRow(3)
        else:self.info('Prepared receptor saved. Inspect the geometry and preparation metadata before screening.')
    def show_pocket(self):
        p=self.pocket_table.selected()
        if p and self.preview_protein:self.pocket_viewer.display(self.preview_protein,pockets=[p])
    def use_pocket(self):
        p=self.pocket_table.selected()
        if p:self.pocket_mode.setCurrentText('Manual pocket');self.pocket_rank.setValue(p['rank']);self.nav.setCurrentRow(4)

    def workspace(self):
        w,l=self.page('Screening uses verified local ligand structures. Jobs run sequentially with controlled Smina CPU usage. Pause takes effect between calculations; Cancel stops the active engine.')
        self.selection_label=QLabel();l.addWidget(self.selection_label);form=QFormLayout();self.study_name=QLineEdit('Essential oil screening');form.addRow('Study title',self.study_name)
        self.pocket_mode=QComboBox();self.pocket_mode.addItems(['Automatic','Top N','Manual pocket','Custom box','Reference ligand']);form.addRow('Binding-site mode',self.pocket_mode)
        self.top_n=QSpinBox();self.top_n.setRange(1,20);self.pocket_rank=QSpinBox();self.pocket_rank.setRange(1,999);row=QHBoxLayout();row.addWidget(QLabel('Top N'));row.addWidget(self.top_n);row.addWidget(QLabel('Manual pocket rank'));row.addWidget(self.pocket_rank);form.addRow('Pocket selection',row)
        self.center=[];self.size=[]
        for title,key,values in [('Center X / Y / Z','center',[0,0,0]),('Dimensions X / Y / Z (Å)','size',[22,22,22])]:
            row=QHBoxLayout()
            for v in values:
                box=QDoubleSpinBox();box.setRange(-9999 if key=='center' else 4,9999 if key=='center' else 126);box.setDecimals(3);box.setValue(v);getattr(self,key).append(box);row.addWidget(box)
            form.addRow(title,row)
        self.reference=QLineEdit();self.reference.setPlaceholderText('Exact label from Protein Manager, e.g. BEN A:1');form.addRow('Reference ligand',self.reference)
        from PySide6.QtWidgets import QGridLayout
        row=QGridLayout();self.exhaust=QSpinBox();self.exhaust.setRange(1,256);self.exhaust.setValue(8);self.modes=QSpinBox();self.modes.setRange(1,100);self.modes.setValue(5);self.cpu=QSpinBox();self.cpu.setRange(1,__import__('app.resource_policy',fromlist=['cpu_budget']).cpu_budget());self.cpu.setValue(self.cpu.maximum())
        for index,(label,box) in enumerate([('Exhaustiveness',self.exhaust),('Poses',self.modes),('CPU threads',self.cpu)]):row.addWidget(QLabel(label),index,0);row.addWidget(box,index,1)
        form.addRow('Docking effort',row);self.seed=QSpinBox();self.seed.setRange(1,2147483647);self.seed.setValue(20261029);self.seed.setToolTip('Identical inputs and seed can reproduce identical scores. Change the seed for an independent search.');form.addRow('Random seed',self.seed);self.scoring=QComboBox();self.scoring.addItems(['vina','vinardo']);form.addRow('Smina scoring function',self.scoring)
        self.reuse_cache=QCheckBox('Reuse verified matching calculations');self.reuse_cache.setChecked(True);self.reuse_cache.setToolTip('Disable for fresh calculations in a new study. Resume preserves completed jobs in the same study.');form.addRow(self.reuse_cache)
        row=QHBoxLayout();self.waters=QCheckBox('Retain crystallographic waters');self.ph=QDoubleSpinBox();self.ph.setRange(0,14);self.ph.setValue(7.4);row.addWidget(self.waters);row.addWidget(QLabel('Preparation pH'));row.addWidget(self.ph);form.addRow('Protein preparation',row)
        self.remove_hetero=QLineEdit();self.remove_hetero.setPlaceholderText('Semicolon-separated exact labels. Cofactors/metals are otherwise retained.');form.addRow('Remove bound residues',self.remove_hetero);l.addLayout(form)
        bar=FlowLayout();self.start_button=self.button('Start Screening',self.start_screening,bar,True);self.start_button.setEnabled(False);self.button('Pause / Resume queue',self.pause_screening,bar);self.button('Cancel',self.cancel_screening,bar);self.button('Resume current project',self.resume_screening,bar);bar.addStretch();l.addLayout(bar)
        self.job_label=QLabel('No calculation running');self.job_label.setWordWrap(True);l.addWidget(self.job_label);self.job_progress=QProgressBar();l.addWidget(self.job_progress);self.log_view=QTextEdit();self.log_view.setReadOnly(True);l.addWidget(self.log_view);return w
    def get_settings(self):
        return {**DEFAULTS,'reuse_calculations':self.reuse_cache.isChecked(),'pocket_mode':self.pocket_mode.currentText(),'top_n':self.top_n.value(),'pocket_rank':self.pocket_rank.value(),'center':[x.value() for x in self.center],'box_size':[x.value() for x in self.size],'reference_ligand':self.reference.text().strip(),'exhaustiveness':self.exhaust.value(),'num_modes':self.modes.value(),'seed':self.seed.value(),'cpu':self.cpu.value(),'scoring':self.scoring.currentText(),'keep_waters':self.waters.isChecked(),'ph':self.ph.value(),'remove_heterogens':[x.strip() for x in self.remove_hetero.text().split(';') if x.strip()]}
    def start_screening(self):
        if self.busy:return
        try:
            from scientific.pipeline import create_project
            from scientific.pockets import validate_box
            settings=self.get_settings();validate_box(settings['center'],settings['box_size'])
            if settings['pocket_mode']=='Reference ligand' and not settings['reference_ligand']:raise ValueError('Enter the reference ligand label')
            folder=user_data()/'projects'/time.strftime('%Y%m%d_%H%M%S');self.project_id=create_project(self.db,self.study_name.text().strip() or 'Screening',self.protein_files,self.selected_profiles(),settings,folder)
            self.launch_screening()
        except Exception as e:self.error(e)
    def launch_screening(self):
        self.busy=True;self.start_button.setEnabled(False);self.runner=Runner();pid=self.project_id;db_path=self.db_path
        def fn(emit):
            from scientific.pipeline import run_project
            db=connect(db_path)
            try:return run_project(db,pid,self.runner,emit)
            finally:db.close()
        self.run_task(fn,self.screening_done,runner=self.runner)
    def screening_done(self,result):
        self.busy=False;self.start_button.setEnabled(all(v['ok'] for v in self.health_data.values()));self.refresh();self.refresh_results();self.info(f"Screening finished. {result['processed']} jobs processed; {result['failures']} failures. Fresh: {result.get('calculated',0)}; verified cache: {result.get('reused',0)}; resumed: {result.get('resumed',0)}. Review statuses and coverage before interpretation.");self.nav.setCurrentRow(5)
    def resume_screening(self):
        if self.busy:return
        if self.project_id:self.launch_screening()
        else:self.error('Open or select a project on the Dashboard first')
    def pause_screening(self):
        if self.runner:
            if self.runner.paused.is_set():self.runner.paused.clear();self.job_label.setText('Queue resumed')
            else:self.runner.paused.set();self.job_label.setText('Queue will pause after the active calculation')
    def cancel_screening(self):
        if self.runner:self.runner.cancelled.set()
        for task in list(self.tasks):task.cancel()
        for task in self._pending_tasks:
            self.tasks.remove(task);task.deleteLater()
        self._pending_tasks.clear();self.job_label.setText('Cancelling active work…')

    def results(self):
        w,l=self.page('Scores are kcal/mol for the selected Vina-family scoring function. Compare compounds within the same protein and protocol. Double-click a pose to inspect its interactions.')
        bar=FlowLayout();self.result_filter=QLineEdit();self.result_filter.setPlaceholderText('Filter protein, compound, pocket, status or oil');self.result_filter.textChanged.connect(self.filter_results);bar.addWidget(self.result_filter);self.button('Save project copy',self.save_project,bar);self.button('Export results and report',self.export_report,bar);l.addLayout(bar);self.results_table=Table();self.results_table.itemDoubleClicked.connect(self.open_interaction);l.addWidget(self.results_table);return w
    def filter_results(self):
        q=self.result_filter.text().lower();self.results_table.populate([r for r in getattr(self,'result_records',[]) if q in ' '.join(str(v) for v in r.values()).lower()],['protein','compound','pocket','pose','score','status','interaction_count','oil_profiles','error'])

    def interaction_page(self):
        w,l=self.page('Contacts use ProLIF chemical typing and geometric rules. No classified contacts is a valid result. Interaction failures are shown in the run status.')
        bar=FlowLayout();self.pose_label=QLabel('Select a pose in Screening Results');bar.addWidget(self.pose_label);bar.addStretch();self.button('Export 2D PNG/SVG and PyMOL script',self.export_interaction,bar);self.button('Export 3D PNG',lambda:self.export_view(self.interaction_viewer),bar);l.addLayout(bar)
        split=QSplitter();self.interaction_viewer=MolecularViewer();split.addWidget(self.interaction_viewer);self.diagram=FitImage('No pose selected');split.addWidget(self.diagram);l.addWidget(split,2);self.contacts_table=Table();self.contacts_table.setMinimumHeight(180);l.addWidget(self.contacts_table);self.current_pose=None;return w
    def open_interaction(self,*_):
        row=self.results_table.selected()
        if not row or not row.get('pose_id'):self.error('Select a successfully calculated pose');return
        self.current_pose=row['pose_id'];contacts=rows(self.db,'SELECT * FROM molecular_interactions WHERE pose_id=?',(self.current_pose,));self.contacts_table.populate(contacts,['residue','chain','residue_number','interaction_type','protein_atom','ligand_atom','distance','angle','method']);self.interaction_viewer.display(row['prepared_path'],row['sdf_path'],contacts=contacts);self.pose_label.setText(f"{row['compound']} · {row['protein']} · pose {row['pose']}")
        from visualization.figures import export_pose
        image=Path(row['sdf_path']).parent/f'interactions_pose_{row["pose"]}.png'
        if not image.exists():export_pose(self.db,self.current_pose,image.parent)
        self.diagram.setPixmap(QPixmap(str(image)))
        self.nav.setCurrentRow(6)
    def export_interaction(self):
        if not self.current_pose:self.error('Select a pose first');return
        folder=QFileDialog.getExistingDirectory(self,'Export interaction figures')
        if not folder:return
        dpi,ok=QInputDialog.getItem(self,'Figure resolution','PNG DPI',['300','600'],0,False)
        if ok:
            from visualization.figures import export_pose
            export_pose(self.db,self.current_pose,folder,int(dpi));self.info('Interaction PNG, SVG and PyMOL script exported.')
    def export_view(self,viewer):
        path,_=QFileDialog.getSaveFileName(self,'Export 3D viewport','','PNG (*.png)')
        if path:viewer.export_png(path)

    def ranking_page(self):
        w,l=self.page('Oil index = Σ(published peak area × target-specific docking percentile) / Σ(screened peak area). Higher index means higher computational priority. Coverage below 70% is flagged. Headspace and extracted oils remain distinct profiles.')
        self.ranking_table=Table();l.addWidget(self.ranking_table);bar=FlowLayout();self.button('Configure multi-target weights',self.target_weights,bar);self.button('Show combined ranking',self.show_combined,bar);bar.addStretch();l.addLayout(bar);self.combined_table=Table();l.addWidget(self.combined_table);return w
    def target_weights(self):
        if not self.project_id:self.error('Select a project first');return
        ts=rows(self.db,'SELECT id,name FROM protein_targets WHERE project_id=?',(self.project_id,));settings=json.loads(self.db.execute('SELECT settings FROM analysis_projects WHERE id=?',(self.project_id,)).fetchone()[0]);dialog=QDialog(self);dialog.setWindowTitle('Target weights');form=QFormLayout(dialog);spins={}
        for t in ts:
            b=QDoubleSpinBox();b.setRange(0,1000);b.setValue(settings.get('target_weights',{}).get(str(t['id']),1));spins[str(t['id'])]=b;form.addRow(t['name'],b)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);form.addRow(buttons);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
        if dialog.exec():
            weights={t:b.value() for t,b in spins.items()}
            if sum(weights.values())<=0:self.error('At least one target weight must be positive');return
            settings['target_weights']=weights;self.db.execute('UPDATE analysis_projects SET settings=? WHERE id=?',(json.dumps(settings),self.project_id));self.db.commit();self.show_combined()
    def show_combined(self):
        if not self.project_id:return
        from reporting.export import datasets
        self.combined_table.populate(datasets(self.db,self.project_id)[2]['Multi target'])

    def analysis_page(self):
        w,l=self.page('Charts use saved calculation records. Blank cells represent unavailable calculations. Exported figures include PNG and SVG.')
        bar=FlowLayout();self.button('Generate project charts',self.generate_charts,bar,True);self.chart_picker=QComboBox();self.chart_picker.currentTextChanged.connect(self.show_chart);bar.addWidget(self.chart_picker);self.button('Open figure folder',lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(getattr(self,'chart_folder',user_data())))),bar);l.addLayout(bar);self.chart_image=FitImage('Run a screening project to generate charts');l.addWidget(self.chart_image,1);return w
    def generate_charts(self):
        if not self.project_id:self.error('Select a project first');return
        pid=self.project_id;self.chart_folder=user_data()/'figures'/str(pid);db_path=self.db_path
        def fn(emit):
            from visualization.figures import charts
            db=connect(db_path)
            try:return charts(db,pid,self.chart_folder)
            finally:db.close()
        self.run_task(fn,lambda fs:self.chart_picker.addItems([str(f) for f in fs]) if fs else self.info('No calculated values are available for plotting.'))
    def show_chart(self,path):
        if path:self.chart_image.setPixmap(QPixmap(path))

    def reports(self):
        w,l=self.page('Create a scientific report with source references, protocol settings, calculated results, oil priorities, coverage, interactions and limitations.')
        l.addWidget(QLabel('Exports\n\n• Scientific report: PDF and DOCX\n• Complete results: CSV and XLSX\n• Figures: PNG and SVG\n• Reproducibility record: JSON'))
        bar=FlowLayout();self.button('Export report package',self.export_report,bar,True);self.button('Save project copy',self.save_project,bar);self.button('Open saved project',self.open_project,bar);bar.addStretch();l.addLayout(bar);self.report_status=QLabel('Select a saved analysis on the Dashboard or complete a screening run.');self.report_status.setWordWrap(True);l.addWidget(self.report_status);l.addStretch();return w
    def export_report(self):
        if not self.project_id:self.error('Select a project first');return
        folder=QFileDialog.getExistingDirectory(self,'Export scientific report package')
        if not folder:return
        pid=self.project_id;db_path=self.db_path
        def fn(emit):
            from reporting.export import export_all
            db=connect(db_path)
            try:return str(export_all(db,pid,folder))
            finally:db.close()
        self.report_status.setText('Generating report and figures…');self.run_task(fn,lambda p:(self.report_status.setText('Report package saved: '+p),self.info('Report package saved to '+p)))
    def select_project(self,*_):
        r=self.projects_table.selected()
        if r:self.project_id=r['id'];self.refresh_results();self.nav.setCurrentRow(5)
    def save_project(self):
        if not self.project_id:self.error('Select a project first');return
        if self.busy:self.error('Pause or finish screening before saving a project snapshot');return
        folder=QFileDialog.getExistingDirectory(self,'Select parent folder for saved project')
        if not folder:return
        try:
            from app.projects import save_project
            p=save_project(self.db,self.project_id,Path(folder)/f'NilePhytoDock_Project_{self.project_id}_{time.strftime("%H%M%S")}');self.info('Project saved: '+str(p))
        except Exception as e:self.error(e)
    def open_project(self):
        if self.busy:self.error('Finish or cancel the active screening first');return
        path,_=QFileDialog.getOpenFileName(self,'Open saved project','','NilePhytoDock database (*.sqlite)')
        if path:
            try:
                test=connect(path)
                from app.projects import relocate_saved_project
                relocate_saved_project(test,path);self.db.close();self.db=test;self.db_path=Path(path);last=self.db.execute('SELECT id FROM analysis_projects ORDER BY id DESC LIMIT 1').fetchone();self.project_id=last[0] if last else None
                self.chart_workspace.project=None;self.molecular_workspace.project=None;self.molecular_workspace.result=None;self.molecular_workspace.export_button.setEnabled(False);self.refresh();self.refresh_results()
            except Exception as e:self.error(e)

    def settings_page(self):
        w,l=self.page('Scientific components are bundled. Normal screening works offline after ligand preparation. Library maintenance uses PubChem only when explicitly requested below.')
        self.health_table=Table();l.addWidget(self.health_table);bar=FlowLayout();self.button('Recheck engines',lambda:self.run_task(lambda emit:__import__('scientific.runtime',fromlist=['health']).health(),self.health_done),bar);self.button('Resolve missing structures online',self.maintain_library,bar);self.button('Export database audit',self.export_audit,bar);self.button('Open application data',lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(user_data()))),bar);l.addLayout(bar)
        self.dark=QCheckBox('Dark theme');self.dark.toggled.connect(self.theme);l.addWidget(self.dark);label=QLabel('Protein preparation uses a general pH model and does not rebuild missing residues. Retained cofactors/metals and ambiguous stereochemistry require scientific review. Refer to the separate English documentation for the tested scope.');label.setWordWrap(True);l.addWidget(label);l.addStretch();return w
    def maintain_library(self):
        if self.busy:self.error('Finish screening before library maintenance');return
        db_path=self.db_path
        def fn(emit):
            from scientific.ligands import resolve_library
            db=connect(db_path)
            try:return resolve_library(db,user_data()/'compound_library',lambda s:emit(s,0,1))
            finally:db.close()
        self.run_task(fn,lambda r:(self.refresh(),self.info('Library maintenance completed. '+str(r))))
    def export_audit(self):
        folder=QFileDialog.getExistingDirectory(self,'Export complete extraction audit')
        if folder:
            from database.import_documents import audit
            audit(self.db,folder);self.info('Extraction CSV and database validation JSON exported.')

    def refresh(self):
        c=counts(self.db);self.metrics.setText(f"{c['species']} plant species     {c['profiles']} oil profiles     {c['compounds']} compound names\n{c['ready']} docking-ready records ({c['unique_ready']} distinct structures)     {c['compounds']-c['ready']} awaiting review\n{c['records']} source composition records")
        self.projects_table.populate(rows(self.db,'SELECT id,name,created_at,status,folder FROM analysis_projects ORDER BY id DESC'))
        checked=set(self.selected_profiles());self.profile_list.blockSignals(True);self.profile_list.clear()
        from PySide6.QtWidgets import QListWidgetItem
        for p in rows(self.db,'SELECT * FROM oil_profiles ORDER BY name'):
            item=QListWidgetItem(p['name']+(' [headspace]' if p['method']=='HS' else ''));item.setData(Qt.ItemDataRole.UserRole,p['id']);item.setFlags(item.flags()|Qt.ItemFlag.ItemIsUserCheckable);item.setCheckState(Qt.CheckState.Checked if p['id'] in checked else Qt.CheckState.Unchecked);item.setToolTip(f"{p['plant_part']} | {p['origin']}\n{p['notes']}");self.profile_list.addItem(item)
        self.profile_list.blockSignals(False)
        self.library_records=rows(self.db,"SELECT sp.name AS species,p.name AS profile,p.preparation_category,p.method,p.plant_part,pc.original_name,pc.percentage,COALESCE(pc.reported_value,pc.percentage) AS reported_value,COALESCE(pc.reported_unit,CASE WHEN pc.percentage IS NOT NULL THEN 'GC peak area %' ELSE '' END) AS reported_unit,pc.sd,pc.value_status,p.profile_type,p.origin,p.geography_status,pc.annotation_level,pc.docking_eligible,CASE WHEN pc.docking_eligible=0 THEN 'Source identity review - excluded' WHEN s.status='ready' THEN 'Ready' ELSE 'Structure review - excluded' END AS docking_status,COALESCE(s.status,'unresolved') AS structure_status,c.identity_notes,ref.source_document,ref.citation FROM profile_compounds pc JOIN oil_profiles p ON p.id=pc.profile_id JOIN essential_oils o ON o.id=p.oil_id JOIN plant_species sp ON sp.id=o.species_id JOIN chemical_compounds c ON c.id=pc.compound_id LEFT JOIN compound_structures s ON s.compound_id=c.id JOIN scientific_references ref ON ref.id=pc.reference_id")
        self.filter_library();self.update_selection()
    def refresh_live(self):
        # Progress signals update the queue. Detailed results are queried only
        # when a results page is visible, never on the screening/dashboard loop.
        if self.busy and self.nav.currentRow() in (5,7):self.refresh_results()
    def refresh_results(self):
        if not self.project_id or self._results_loading or self._closing:return
        revision=(str(self.db_path.resolve()),self.project_id,self.db.execute('PRAGMA data_version').fetchone()[0],self.db.total_changes)
        if revision==self._results_revision:return
        self._results_loading=True;pid=self.project_id;path=self.db_path
        def work(emit):
            import sqlite3
            from scientific.ranking import project_rankings
            db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
            try:
                records=rows(db,"""SELECT p.id AS pose_id,t.name AS protein,c.name AS compound,k.rank AS pocket,p.rank AS pose,p.score,r.status,r.error,t.prepared_path,p.sdf_path,p.complex_path,(SELECT count(*) FROM molecular_interactions i WHERE i.pose_id=p.id) AS interaction_count,(SELECT group_concat(op.name,'; ') FROM oil_profiles op JOIN profile_compounds pc ON pc.profile_id=op.id WHERE pc.compound_id=c.id) AS oil_profiles FROM docking_runs r JOIN protein_targets t ON t.id=r.protein_id JOIN chemical_compounds c ON c.id=r.compound_id JOIN predicted_pockets k ON k.id=r.pocket_id LEFT JOIN docking_poses p ON p.run_id=r.id WHERE r.project_id=? ORDER BY p.score LIMIT 2000""",(pid,))
                names={r['id']:r['name'] for r in rows(db,'SELECT id,name FROM oil_profiles')};targets={r['id']:r['name'] for r in rows(db,'SELECT id,name FROM protein_targets WHERE project_id=?',(pid,))}
                ranking=[{'protein':targets[t],'profile':names[r['profile_id']],**r} for t,rs in project_rankings(db,pid).items() for r in rs]
                return records,ranking
            finally:db.close()
        def done(result):
            if self.project_id!=pid or self.db_path!=path:return
            self._results_revision=revision;self.result_records,ranking=result;self.filter_results()
            self.ranking_table.populate(ranking,['protein','profile','best_constituent_score','index','screened_peak_area_percent','reported_peak_area_percent','fraction_of_reported','sensitivity_min','sensitivity_max','sensitivity_rank_best','sensitivity_rank_worst','warning'])
            if len(self.result_records)==2000:self.statusBar().showMessage('Detailed view limited to 2,000 poses. Exports include all results.')
        task=self.run_task(work,done)
        if task:task.finished.connect(lambda:setattr(self,'_results_loading',False))
    def theme(self,dark):
        bg='#172731' if dark else '#f5f8fa';fg='#e6edf1' if dark else '#203b48';card='#223743' if dark else '#ffffff';border='#3a505c' if dark else '#dce5e9';alt='#1c303b' if dark else '#f0f5f6'
        self.setStyleSheet(f'''QWidget{{font-family:"Segoe UI";font-size:13px;color:{fg};}} QMainWindow,QStackedWidget{{background:{bg};}} QWidget#sidebar{{background:#103d49;}} QWidget#sidebar QLabel{{color:#b8d2d8;}} QLabel#brand{{font-size:24px;font-weight:700;color:white;}} QLabel#subbrand{{font-size:12px;line-height:1.6;}} QLabel#pageTitle{{font-size:27px;font-weight:650;}} QLabel#description{{color:{'#b5c8cf' if dark else '#5a7280'};padding-bottom:12px;}} QLabel#metrics{{background:{card};border:1px solid {border};border-radius:12px;padding:26px;font-size:19px;line-height:1.7;}} QListWidget{{background:{card};border:1px solid {border};border-radius:8px;padding:5px;}} QWidget#sidebar QListWidget{{background:transparent;border:0;color:#c7dde0;outline:0;}} QListWidget::item{{padding:10px 7px;}} QListWidget::item:selected{{background:#1d776f;color:white;border-radius:6px;}} QPushButton{{background:{card};border:1px solid {border};border-radius:6px;padding:10px 15px;font-weight:550;}} QPushButton:hover{{border-color:#268d82;}} QPushButton#primary{{background:#147f74;color:white;border:0;padding:12px 22px;}} QPushButton:disabled{{color:#96a5ad;background:{alt};}} QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QTextEdit{{background:{card};border:1px solid {border};border-radius:5px;padding:7px;selection-background-color:#247f77;}} QTableWidget{{background:{card};alternate-background-color:{alt};gridline-color:{border};border:1px solid {border};border-radius:7px;selection-background-color:#cfebe5;selection-color:#183c42;}} QHeaderView::section{{background:{alt};padding:10px;border:0;border-bottom:1px solid {border};font-weight:600;}} QProgressBar{{border:1px solid {border};border-radius:5px;text-align:center;height:22px;background:{card};}} QProgressBar::chunk{{background:#1b9587;}} QSplitter::handle{{background:{border};}} QStatusBar{{background:{card};}}''')
    def closeEvent(self,event):
        if self.tasks:
            self._closing=True;self.timer.stop();self.cancel_screening()
            if getattr(self,'three_d_window',None):self.three_d_window.close()
            self.hide();self.statusBar().showMessage('Stopping owned calculations and closing…')
            if self.tasks:event.ignore();return
        self.db.close();event.accept()
        # Hiding during cancellation suppresses lastWindowClosed. Finish the
        # application loop explicitly once the final owned task has stopped.
        if self._closing:QTimer.singleShot(0,QApplication.instance().quit)

from app.redesign import RedesignMixin
from app.studio import StudioMixin
from app.upgrade import UpgradeMixin
class Window(UpgradeMixin,StudioMixin,RedesignMixin,BaseWindow):pass

def launch(db_path=None):
    from app.branding import NAME,VERSION
    app=QApplication.instance() or QApplication(sys.argv);app.setApplicationName(NAME);app.setOrganizationName(NAME);app.setApplicationVersion(VERSION);window=Window(db_path);window.show();return app.exec()
