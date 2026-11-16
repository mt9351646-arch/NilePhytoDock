"""Compact desktop workspace with consistent navigation and contextual help."""
from pathlib import Path
from PySide6.QtCore import Qt,QSize,QTimer,QUrl,QSettings
from PySide6.QtGui import QIcon,QPixmap,QDesktopServices
from PySide6.QtWidgets import (QWidget,QFrame,QLabel,QVBoxLayout,QHBoxLayout,QGridLayout,QPushButton,QFormLayout,QTabWidget,QSizePolicy,QAbstractItemView)
from app.paths import resource
from app.branding import VERSION,DEVELOPERS
from app.flow_layout import FlowLayout
from database.store import rows,counts

NAV_LABELS=['Overview','Botanical library','Protein targets','Binding sites','Screening setup','Oil results','2D interactions','Profile priorities','Scientific charts','Reports','Settings','Functional groups','3D viewer']

class StudioMixin:
    def __init__(self,*args,**kwargs):
        stored=QSettings('NilePhytoDock','NilePhytoDock');desired_dark=stored.value('studio_dark',True,type=bool) if stored.value('studio_theme_version','')==VERSION else True
        self.studio_ready=False;self.engine_badges={};self.workflow_values={}
        super().__init__(*args,**kwargs)
        self.studio_ready=True
        self.setWindowTitle('NilePhytoDock Studio v'+VERSION)
        self.sidebar_subtitle.setText('MOLECULAR SCREENING STUDIO')
        self.sidebar_credit.setText('Ahmed G Soliman\nMalak Taha   ·   '+VERSION)
        self.sidebar_brand.setText('NilePhytoDock')
        self.health_label.setObjectName('engineStatus')
        self.page_title.setObjectName('pageTitle')
        self.statusBar().setSizeGripEnabled(False)
        self.sticky_status.setText('Choose the results folder, then run the prepared study.')
        self.preferences.setValue('studio_seen',VERSION)
        # A new visual release opens in the intended dark workspace. The light
        # theme remains available and subsequent choices persist separately.
        dark=desired_dark
        self.dark.blockSignals(True);self.dark.setChecked(dark);self.dark.blockSignals(False);self.theme(dark)
        self.results_table.empty_message='No docking results yet. Complete a screening run or open a saved project.'
        self.protein_table.empty_message='Import a PDB or mmCIF structure to begin.'
        self.pocket_table.empty_message='Predicted pockets will appear after receptor preparation and P2Rank.'
        self.contacts_table.empty_message='Double-click a calculated pose to inspect its molecular contacts.'
        self.ranking_table.empty_message='Oil priorities appear after a completed calculation.'
        for table in [self.results_table,self.protein_table,self.pocket_table,self.contacts_table,self.ranking_table]:table.update_empty_state()
        self.refresh();self.responsive_layout()
        available=self.screen().availableGeometry();self.resize(min(1460,available.width()-64),min(940,available.height()-48));self.move(available.left()+(available.width()-self.width())//2,available.top()+(available.height()-self.height())//2)
    def navigate(self,index):
        super().navigate(index)
        if 0<=index<len(NAV_LABELS):self.page_title.setText(NAV_LABELS[index])
    def responsive_layout(self):
        if not hasattr(self,'sidebar'):return
        compact=self.width()<1080
        self.sidebar.setFixedWidth(76 if compact else 228)
        self.sidebar.layout().setContentsMargins(10 if compact else 18,18,10 if compact else 18,16)
        self.sidebar.layout().setSpacing(8)
        for label in [self.sidebar_brand,self.sidebar_subtitle,self.sidebar_credit]:label.setVisible(not compact)
        self.sidebar_logo.setPixmap(QPixmap(str(resource('app','resources','brand','NilePhytoDock-logo.png'))).scaled(54 if compact else 84,48 if compact else 72,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        for i,label in enumerate(NAV_LABELS):
            item=self.nav.item(i);item.setText('' if compact else label);item.setToolTip(label)
            item.setSizeHint(QSize(48 if compact else 180,36))
            icon=resource('app','resources','nav',str(i)+'.svg')
            if icon.exists():item.setIcon(QIcon(str(icon)))
        self.nav.setIconSize(QSize(20,20));self.nav.setSpacing(1)
        if hasattr(self,'stack'):
            self.stack.parentWidget().layout().setContentsMargins(16 if compact else 26,20,16 if compact else 26,16)
        for i in range(self.stack.count()):
            container=self.stack.widget(i)
            if hasattr(container,'widget'):container.widget().setMinimumWidth(520 if compact else 730)
        if hasattr(self,'metric_grid'):
            columns=2 if compact else 4
            for index,card in enumerate(self.studio_cards):self.metric_grid.addWidget(card,index//columns,index%columns)
        if hasattr(self,'lower_grid'):
            self.lower_grid.addWidget(self.workflow_panel,0,0);self.lower_grid.addWidget(self.recent_panel,1 if compact else 0,0 if compact else 1)
    def card(self,*args,**kwargs):
        box,value=super().card(*args,**kwargs)
        for label in box.findChildren(QLabel):label.setWordWrap(True)
        return box,value
    def section(self,title,subtitle=''):
        card=QFrame();card.setObjectName('panel');layout=QVBoxLayout(card);layout.setContentsMargins(20,18,20,18);layout.setSpacing(12)
        heading=QLabel(title);heading.setObjectName('sectionTitle');layout.addWidget(heading)
        if subtitle:
            note=QLabel(subtitle);note.setWordWrap(True);note.setObjectName('muted');layout.addWidget(note)
        return card,layout
    def dashboard(self):
        w,l=self.page();l.setSpacing(16)
        self.metrics=QLabel();self.metrics.hide();l.addWidget(self.metrics)
        hero,hl=self.section('Your next molecular screening study','Prepare a receptor, select a real binding pocket and screen documented botanical constituents.')
        eyebrow=QLabel('NILEPHYTODOCK  /  DISCOVERY WORKSPACE');eyebrow.setObjectName('eyebrow');hl.insertWidget(0,eyebrow)
        actions=FlowLayout();self.button('New screening',lambda:self.nav.setCurrentRow(2),actions,True);self.button('Open saved project',self.open_project,actions);hl.addLayout(actions)
        self.library_summary=QLabel();self.library_summary.setWordWrap(True);self.library_summary.setObjectName('muted');hl.addWidget(self.library_summary);l.addWidget(hero)
        self.metric_grid=QGridLayout();self.metric_grid.setSpacing(12);self.studio_cards=[]
        for index,(key,title,note) in enumerate([('profiles','Botanical profiles','Oils, extracts and headspace'),('unique_ready','Verified structures','Distinct ready InChIKeys'),('ready','Ready compound records','Prepared for local screening'),('review','Identity review','Kept visible and excluded')]):
            card,value=self.card(title,'',note);self.metric_cards[key]=value;self.studio_cards.append(card);self.metric_grid.addWidget(card,0,index)
        l.addLayout(self.metric_grid)
        columns=QGridLayout();columns.setSpacing(16);self.lower_grid=columns
        steps,sl=self.section('Study workflow','Move through each stage. Values below reflect the current session.')
        for index,(title,description,page) in enumerate([('Protein targets','Import and review PDB / mmCIF structures',2),('Binding-site prediction','Prepare receptors and inspect P2Rank pockets',3),('Oil selection','Choose documented profiles and local ligands',1),('Screen and review','Configure output, run Smina and inspect contacts',4)]):
            row=QFrame();row.setObjectName('workflowRow');rl=QHBoxLayout(row);rl.setContentsMargins(0,8,0,8)
            number=QLabel(f'{index+1:02}');number.setObjectName('stepNumber');rl.addWidget(number)
            texts=QVBoxLayout();label=QLabel(title);label.setObjectName('rowTitle');texts.addWidget(label);detail=QLabel(description);detail.setWordWrap(True);detail.setObjectName('muted');texts.addWidget(detail);rl.addLayout(texts,1)
            status=QLabel('—');status.setObjectName('smallBadge');self.workflow_values[index]=status;rl.addWidget(status)
            go=QPushButton('→');go.setToolTip('Open '+title);go.setObjectName('iconButton');go.clicked.connect(lambda checked=False,p=page:self.nav.setCurrentRow(p));rl.addWidget(go);sl.addWidget(row)
        self.workflow_panel=steps;columns.addWidget(steps,0,0)
        recent,rl=self.section('Recent studies','Double-click a row to reopen its saved results.')
        from app.gui import Table
        self.projects_table=Table();self.projects_table.setMinimumHeight(210);self.projects_table.itemDoubleClicked.connect(self.select_project);self.projects_table.empty_message='No saved studies yet. Start a screening to create one.';rl.addWidget(self.projects_table)
        self.button('View selected study',self.select_project,rl);self.recent_panel=recent;columns.addWidget(recent,0,1);l.addLayout(columns)
        engine,el=self.section('Scientific engines','Calculations run locally. Online structure maintenance is optional.')
        bar=FlowLayout()
        for name in ['P2Rank','Smina','prolif','rdkit']:
            badge=QLabel(name+'  ·  checking');badge.setObjectName('engineBadge');self.engine_badges[name]=badge;bar.addWidget(badge)
        el.addLayout(bar);l.addWidget(engine)
        return w
    def workspace(self):
        w=super().workspace();layout=w.layout()
        # Preserve the actual bound controls and their scientific signal wiring,
        # while grouping the long protocol form into purposeful tabs.
        form=next((layout.itemAt(i).layout() for i in range(layout.count()) if isinstance(layout.itemAt(i).layout(),QFormLayout)),None)
        if form:
            tabs=QTabWidget();tabs.setObjectName('protocolTabs');forms={}
            for title in ['Binding site','Docking protocol','Receptor preparation']:
                page=QWidget();fl=QFormLayout(page);fl.setContentsMargins(18,18,18,18);fl.setVerticalSpacing(12);fl.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows);fl.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow);tabs.addTab(page,title);forms[title]=fl
            position=next(i for i in range(layout.count()) if layout.itemAt(i).layout() is form)
            while form.rowCount():
                row=form.takeRow(0);label=row.labelItem.widget() if row.labelItem else None;name=label.text() if label else ''
                target='Receptor preparation' if name in ['Protein preparation','Remove bound residues'] else 'Docking protocol' if name in ['Docking effort','Random seed','Smina scoring function'] else 'Binding site'
                field=row.fieldItem.widget() or row.fieldItem.layout()
                if label:forms[target].addRow(label,field)
                else:forms[target].addRow(field)
            layout.removeItem(form);layout.insertWidget(position,tabs);form.deleteLater();self.protocol_tabs=tabs
        self.box_preview_table.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);self.box_preview_table.setFixedHeight(120)
        return w
    def update_box_table(self):
        super().update_box_table()
        if hasattr(self,'box_preview_table'):self.box_preview_table.setFixedHeight(54+min(max(self.box_preview_table.rowCount(),1),4)*38)
    def refresh(self):
        super().refresh()
        if hasattr(self,'library_summary'):
            c=counts(self.db);self.library_summary.setText(f"{c['species']} botanical species  ·  {c['compounds']} compound names  ·  {c['records']} source observations")
            projects=rows(self.db,'SELECT id,name,created_at,status,folder FROM analysis_projects ORDER BY id DESC');self.projects_table.populate(projects,['name','status'])
            from PySide6.QtWidgets import QHeaderView
            self.projects_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch);self.projects_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.ResizeToContents)
        self.refresh_workflow()
    def refresh_workflow(self):
        if not self.workflow_values:return
        values=[f'{len(self.protein_files)} imported',f'{len(self.pocket_choices)} ready',f'{len(self.selected_profiles())} selected','Running' if self.busy else 'Ready' if self.start_button.isEnabled() else 'Set up']
        for index,value in enumerate(values):self.workflow_values[index].setText(value)
    def update_selection(self):super().update_selection();self.refresh_workflow()
    def health_done(self,data):
        super().health_done(data)
        for name,label in self.engine_badges.items():label.setText(('ProLIF' if name=='prolif' else 'RDKit' if name=='rdkit' else name)+('  ●  ready' if data.get(name,{}).get('ok') else '  ○  unavailable'))
    def update_start_state(self,*args):super().update_start_state(*args);self.refresh_workflow()
    def settings_page(self):
        return super().settings_page()
    def theme(self,dark):
        if self.studio_ready:self.preferences.setValue('studio_dark',dark);self.preferences.setValue('studio_theme_version',VERSION)
        bg='#0b1220' if dark else '#eef3f8';card='#111d30' if dark else '#ffffff';fg='#e9f0fa' if dark else '#13253d';muted='#9daec5' if dark else '#5b708a';border='#24344d' if dark else '#d7e1ec';alt='#142237' if dark else '#f5f8fc';accent='#37c9bd' if dark else '#008d87'
        self.setStyleSheet(f'''
        QWidget{{font-family:"Segoe UI";font-size:16px;color:{fg};}}
        QMainWindow,QStackedWidget,QScrollArea{{background:{bg};}} QScrollArea{{border:0;}}QScrollArea>QWidget>QWidget{{background:{bg};}}
        QWidget#sidebar{{background:#0e192a;border-right:1px solid #22324a;}}QWidget#sidebar QLabel{{color:#aabbd1;}}QLabel#brand{{color:#ffffff;font-size:21px;font-weight:650;}}QLabel#subbrand{{font-size:11px;color:#8399b7;}}
        QLabel#pageTitle{{font-size:27px;font-weight:650;}}QLabel#engineStatus{{color:{accent};font-size:13px;padding:5px 10px;}}QLabel#description,QLabel#muted{{color:{muted};font-size:14px;}}QLabel#description{{padding-bottom:6px;}}
        QFrame#panel,QFrame#card{{background:{card};border:1px solid {border};border-radius:12px;}}QLabel#sectionTitle{{font-size:21px;font-weight:650;}}QLabel#eyebrow{{color:{muted};font-size:12px;font-weight:600;}}QLabel#cardValue{{font-size:29px;font-weight:650;color:{accent};}}
        QLabel#rowTitle{{font-size:16px;font-weight:600;}}QLabel#stepNumber{{font-size:20px;color:{accent};padding-right:10px;}}QLabel#smallBadge{{font-size:12px;color:{muted};padding:5px;}}QLabel#engineBadge{{background:{alt};border:1px solid {border};border-radius:7px;padding:9px 13px;font-size:14px;}}
        QListWidget{{background:{card};border:1px solid {border};border-radius:8px;padding:4px;}}QWidget#sidebar QListWidget{{background:transparent;border:0;color:#a8bbd4;outline:0;padding:0;}}QWidget#sidebar QListWidget::item{{padding:8px 10px;border-radius:7px;}}QWidget#sidebar QListWidget::item:selected{{background:#193c49;color:#64e0d1;}}QWidget#sidebar QListWidget::item:hover{{background:#152b40;}}
        QPushButton{{background:{alt};border:1px solid {border};border-radius:7px;padding:10px 14px;font-size:14px;font-weight:600;}}QPushButton:hover{{background:{card};border-color:{accent};}}QPushButton#primary{{background:#15a99c;border:1px solid #15a99c;color:#062b2b;}}QPushButton#primary:hover{{background:#38c9ba;}}QPushButton#quietButton{{background:transparent;color:{muted};}}QPushButton#iconButton{{padding:6px 11px;color:{accent};}}QPushButton:disabled,QPushButton#primary:disabled{{color:#647895;background:{alt};border-color:{border};}}
        QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QTextEdit{{background:{card};border:1px solid {border};border-radius:6px;padding:8px;selection-background-color:#087f83;}}QLineEdit:focus,QComboBox:focus,QSpinBox:focus,QDoubleSpinBox:focus,QTextEdit:focus{{border-color:{accent};}}
        QTableWidget{{background:{card};alternate-background-color:{alt};gridline-color:{border};border:1px solid {border};border-radius:8px;selection-background-color:#194c5d;selection-color:#ffffff;}}QHeaderView::section{{background:{alt};padding:10px;border:0;border-bottom:1px solid {border};font-size:13px;font-weight:600;color:{muted};}}QTableWidget::item{{padding:5px;border:0;}}QTableWidget::item:selected{{background:#194c5d;color:#ffffff;}}
        QLabel#tableEmpty{{color:{muted};font-size:15px;padding:16px;}}QLabel#workflow{{color:{accent};background:{alt};border:1px solid {border};border-radius:8px;padding:12px;font-size:14px;}}
        QTabWidget::pane{{border:1px solid {border};background:{card};border-radius:8px;}}QTabBar::tab{{background:{alt};color:{muted};padding:12px 16px;border-bottom:2px solid transparent;}}QTabBar::tab:selected{{color:{fg};border-bottom:2px solid {accent};}}
        QProgressBar{{background:{card};border:1px solid {border};border-radius:5px;min-height:22px;text-align:center;}}QProgressBar::chunk{{background:#15a99c;border-radius:4px;}}QSplitter::handle{{background:{border};width:6px;}}QStatusBar{{background:{bg};color:{muted};font-size:12px;}}
        QScrollBar:vertical{{background:{bg};width:10px;margin:0;}}QScrollBar::handle:vertical{{background:{border};border-radius:4px;min-height:28px;}}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}QScrollBar:horizontal{{background:{bg};height:10px;}}QScrollBar::handle:horizontal{{background:{border};border-radius:4px;min-width:28px;}}
        QDialog,QMessageBox{{background:{card};}}QDialog QLabel,QMessageBox QLabel{{color:{fg};}}QToolTip{{background:{card};color:{fg};border:1px solid {border};padding:7px;}}
        ''')
