"""Scientific visualization controls and a minimal two-counter homepage."""
import json,shutil,time
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel,QWidget,QHBoxLayout,QVBoxLayout,QComboBox,QCheckBox,QFileDialog,QInputDialog,QPushButton
from database.store import rows,counts
from app.flow_layout import FlowLayout
from visualization.semantics import MODES,INTERACTIONS,CHARGE_NOTE

class UpgradeMixin:
    def library(self):
        w=super().library();bar=FlowLayout();self.library_category=QComboBox();self.library_category.addItems(['All preparations','Essential Oils','Fixed Oils','Botanical Extracts','Resins and Aromatic Preparations','Individual Natural Compounds','Ancient Egyptian Botanical Heritage']);bar.addWidget(QLabel('Preparation / heritage'));bar.addWidget(self.library_category);self.library_category.currentTextChanged.connect(self.filter_library);w.layout().insertLayout(2,bar);return w
    def filter_library(self,*_):
        if not hasattr(self,'library_category'):return super().filter_library()
        category=self.library_category.currentText();text=self.search.text().casefold()
        self.library_source.setEnabled(category=='All preparations')
        if category=='Ancient Egyptian Botanical Heritage':
            records=rows(self.db,'SELECT * FROM botanical_history ORDER BY common_name');self.library_table.populate([r for r in records if text in ' '.join(str(v) for v in r.values()).casefold()],['common_name','scientific_name','association','evidence_type','period','confidence','taxonomic_scope','description','source_url']);self.profile_list.hide();return
        self.profile_list.show()
        if category=='All preparations':
            for i in range(self.profile_list.count()):self.profile_list.item(i).setHidden(False)
            return super().filter_library()
        self.library_table.populate([r for r in self.library_records if r['preparation_category']==category and text in ' '.join(str(v) for v in r.values()).casefold()],['original_name','reported_value','reported_unit','docking_status','profile','preparation_category','origin','geography_status','annotation_level','identity_notes','citation'])
        eligible_profiles={r['id'] for r in rows(self.db,'SELECT id FROM oil_profiles WHERE preparation_category=?',(category,))}
        for i in range(self.profile_list.count()):self.profile_list.item(i).setHidden(self.profile_list.item(i).data(Qt.ItemDataRole.UserRole) not in eligible_profiles)
    def dashboard(self):
        from app.gui import Table
        w,l=self.page();l.setContentsMargins(12,40,12,20);l.setSpacing(24)
        self.metrics=QLabel();self.metrics.hide();self.library_summary=QLabel();self.library_summary.hide();l.addWidget(self.metrics)
        cards=QHBoxLayout();cards.setSpacing(24)
        for key,title,note in [('botanical_oils','Botanical Oils','Unique essential and fixed botanical oils'),('unique_ready','Chemical Compounds','Unique verified chemical structures')]:
            box,label=self.card(title,'',note);box.setMaximumHeight(180);cards.addWidget(box);self.metric_cards[key]=label
        l.addLayout(cards)
        bar=FlowLayout();self.button('Start New Screening',self.new_screening,bar,True);self.button('Essential Oil Library',lambda:self.nav.setCurrentRow(1),bar);self.button('Previous Projects',self.toggle_previous,bar);self.button('Open Saved Project',self.open_project,bar);l.addLayout(bar)
        self.projects_table=Table();self.projects_table.itemDoubleClicked.connect(self.select_project);self.projects_table.empty_message='No saved studies yet.';self.projects_table.hide();l.addWidget(self.projects_table);l.addStretch();return w
    def toggle_previous(self):self.projects_table.setVisible(not self.projects_table.isVisible())
    def new_screening(self):
        if self.busy:self.error('Finish or cancel the running study before starting a new one.');return
        self.project_id=None;self.protein_files=[];self.previews={};self.pocket_choices={};self.preview_pockets=[];self.study_name.setText('Screening '+time.strftime('%Y-%m-%d %H%M'));self.refresh();self.nav.setCurrentRow(2);self.update_start_state()
    def refresh_workflow(self):
        if getattr(self,'workflow_values',None):super().refresh_workflow()
    def responsive_layout(self):
        # Reuse the established typography and responsive sidebar, while the
        # new dashboard deliberately has no four-card or workflow grid.
        super().responsive_layout()
    def interaction_page(self):
        w=super().interaction_page();l=w.layout();base_exports=l.itemAt(1).layout();primary_tools=l.itemAt(2).layout();bar=FlowLayout();self.diagram_style=QComboBox();self.diagram_style.addItems(['Interaction map','Classic','Circular','Functional group']);self.residue_mode=QComboBox();self.residue_mode.addItems(MODES);self.residue_mode.setCurrentText('Interaction participation');self.line_style=QComboBox();self.line_style.addItems(['Accessible','Solid']);self.show_nodes=QCheckBox('Show residues');self.show_nodes.setChecked(True);self.show_types.setChecked(False);self.custom_line_colors={}
        for label,control in [('2D style',self.diagram_style),('Residue color',self.residue_mode),('Line style',self.line_style)]:bar.addWidget(QLabel(label));bar.addWidget(control);control.currentTextChanged.connect(self.refresh_diagram)
        bar.addWidget(self.show_nodes);self.show_nodes.toggled.connect(self.refresh_diagram);self.button('Open 3D viewer',lambda:self.nav.setCurrentRow(12),bar,True);l.insertLayout(2,bar)
        self.interaction_viewer.setParent(None)
        self.contacts_table.hide();contact_toggle=QCheckBox('Show detailed contacts');contact_toggle.toggled.connect(self.contacts_table.setVisible);l.addWidget(contact_toggle)
        actions=FlowLayout();self.button('Export complex and ligand',self.export_complex,actions);self.button('Reanalyze selected pose',self.reanalyze_pose,actions);self.pymol_session_button=self.button('Export PyMOL session',lambda:self.export_complex(session=True),actions);self.pymol_session_button.setEnabled(bool(shutil.which('pymol')));self.pymol_session_button.setToolTip('Requires an available legitimate PyMOL installation. The PML script export works without PyMOL.');l.insertLayout(3,actions)
        self.button('Change 2D Line Colors',self.choose_line_color,actions);self.button('Reset Layout',self.reset_diagram_layout,actions);self.button('Export Interaction Table',self.export_interaction_table,actions)
        self.interaction_info=QLabel('Select a calculated pose. Interaction line and residue-fill legends appear below the 2D canvas.');self.interaction_info.setWordWrap(True);l.addWidget(self.interaction_info);self.contacts_table.itemSelectionChanged.connect(self.focus_contact)
        # Keep the drawing large. Less-frequent controls are available in a
        # collapsed panel instead of taking most of the viewport height.
        canvas=self.diagram.parentWidget();base_exports.removeWidget(self.pose_label)
        l.itemAt(0).widget().hide()
        while l.count():
            item=l.takeAt(0)
            if item.layout():item.layout().setParent(None)
        header=FlowLayout();header.addWidget(self.pose_label);header.addStretch();more=QPushButton('More controls');more.setCheckable(True);header.addWidget(more);l.addLayout(header);l.addLayout(primary_tools)
        advanced=QWidget();advanced_layout=QVBoxLayout(advanced);advanced_layout.setContentsMargins(0,0,0,0);advanced_layout.addLayout(bar);advanced_layout.addLayout(actions);advanced_layout.addLayout(base_exports);advanced_layout.addWidget(self.interaction_info);advanced.hide();more.toggled.connect(advanced.setVisible);l.addWidget(advanced)
        self.diagram.setMinimumHeight(320);l.addWidget(canvas,1);l.addWidget(contact_toggle);l.addWidget(self.contacts_table);return w
    def open_interaction(self,*_):
        row=self.results_table.selected()
        if not row or not row.get('pose_id'):self.error('Select a successfully calculated pose');return
        self.show_pose(row,three_d=True)
    def show_pose_id(self,pose_id,three_d=True):
        records=rows(self.db,'SELECT p.id AS pose_id,p.rank AS pose,p.score,p.sdf_path,p.complex_path,c.name AS compound,t.name AS protein,t.prepared_path,k.rank AS pocket FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id JOIN chemical_compounds c ON c.id=r.compound_id JOIN protein_targets t ON t.id=r.protein_id JOIN predicted_pockets k ON k.id=r.pocket_id WHERE p.id=?',(pose_id,))
        if records:self.show_pose(records[0],three_d)
    def show_pose(self,row,three_d=True):
        self._pose_generation=getattr(self,'_pose_generation',0)+1;generation=self._pose_generation;path=self.db_path;row=dict(row)
        context={'protein':row['protein'],'ligand':row['compound'],'pocket':row['pocket'],'pose':row['pose']}
        self.statusBar().showMessage('Preparing verified molecular views…')
        def work(emit):
            from database.store import connect
            from scientific.contact_store import ensure_pose_contacts
            from visualization.viewer import MolecularViewer
            db=connect(path)
            try:contacts=ensure_pose_contacts(db,row['pose_id'])
            finally:db.close()
            return contacts,MolecularViewer.prepare_data(row['prepared_path'],row['sdf_path'],contacts=contacts,context=context)
        def done(result):
            if generation!=self._pose_generation or path!=self.db_path:return
            contacts,data=result;self.current_pose=row['pose_id'];self.contacts_table.populate(contacts,['residue','chain','residue_number','interaction_type','protein_atom','ligand_atom','distance','angle','method'])
            self.viewer_pose=row;self.viewer_contacts=contacts;self.viewer_context=context;self.interaction_viewer.display_data(data)
            self.pose_label.setText(f"{row['compound']} | {row['protein']} | pocket {row['pocket']} | pose {row['pose']}");self.viewer_pose_label.setText(self.pose_label.text());self.interaction_info.setText(self.pose_label.text()+' | '+str(len(contacts))+' chemically classified contacts. '+CHARGE_NOTE)
            if not three_d:self.refresh_diagram()
            self.nav.setCurrentRow(12 if three_d else 6)
            if getattr(self,'_open_separate_after_pose',False):self._open_separate_after_pose=False;self.open_three_d_window()
        self.run_task(work,done)
    def reanalyze_pose(self):
        if not self.current_pose:return
        try:
            from scientific.contact_store import ensure_pose_contacts
            ensure_pose_contacts(self.db,self.current_pose,True);self.show_pose_id(self.current_pose,self.nav.currentRow()==12)
        except Exception as error:self.error(error)
    def focus_contact(self):
        contact=self.contacts_table.selected()
        if not contact:return
        meta=json.loads(contact.get('metadata') or '{}');self.interaction_viewer.focus_contact(contact['id']);self.interaction_info.setText(self.pose_label.text()+f" | {contact['residue']} | {contact['interaction_type']} | {contact['distance']:.3f} A"+(f" | {meta.get('reported_angle_name','angle')} {contact['angle']:.2f} degrees" if contact.get('angle') is not None else '')+' | '+contact['method'])
    def current_diagram(self):
        if not self.current_pose:return None
        from visualization.interaction_diagram import diagram
        pose=self.db.execute('SELECT * FROM docking_poses WHERE id=?',(self.current_pose,)).fetchone();contacts=rows(self.db,'SELECT * FROM molecular_interactions WHERE pose_id=?',(self.current_pose,))
        if self.diagram_style.currentText()=='Functional group':
            from visualization.functional_map import diagram as feature_diagram
            return feature_diagram(pose['sdf_path'],contacts,self.pose_label.text(),self.residue_mode.currentText(),self.custom_line_colors,self.show_distances.isChecked(),self.show_types.isChecked(),self.show_residues.isChecked(),self.line_style.currentText(),self.show_nodes.isChecked())
        return diagram(pose['sdf_path'],contacts,self.pose_label.text(),self.show_distances.isChecked(),self.show_types.isChecked(),self.show_residues.isChecked(),self.diagram_style.currentText(),self.residue_mode.currentText(),self.line_style.currentText(),self.show_nodes.isChecked(),self.custom_line_colors)
    def choose_line_color(self):
        from PySide6.QtWidgets import QColorDialog
        from PySide6.QtGui import QColor
        kind,ok=QInputDialog.getItem(self,'2D interaction colors','Interaction category',list(INTERACTIONS),0,False)
        if not ok:return
        color=QColorDialog.getColor(QColor(self.custom_line_colors.get(kind,INTERACTIONS[kind][1])),self,'Choose 2D '+kind+' color')
        if color.isValid():self.custom_line_colors[kind]=color.name();self.refresh_diagram()
    def reset_diagram_layout(self):
        self.refresh_diagram();self.diagram.fit()
    def export_interaction_table(self):
        if not self.project_id:self.error('Open a calculated project first.');return
        modes=['Complete Interaction Table','Best Pose Interactions','Selected Protein Interactions','Selected Compound Interactions','Functional Group Interaction Summary','Interaction Frequency Summary'];mode,ok=QInputDialog.getItem(self,'Export Interaction Table','Export mode',modes,0,False)
        if not ok:return
        protein=compound=None
        if mode=='Selected Protein Interactions':
            options=rows(self.db,'SELECT id,name FROM protein_targets WHERE project_id=?',(self.project_id,));label,ok=QInputDialog.getItem(self,'Protein','Target',[r['name'] for r in options],0,False)
            if not ok:return
            protein=next(r['id'] for r in options if r['name']==label)
        if mode=='Selected Compound Interactions':
            options=rows(self.db,'SELECT DISTINCT c.id,c.name FROM chemical_compounds c JOIN docking_runs r ON r.compound_id=c.id WHERE r.project_id=?',(self.project_id,));label,ok=QInputDialog.getItem(self,'Compound','Ligand',[r['name'] for r in options],0,False)
            if not ok:return
            compound=next(r['id'] for r in options if r['name']==label)
        folder=QFileDialog.getExistingDirectory(self,'Export calculated interaction CSV XLSX and DOCX')
        if not folder:return
        try:
            from scientific.molecular_analysis import interaction_rows,analyze,export_tables
            if mode=='Functional Group Interaction Summary':data=analyze(self.db,self.project_id)['functional_group_interactions']
            else:data=interaction_rows(self.db,self.project_id,mode,protein,compound)
            if mode=='Interaction Frequency Summary':
                grouped={}
                for r in data:
                    key=(r['protein_id'],r['pocket_id'],r['residue'],r['interaction_type']);g=grouped.setdefault(key,{'protein':r['protein'],'pocket':r['binding_pocket'],'residue':r['residue'],'interaction_type':r['interaction_type'],'events':0,'identities':set(),'pairs':set()});g['events']+=1;g['identities'].add(r['inchikey'] or r['compound_id']);g['pairs'].add((r['inchikey'] or r['compound_id'],r['residue']))
                data=[{k:v for k,v in g.items() if k not in ['identities','pairs']}|{'distinct_compounds':len(g['identities']),'distinct_ligand_residue_pairs':len(g['pairs'])} for g in grouped.values()]
            export_tables(data,Path(folder)/mode.replace(' ','_'),mode);self.info('Interaction tables exported to '+folder)
        except Exception as error:self.error(error)
    def refresh_diagram(self,*_):
        if not getattr(self,'current_pose',None) or not hasattr(self,'diagram_style'):return
        result=self.current_diagram()
        if result:self.diagram.set_svg(result[0])
    def export_interaction(self):
        if not self.current_pose:self.error('Select a pose first');return
        folder=QFileDialog.getExistingDirectory(self,'Export 2D figures and molecular visualization script')
        if not folder:return
        dpi,ok=QInputDialog.getItem(self,'Figure resolution','PNG DPI',['300','600'],0,False)
        if not ok:return
        try:
            from visualization.interaction_diagram import save_diagram
            from visualization.export3d import export_molecular_files
            svg,layout=self.current_diagram();stem=Path(folder)/('pose_'+str(self.current_pose)+'_'+self.diagram_style.currentText());save_diagram(svg,stem,int(dpi));stem.with_suffix('.layout.json').write_text(json.dumps(layout,indent=2),encoding='utf-8');export_molecular_files(self.db,self.current_pose,folder);self.info('Figure and molecular files saved to '+folder)
        except Exception as error:self.error(error)
    def save_2d_figure(self):
        if not self.current_pose:self.error('Select a calculated pose first.');return
        path,selected=QFileDialog.getSaveFileName(self,'Save 2D interaction figure','pose_'+str(self.current_pose)+'_interactions.png','PNG image (*.png);;SVG vector (*.svg)')
        if not path:return
        try:
            svg,_=self.current_diagram();target=Path(path)
            if target.suffix.lower() not in ('.png','.svg'):target=target.with_suffix('.svg' if 'SVG' in selected else '.png')
            if target.suffix.lower()=='.svg':target.write_text(svg,encoding='utf-8')
            else:
                from visualization.interaction_diagram import save_diagram
                save_diagram(svg,target,300)
            self.info('2D figure saved to '+str(target))
        except Exception as error:self.error(error)
    def export_complex(self,checked=False,session=False):
        if not self.current_pose:return
        folder=QFileDialog.getExistingDirectory(self,'Export complex PDB ligand SDF and PyMOL script')
        if not folder:return
        try:
            from visualization.export3d import export_molecular_files
            export_molecular_files(self.db,self.current_pose,folder,session=session);self.info('Molecular files and '+('PyMOL session' if session else 'PyMOL script')+' exported to '+folder)
        except Exception as error:self.error(error)
    def export_view(self,viewer):
        record=self.db.execute('SELECT folder FROM analysis_projects WHERE id=?',(self.project_id,)).fetchone() if self.project_id else None
        default=Path(record[0])/'3D_Figures' if record else Path.home();default.mkdir(parents=True,exist_ok=True)
        path,_=QFileDialog.getSaveFileName(self,'Export high-resolution 3D figure',str(default/'molecular_view.png'),'PNG (*.png)')
        if not path:return
        dpi,ok=QInputDialog.getItem(self,'3D figure resolution','PNG DPI',['300','600'],0,False)
        if ok:viewer.export_png(path,int(dpi),2400 if dpi=='300' else 4800,1800 if dpi=='300' else 3600,lambda success:self.info('3D figure saved to '+path) if success else self.error('The 3D viewport could not be exported.'))
    def analysis_page(self):
        from app.chart_workspace import ChartWorkspace
        w,l=self.page('Choose a chart supported by saved results. Hover for values; click a point for details.');self.chart_workspace=ChartWorkspace(self);l.addWidget(self.chart_workspace,1);return w
    def navigate(self,index):
        super().navigate(index)
        if index==8 and getattr(self,'project_id',None):self.chart_workspace.set_project(self.project_id)
        if index==11 and getattr(self,'project_id',None) and self.functional_tabs.currentIndex()==1:self.molecular_workspace.set_project(self.project_id)
        if index==5 and hasattr(self,'oil_results'):self.oil_results.set_project(getattr(self,'project_id',None))
        if index==11 and hasattr(self,'functional_results') and self.functional_tabs.currentIndex()==0:self.functional_results.set_project(getattr(self,'project_id',None))
    def molecular_page(self):
        from app.molecular_workspace import MolecularWorkspace
        from app.result_workspace import FunctionalResults
        from PySide6.QtWidgets import QTabWidget
        w,l=self.page();tabs=QTabWidget();self.functional_tabs=tabs;self.functional_results=FunctionalResults(self);self.molecular_workspace=MolecularWorkspace(self);tabs.addTab(self.functional_results,'Groups in best compounds');tabs.addTab(self.molecular_workspace,'Similarity & shared groups');tabs.currentChanged.connect(lambda index:(self.functional_results if index==0 else self.molecular_workspace).set_project(getattr(self,'project_id',None)));l.addWidget(tabs,1);return w
    def results(self):
        from app.result_workspace import OilResults
        from PySide6.QtWidgets import QTabWidget
        raw=super().results();w,l=self.page();tabs=QTabWidget();self.oil_results=OilResults(self);tabs.addTab(self.oil_results,'Best compounds by oil');tabs.addTab(raw,'Detailed docking records');l.addWidget(tabs,1);return w
    def three_d_page(self):
        w,l=self.page();bar=FlowLayout();self.viewer_pose_label=QLabel('Choose a compound from Oil results');self.viewer_pose_label.setWordWrap(True);bar.addWidget(self.viewer_pose_label);self.button('Open separate 3D window',self.open_three_d_window,bar,True);self.button('Export 3D PNG',lambda:self.export_view(self.interaction_viewer),bar);l.addLayout(bar);l.addWidget(self.interaction_viewer,1);self.interaction_viewer.setMinimumHeight(420);return w
    def open_three_d_window(self):
        if not getattr(self,'viewer_pose',None):self.error('Choose a calculated compound from Oil results first.');return
        from app.viewer_window import ViewerWindow
        if not getattr(self,'three_d_window',None):self.three_d_window=ViewerWindow(self)
        self.three_d_window.display(self.viewer_pose,self.viewer_contacts,self.viewer_context);self.three_d_window.showMaximized();self.three_d_window.raise_();self.three_d_window.activateWindow()
    def screening_done(self,result):
        super().screening_done(result)
        self.oil_results.set_project(self.project_id,force=True)
    def generate_charts(self):
        if self.project_id:self.chart_workspace.set_project(self.project_id,force=True)
