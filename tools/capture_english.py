"""Capture the English UI against a private copy of actual prior study results."""
import sqlite3,time,json
from pathlib import Path
from PySide6.QtCore import Qt,QPoint
from PySide6.QtWidgets import QApplication
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
from app.gui import Window
root=Path('data/validation/english_ui');root.mkdir(parents=True,exist_ok=True)
src=sqlite3.connect('data/validation/studio_workflow/screening.sqlite');dst=sqlite3.connect(root/'screening.sqlite');src.backup(dst);dst.close();src.close()
app=QApplication([]);w=Window(root/'screening.sqlite');w.output_path.setText(str((root/'English_outputs').resolve()));w.show();w.resize(1440,920)
def settle(seconds=0):
    until=time.monotonic()+seconds
    while w.tasks or time.monotonic()<until:app.processEvents();time.sleep(.03)
def capture(name):app.processEvents();w.grab().save(str(root/(name+'.png')))
settle();w.nav.setCurrentRow(0);capture('overview');w.nav.setCurrentRow(1);w.search.setText('Curcuma longa');capture('library_hplc');w.search.setText('Jasminum grandiflorum');capture('library_headspace')
w.project_id=1;w.refresh_results();w.nav.setCurrentRow(5);capture('results');w.results_table.selectRow(0);w.open_interaction();settle(1)
deadline=time.monotonic()+90
while True:
 state=[];w.interaction_viewer.page().runJavaScript('Boolean(window.viewerReady)',lambda value:state.append(value))
 while not state:app.processEvents();time.sleep(.025)
 if state[0]:break
 if time.monotonic()>deadline:raise TimeoutError('Actual interaction viewer did not render')
 settle(.25)
settle(2);capture('interactions');w.nav.setCurrentRow(4);w.protocol_tabs.setCurrentIndex(1);app.processEvents();w.stack.currentWidget().verticalScrollBar().setValue(w.protocol_tabs.mapTo(w.stack.currentWidget().widget(),QPoint(0,0)).y()-10);capture('protocol')
w.nav.setCurrentRow(10);capture('settings');w.close();app.processEvents();print('English UI captured with real source-study results')
