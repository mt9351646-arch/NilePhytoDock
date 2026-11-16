"""Nile scientific workspace, built on the existing working desktop engine."""
import hashlib,json,shutil,time
from pathlib import Path
from PySide6.QtCore import Qt,QSize,QSettings,QUrl,QTimer
from PySide6.QtGui import QIcon,QPixmap,QDesktopServices
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QFrame,QScrollArea,QLineEdit,QFileDialog,QInputDialog,QCheckBox,QSplitter,QComboBox,QMessageBox,QSizePolicy,QStyle,QDialog,QTextEdit,QDialogButtonBox)
from app.flow_layout import FlowLayout
from app.paths import resource,user_data
from app.branding import NAME,VERSION,DEVELOPERS,PURPOSE
from database.store import connect,rows,counts
from scientific.runtime import Runner,sha
from visualization.viewer import MolecularViewer
from app.diagram_view import DiagramView

class RedesignMixin:
    def __init__(self,*args,**kwargs):
        from app.branding import configure_fonts
        configure_fonts()
        self.preferences=QSettings(NAME,NAME);self.previews={};self.pocket_choices={};self.preview_source=None;self.metric_cards={}
        super().__init__(*args,**kwargs)
        self.page_title.setWordWrap(True);self.health_label.setWordWrap(True)
        self.setWindowTitle(f'{NAME} • Molecular Discovery');self.setWindowIcon(QIcon(str(resource('app','resources','brand','NilePhytoDock-Studio.ico'))))
        screen=self.screen().availableGeometry();self.resize(min(1530,screen.width()-24),min(1000,screen.height()-40))
        self.update_library_from_bundle();self.refresh()
        self.dark.setChecked(self.preferences.value('dark',False,type=bool))
        icons=[QStyle.StandardPixmap.SP_DirHomeIcon,QStyle.StandardPixmap.SP_DirIcon,QStyle.StandardPixmap.SP_FileIcon,QStyle.StandardPixmap.SP_FileDialogContentsView,QStyle.StandardPixmap.SP_MediaPlay,QStyle.StandardPixmap.SP_DialogApplyButton,QStyle.StandardPixmap.SP_FileDialogDetailedView,QStyle.StandardPixmap.SP_ArrowUp,QStyle.StandardPixmap.SP_ComputerIcon,QStyle.StandardPixmap.SP_DialogSaveButton,QStyle.StandardPixmap.SP_FileDialogInfoView]
        for i,icon in enumerate(icons):self.nav.item(i).setIcon(self.style().standardIcon(icon))
        self.nav.setIconSize(QSize(18,18))
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sticky_bar=QFrame();self.sticky_bar.setObjectName('card');sticky_layout=QVBoxLayout(self.sticky_bar);self.sticky_status=QLabel('Prepare pockets, select oils and choose an output directory.');self.sticky_status.setWordWrap(True);sticky_layout.addWidget(self.sticky_status)
        actions=QHBoxLayout();self.button('Output…',self.browse_output,actions);self.sticky_start=self.button('Run screening',self.start_screening,actions,True);self.button('Cancel',self.cancel_screening,actions);actions.addStretch();sticky_layout.addLayout(actions)
        self.stack.parentWidget().layout().addWidget(self.sticky_bar);self.nav.currentRowChanged.connect(lambda i:self.sticky_bar.setVisible(i==4));self.sticky_bar.hide();self.update_start_state()
        self.responsive_layout()
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'sidebar_brand'):self.responsive_layout()
    def responsive_layout(self):
        from app.gui import NAV
        compact=self.width()<1100
        self.sidebar.setFixedWidth(74 if compact else 250)
        self.sidebar.layout().setContentsMargins(7 if compact else 16,12,7 if compact else 16,12)
        for label in [self.sidebar_brand,self.sidebar_subtitle,self.sidebar_credit]:label.setVisible(not compact)
        self.sidebar_logo.setPixmap(QPixmap(str(resource('app','resources','brand','NilePhytoDock-logo.png'))).scaled(58 if compact else 150,55 if compact else 115,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        for i,name in enumerate(NAV):self.nav.item(i).setText('' if compact else name);self.nav.item(i).setToolTip(name)
        if hasattr(self,'stack'):
            self.stack.parentWidget().layout().setContentsMargins(14 if compact else 30,16,14 if compact else 30,14)
            for i in range(self.stack.count()):self.stack.widget(i).widget().setMinimumWidth(550 if compact else 790)
    def info(self,text):
        self.statusBar().showMessage(str(text),15000)
        if len(str(text))>300:self.text_dialog('NilePhytoDock',str(text))
    def text_dialog(self,title,text):
        dialog=QDialog(self);dialog.setWindowTitle(title);layout=QVBoxLayout(dialog);body=QTextEdit();body.setReadOnly(True);body.setPlainText(text);layout.addWidget(body)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
        screen=self.screen().availableGeometry();dialog.resize(min(760,screen.width()-60),min(620,screen.height()-60));dialog.exec()
    def update_library_from_bundle(self):
        from database.import_csv import import_csv
        # SQLite backup includes WAL content and preserves research projects
        # before any new bundled source package is merged into a user library.
        import sqlite3
        pending=False
        for name in ['reviewed_manifest.json','six_oils_manifest.json','comprehensive_manifest.json']:
            candidate=resource('data','literature',name)
            if candidate.exists() and not self.db.execute('SELECT 1 FROM literature_imports WHERE sha256=?',(hashlib.sha256(candidate.read_bytes()).hexdigest(),)).fetchone():pending=True
        if pending:
            backup=self.db_path.with_name(self.db_path.stem+'-before-library-0.6.sqlite')
            if not backup.exists():
                snapshot=sqlite3.connect(backup);self.db.backup(snapshot);snapshot.close()
        path=resource('data','source_documents','essential_oils_combined (1).csv')
        if path.exists():self.import_summary=import_csv(self.db,path)
        from database.import_literature import import_literature
        for name in ['reviewed_manifest.json','six_oils_manifest.json','comprehensive_manifest.json']:
            manifest=resource('data','literature',name)
            if manifest.exists():self.literature_summary=import_literature(self.db,manifest)
        # Add only name-matched, already verified bundled structures. Never
        # overwrite a curator's existing prepared structure or scientific data.
        seed=sqlite3.connect(resource('data','nilephytodock.sqlite').as_uri()+'?mode=ro',uri=True);seed.row_factory=sqlite3.Row
        for r in rows(seed,"SELECT s.*,c.name FROM compound_structures s JOIN chemical_compounds c ON c.id=s.compound_id WHERE s.status='identity_review' AND s.notes LIKE 'Source geometry review:%'"):
            current=self.db.execute('SELECT c.id,s.notes FROM chemical_compounds c JOIN compound_structures s ON s.compound_id=c.id WHERE c.name=? AND s.status=\'ready\'',(r['name'],)).fetchone()
            if current and str(current['notes']).startswith(('Exact normalized PubChem synonym','Verified identical InChIKey')):
                self.db.execute("UPDATE compound_structures SET status='identity_review',notes=? WHERE compound_id=?",(r['notes'],current['id']));self.db.execute("UPDATE chemical_compounds SET identity_status='identity_review',identity_notes=? WHERE id=?",(r['notes'],current['id']))
        for r in rows(seed,"SELECT s.*,c.name FROM compound_structures s JOIN chemical_compounds c ON c.id=s.compound_id WHERE s.status='ready'"):
            target=self.db.execute('SELECT id FROM chemical_compounds WHERE name=?',(r['name'],)).fetchone()
            if not target:continue
            current=self.db.execute('SELECT status FROM compound_structures WHERE compound_id=?',(target[0],)).fetchone()
            if current and current[0]=='ready':continue
            values={k:v for k,v in r.items() if k not in ['id','name']};values['compound_id']=target[0]
            self.db.execute('DELETE FROM compound_structures WHERE compound_id=?',(target[0],))
            self.db.execute('INSERT INTO compound_structures ('+','.join(values)+') VALUES ('+','.join('?' for _ in values)+')',tuple(values.values()))
            self.db.execute("UPDATE chemical_compounds SET identity_status='ready',identity_notes=? WHERE id=?",(r['notes'],target[0]))
        self.db.commit();seed.close()
        from database.heritage import import_heritage,qualify_fixed_pools
        history=resource('data','literature','heritage_manifest.json')
        if history.exists():import_heritage(self.db,history)
        qualify_fixed_pools(self.db)
    def card(self,title,value='',description=''):
        box=QFrame();box.setObjectName('card');layout=QVBoxLayout(box);layout.setContentsMargins(20,17,20,17)
        label=QLabel(title);label.setObjectName('eyebrow');layout.addWidget(label)
        number=QLabel(str(value));number.setObjectName('cardValue');layout.addWidget(number)
        if description:
            note=QLabel(description);note.setWordWrap(True);note.setObjectName('description');layout.addWidget(note)
        return box,number
    def dashboard(self):
        w=super().dashboard();l=w.layout();self.metrics.hide()
        for label in w.findChildren(QLabel,options=Qt.FindChildOption.FindDirectChildrenOnly):
            if label.text().startswith(('Screen documented constituents','Egyptian Essential Oils —')):label.hide()
        hero=QFrame();hero.setObjectName('hero');hl=QHBoxLayout(hero);hl.setContentsMargins(24,20,24,20)
        logo=QLabel();logo.setPixmap(QPixmap(str(resource('app','resources','brand','NilePhytoDock-logo.png'))).scaled(200,160,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));hl.addWidget(logo)
        text=QVBoxLayout();heading=QLabel('Discover at the intersection\nof nature and molecular science');heading.setObjectName('heroTitle');heading.setWordWrap(True);text.addWidget(heading)
        note=QLabel('A connected workspace for Egyptian essential oils, binding pockets and reproducible virtual screening.');note.setWordWrap(True);text.addWidget(note)
        credit=QLabel('Developed by '+DEVELOPERS);credit.setWordWrap(True);credit.setObjectName('description');text.addWidget(credit);hl.addLayout(text,1);l.insertWidget(0,hero)
        grid=QGridLayout();grid.setSpacing(14)
        for i,(key,title) in enumerate([('species','Plant species'),('profiles','Oil profiles'),('compounds','Compound names'),('ready','Docking-ready records'),('unique_ready','Verified unique structures'),('review','Identity review')]):
            box,value=self.card(title);self.metric_cards[key]=value;grid.addWidget(box,i//3,i%3)
        l.insertLayout(1,grid)
        actions=FlowLayout();self.button('Import proteins',lambda:self.nav.setCurrentRow(2),actions,True);self.button('Select oil profiles',lambda:self.nav.setCurrentRow(1),actions);self.button('Set up screening',lambda:self.nav.setCurrentRow(4),actions);actions.addStretch();l.insertLayout(2,actions);return w
    def library(self):
        w=super().library();l=w.layout();bar=FlowLayout();self.button('Import combined CSV',self.import_csv_dialog,bar);self.button('View CSV import summary',self.show_import_summary,bar);self.library_source=QComboBox();self.library_source.addItems(['Composition library','CSV source audit']);self.library_source.currentIndexChanged.connect(self.filter_library);bar.addWidget(self.library_source);bar.addStretch();l.insertLayout(1,bar);return w
    def filter_library(self,*_):
        if not hasattr(self,'library_source') or self.library_source.currentIndex()==0:return super().filter_library()
        text=self.search.text().casefold()
        records=rows(self.db,'SELECT p.name AS profile,c.name AS compound,r.percentage,r.status,r.source_row,r.original_row FROM csv_composition_records r JOIN oil_profiles p ON p.id=r.profile_id JOIN chemical_compounds c ON c.id=r.compound_id')
        self.library_table.populate([r for r in records if text in ' '.join(str(v) for v in r.values()).casefold()])
    def import_csv_dialog(self):
        path,_=QFileDialog.getOpenFileName(self,'Import combined essential-oil CSV','','CSV (*.csv)')
        if not path:return
        try:
            from database.import_csv import import_csv
            self.import_summary=import_csv(self.db,path);self.refresh();self.show_import_summary()
        except Exception as e:self.error(e)
    def show_import_summary(self):
        summary=getattr(self,'import_summary',{})
        self.text_dialog('CSV import summary',json.dumps(summary,ensure_ascii=False,indent=2))
    def workspace(self):
        w=super().workspace();l=w.layout()
        self.stage_label=QLabel('1  Import proteins  →  2  Prepare & predict  →  3  Select oils  →  4  Choose output  →  5  Screen');self.stage_label.setWordWrap(True);self.stage_label.setObjectName('workflow');l.insertWidget(1,self.stage_label)
        pocket_bar=FlowLayout();self.button('Prepare & predict all proteins',self.predict_all,pocket_bar,True);self.button('Inspect binding sites',lambda:self.nav.setCurrentRow(3),pocket_bar);pocket_bar.addStretch();l.insertLayout(3,pocket_bar)
        from app.gui import Table
        self.box_preview_table=Table();self.box_preview_table.setMinimumHeight(155);l.insertWidget(4,self.box_preview_table)
        # The center fields are display-only for predicted pockets. They become
        # editable only for an explicitly chosen custom box.
        self.pocket_mode.currentTextChanged.connect(self.update_start_state)
        for box in self.center:box.setDecimals(5)
        for field in [self.waters,self.remove_hetero,self.ph]:
            signal=field.toggled if isinstance(field,QCheckBox) else field.textChanged if isinstance(field,QLineEdit) else field.valueChanged
            signal.connect(self.invalidate_previews)
        self.margin=__import__('PySide6.QtWidgets',fromlist=['QDoubleSpinBox']).QDoubleSpinBox();self.margin.setRange(0,30);self.margin.setValue(6);self.margin.setSuffix(' Å');self.margin.valueChanged.connect(self.invalidate_previews)
        margin_bar=FlowLayout();margin_bar.addWidget(QLabel('Pocket-residue box margin'));margin_bar.addWidget(self.margin);margin_bar.addStretch();l.insertLayout(4,margin_bar)
        output=QFrame();output.setObjectName('card');ol=QVBoxLayout(output);title=QLabel('Output Directory');title.setObjectName('sectionTitle');ol.addWidget(title)
        row=QHBoxLayout();self.output_path=QLineEdit(self.preferences.value('output',str(user_data()/'projects')));self.output_path.setMinimumWidth(230);row.addWidget(self.output_path,1);self.button('Browse…',self.browse_output,row);ol.addLayout(row)
        row=FlowLayout();self.button('Create New Folder',self.create_output_folder,row);self.button('Use Default Location',self.default_output,row);self.button('Check Available Space',self.check_space,row);self.button('Open Results Folder',self.open_results_folder,row);row.addStretch();ol.addLayout(row);l.insertWidget(l.count()-4,output)
        return w
    def preparation_key(self):
        return json.dumps({'waters':self.waters.isChecked(),'remove':self.remove_hetero.text(),'ph':self.ph.value(),'margin':self.margin.value()},sort_keys=True)
    def invalidate_previews(self,*_):
        self.previews.clear();self.pocket_choices.clear();self.preview_source=None;self.preview_protein=None;self.preview_pockets=[]
        if hasattr(self,'pocket_table'):self.pocket_table.populate([])
        if hasattr(self,'site_target'):self.site_target.clear()
        self.update_box_table();self.update_start_state()
    def update_start_state(self,*_):
        if not hasattr(self,'start_button'):return
        mode=self.pocket_mode.currentText();custom=mode=='Custom box'
        for box in self.center:box.setReadOnly(not custom)
        valid=bool(self.protein_files) and bool(self.selected_profiles())
        if mode not in ['Custom box','Reference ligand']:valid=valid and all(sha(p) in self.pocket_choices and sha(p) in self.previews for p in self.protein_files)
        self.start_button.setEnabled(valid and bool(self.health_data) and all(v['ok'] for v in self.health_data.values()) and not self.busy)
        if hasattr(self,'sticky_start'):self.sticky_start.setEnabled(self.start_button.isEnabled())
    def update_selection(self):
        super().update_selection();self.update_start_state()
    def health_done(self,data):super().health_done(data);self.update_start_state()
    def task_failed(self,text):
        super().task_failed(text);self.update_start_state()
        if hasattr(self,'stage_label'):self.stage_label.setText('Stage failed • inspect the diagnostic message and execution log')
    def get_settings(self):
        s=super().get_settings();s.update(geometric_boxes=True,pocket_margin=self.margin.value() if hasattr(self,'margin') else 6,pocket_selections=dict(self.pocket_choices));return s
    def predict_all(self):
        if not self.protein_files:self.error('Import protein structures first');return
        self.predict_files(self.protein_files)
    def predict_files(self,files):
        settings=self.get_settings();key=self.preparation_key()
        def fn(emit):
            from scientific.proteins import prepare
            from scientific.pockets import predict
            result=[]
            for index,path in enumerate(files):
                emit('Preparing and predicting '+Path(path).name,index,len(files));identity=sha(path)
                folder=user_data()/'previews'/identity[:16]/hashlib.sha256(key.encode()).hexdigest()[:12]
                pdb,pdbqt,meta=prepare(path,folder,settings['keep_waters'],settings['remove_heterogens'],settings['ph'])
                pockets=predict(pdb,folder/'pockets',Runner(),settings['cpu'],None,settings['pocket_margin']);result.append({'source':str(path),'sha':identity,'prepared':str(pdb),'metadata':meta,'pockets':pockets})
            return result
        self.run_task(fn,self.predictions_done)
    def prepare_preview(self,predict=False):
        if not predict:return super().prepare_preview(False)
        r=self.protein_table.selected()
        if not r:self.error('Select a protein first');return
        self.predict_files([r['path']])
    def predictions_done(self,results):
        for item in results:
            self.previews[item['sha']]=item;self.pocket_choices[item['sha']]=dict(item['pockets'][0])
        self.site_target.clear()
        for identity,item in self.previews.items():self.site_target.addItem(Path(item['source']).name,identity)
        self.show_target_pockets();self.update_box_table();self.update_start_state();self.nav.setCurrentRow(3)
        self.stage_label.setText('✓ Prepared receptors and predicted pockets • select a pocket or continue to screening')
    def pocket_page(self):
        w=super().pocket_page();l=w.layout();self.site_target=QComboBox();self.site_target.currentIndexChanged.connect(self.show_target_pockets);l.insertWidget(1,self.site_target);return w
    def show_target_pockets(self,*_):
        identity=self.site_target.currentData()
        if identity not in self.previews:return
        item=self.previews[identity];self.preview_source=identity;self.preview_protein=item['prepared'];self.preview_pockets=item['pockets']
        display=[{**p,'center_x':p['center'][0],'center_y':p['center'][1],'center_z':p['center'][2]} for p in item['pockets']]
        self.pocket_table.populate(display,['rank','score','probability','center_x','center_y','center_z','size','residues'])
        self.pocket_table.sortItems(0,Qt.SortOrder.AscendingOrder)
        rank=self.pocket_choices[identity]['rank'];row=next(i for i in range(self.pocket_table.rowCount()) if self.pocket_table.item(i,0).data(Qt.ItemDataRole.UserRole)['rank']==rank);self.pocket_table.selectRow(row);self.show_pocket()
    def show_pocket(self):
        p=self.pocket_table.selected()
        if not p or self.preview_source not in self.previews:return
        self.pocket_choices[self.preview_source]=dict(p)
        self.pocket_viewer.display(self.preview_protein,pockets=[p])
        for box,value in zip(self.center,p['center']):box.setValue(value)
        for box,value in zip(self.size,p['size']):box.setValue(value)
        self.pocket_rank.setValue(p['rank']);self.update_box_table();self.update_start_state()
    def use_pocket(self):self.show_pocket();self.nav.setCurrentRow(4)
    def update_box_table(self):
        if not hasattr(self,'box_preview_table'):return
        self.box_preview_table.populate([{'protein':Path(self.previews[k]['source']).name,'pocket':v['rank'],'center_x':v['center'][0],'center_y':v['center'][1],'center_z':v['center'][2],'dimensions':v['size'],'status':'Ready'} for k,v in self.pocket_choices.items() if k in self.previews])
    def browse_output(self):
        path=QFileDialog.getExistingDirectory(self,'Select output directory',self.output_path.text())
        if path:self.output_path.setText(path);self.preferences.setValue('output',path)
    def create_output_folder(self):
        title,ok=QInputDialog.getText(self,'Create output folder','Folder name:')
        if ok and title:
            try:
                if Path(title).name!=title or title in ['.','..']:raise ValueError('Enter a folder name without path separators')
                path=Path(self.output_path.text())/title;path.mkdir(parents=True,exist_ok=False);self.output_path.setText(str(path))
            except Exception as e:self.error(e)
    def default_output(self):
        path=user_data()/'projects';path.mkdir(exist_ok=True);self.output_path.setText(str(path))
    def check_space(self):
        try:
            from app.outputs import validate_destination
            path,free=validate_destination(self.output_path.text());self.info(f'Writable: {path}\nAvailable space: {free/2**30:.1f} GB')
        except Exception as e:self.error(e)
    def open_results_folder(self):
        r=self.db.execute('SELECT folder FROM analysis_projects WHERE id=?',(self.project_id,)).fetchone() if self.project_id else None
        QDesktopServices.openUrl(QUrl.fromLocalFile(r[0] if r else self.output_path.text()))
    def generate_charts(self):
        if not self.project_id:self.error('Select a project first');return
        project=rows(self.db,'SELECT folder FROM analysis_projects WHERE id=?',(self.project_id,))[0]
        self.chart_folder=Path(project['folder'])/'Heatmaps';self.chart_folder.mkdir(parents=True,exist_ok=True);pid=self.project_id;dbpath=self.db_path
        def fn(emit):
            from visualization.figures import charts
            db=connect(dbpath)
            try:return charts(db,pid,self.chart_folder)
            finally:db.close()
        self.chart_picker.clear();self.run_task(fn,lambda fs:self.chart_picker.addItems([str(f) for f in fs]) if fs else self.info('No calculated values available.'))
    def export_view(self,viewer):
        project=self.db.execute('SELECT folder FROM analysis_projects WHERE id=?',(self.project_id,)).fetchone() if self.project_id else None
        folder=Path(project[0])/'3D_Figures' if project else user_data();folder.mkdir(parents=True,exist_ok=True)
        path,_=QFileDialog.getSaveFileName(self,'Export 3D viewport',str(folder/'complex_view.png'),'PNG (*.png)')
        if path:viewer.export_png(path)
    def select_project(self,*args):
        super().select_project(*args)
        if self.project_id:
            folder=self.db.execute('SELECT folder FROM analysis_projects WHERE id=?',(self.project_id,)).fetchone()[0];self.output_path.setText(str(Path(folder).parent))
    def start_screening(self):
        if self.busy:return
        try:
            from scientific.pipeline import create_project
            from app.outputs import project_folder
            settings=self.get_settings()
            if settings['pocket_mode']=='Reference ligand' and not settings['reference_ligand']:raise ValueError('Enter the reference ligand label from Protein Manager')
            parent=Path(self.output_path.text());parent.mkdir(parents=True,exist_ok=True)
            folder=project_folder(parent,self.study_name.text());self.preferences.setValue('output',str(parent))
            self.project_id=create_project(self.db,self.study_name.text() or 'Screening',self.protein_files,self.selected_profiles(),settings,folder);self.launch_screening();self.update_start_state()
        except Exception as e:self.error(e)
    def progress(self,text,done,total):
        super().progress(text,done,total)
        if hasattr(self,'stage_label'):self.stage_label.setText(('● '+text)+f'   |   {done}/{total or 1} calculations')
    def screening_done(self,result):
        super().screening_done(result);self.stage_label.setText('✓ Screening saved  •  Results, interactions and rankings are ready');self.update_start_state()
    def interaction_page(self):
        w=super().interaction_page();l=w.layout();old=self.diagram;split=old.parentWidget();index=split.indexOf(old);self.diagram=DiagramView();split.replaceWidget(index,self.diagram);old.deleteLater()
        tools=FlowLayout();self.button('Save 2D figure',self.save_2d_figure,tools,True);self.button('Zoom +',lambda:self.diagram.zoom(1.2),tools);self.button('Zoom −',lambda:self.diagram.zoom(1/1.2),tools);self.button('Fit / reset',self.diagram.fit,tools)
        self.show_distances=QCheckBox('Distances');self.show_types=QCheckBox('Interaction types');self.show_residues=QCheckBox('Residue labels')
        for check in [self.show_distances,self.show_types,self.show_residues]:check.setChecked(True);check.toggled.connect(self.refresh_diagram);tools.addWidget(check)
        tools.addStretch();l.insertLayout(2,tools);return w
    def open_interaction(self,*args):super().open_interaction(*args);self.refresh_diagram()
    def refresh_diagram(self,*_):
        if not self.current_pose:return
        row=self.db.execute('SELECT * FROM docking_poses WHERE id=?',(self.current_pose,)).fetchone()
        from visualization.interaction_diagram import diagram
        contacts=rows(self.db,'SELECT * FROM molecular_interactions WHERE pose_id=?',(self.current_pose,))
        svg,_=diagram(row['sdf_path'],contacts,self.pose_label.text(),self.show_distances.isChecked(),self.show_types.isChecked(),self.show_residues.isChecked());self.diagram.set_svg(svg)
    def settings_page(self):
        w=super().settings_page();l=w.layout();self.button('About NilePhytoDock',self.about,l);return w
    def about(self):
        dialog=QDialog(self);dialog.setWindowTitle('About NilePhytoDock Studio v'+VERSION);layout=QVBoxLayout(dialog)
        logo=QLabel();logo.setAlignment(Qt.AlignmentFlag.AlignCenter);logo.setPixmap(QPixmap(str(resource('app','resources','brand','NilePhytoDock-logo.png'))).scaled(250,185,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));layout.addWidget(logo)
        body=QTextEdit();body.setReadOnly(True);body.setHtml(f'<h2>NilePhytoDock Studio v{VERSION}</h2><p>{PURPOSE}</p><h3>Developed by</h3><p>Ahmed G Soliman<br>Malak Taha</p><h3>Scientific engines</h3><p>P2Rank 2.5.1 · Smina 2020.12.10<br>RDKit · ProLIF · OpenBabel</p><h3>Third-party acknowledgments</h3><p>PySide6 / Qt, 3Dmol.js, BioPython, MDAnalysis, Meeko, NumPy, SciPy, matplotlib and report-generation libraries. Original copyright and license notices remain in LICENSES.md and external_tools/licenses.</p><p>Docking predictions require scientific validation.</p>');layout.addWidget(body)
        close=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);close.rejected.connect(dialog.reject);layout.addWidget(close);screen=self.screen().availableGeometry();dialog.resize(min(640,screen.width()-50),min(720,screen.height()-50));dialog.exec()
    def refresh(self):
        super().refresh();c=counts(self.db)
        for key,label in self.metric_cards.items():label.setText(str(c['compounds']-c['ready'] if key=='review' else c[key]))
    def theme(self,dark):
        self.preferences.setValue('dark',dark)
        bg='#0d1d2c' if dark else '#f8f6f0';fg='#e3edf5' if dark else '#102a43';card='#182d40' if dark else '#ffffff';border='#31465a' if dark else '#dce3e9';muted='#a0b1c3' if dark else '#64748b';alt='#15283a' if dark else '#f3f7f8'
        self.setStyleSheet(f'''QWidget{{font-family:"Segoe UI";font-size:16px;color:{fg};}}QMainWindow,QStackedWidget,QScrollArea{{background:{bg};}}QScrollArea{{border:0;}}QScrollArea>QWidget>QWidget{{background:{bg};}}QFrame#card,QFrame#hero{{background:{card};border:1px solid {border};border-radius:14px;}}QLabel#heroTitle{{font-size:28px;font-weight:650;}}QLabel#cardValue{{font-size:32px;font-weight:650;color:{'#42cdcb' if dark else '#008c90'};}}QLabel#eyebrow{{font-size:14px;color:{muted};}}QLabel#sectionTitle{{font-size:19px;font-weight:650;}}QWidget#sidebar{{background:#102a43;}}QWidget#sidebar QLabel{{color:#c5d4df;}}QLabel#brand{{font-size:22px;font-weight:700;color:#ffffff;}}QLabel#subbrand{{font-size:13px;}}QLabel#pageTitle{{font-size:28px;font-weight:650;}}QLabel#description{{color:{muted};padding-bottom:8px;}}QLabel#workflow{{background:{alt};border-left:3px solid #c9a45c;padding:13px;color:{fg};}}QListWidget{{background:{card};border:1px solid {border};border-radius:9px;padding:5px;}}QWidget#sidebar QListWidget{{background:transparent;border:0;color:#d8e4ed;outline:0;}}QListWidget::item{{padding:12px 9px;}}QListWidget::item:selected{{background:#006c75;color:white;border-left:3px solid #c9a45c;border-radius:6px;}}QPushButton{{background:{card};border:1px solid {border};border-radius:8px;padding:11px 15px;font-weight:600;}}QPushButton:hover{{border-color:#00a6a6;background:{alt};}}QPushButton#primary{{background:#008f95;color:white;border:1px solid #008f95;}}QPushButton:disabled{{color:{muted};background:{alt};}}QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QTextEdit{{background:{card};border:1px solid {border};border-radius:6px;padding:8px;selection-background-color:#008e96;}}QTableWidget{{background:{card};alternate-background-color:{alt};gridline-color:{border};border:1px solid {border};border-radius:8px;selection-background-color:#d3eeec;selection-color:#102a43;}}QHeaderView::section{{background:{alt};padding:11px;border:0;border-bottom:1px solid {border};font-weight:600;}}QProgressBar{{border:1px solid {border};border-radius:6px;text-align:center;min-height:25px;background:{card};}}QProgressBar::chunk{{background:#00a6a6;border-radius:5px;}}QSplitter::handle{{background:{border};width:7px;}}QStatusBar{{background:{card};color:{muted};}}QMessageBox,QDialog{{background:{card};}}QMessageBox QLabel,QDialog QLabel{{color:{fg};}}QToolTip{{background:{card};color:{fg};border:1px solid {border};padding:6px;}}''')
