from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from app.gui import Window
app=QApplication([]);w=Window('data/validation/end_to_end/screening.sqlite');w.show();w.project_id=1;w.refresh_results();out=Path('data/validation/ui');out.mkdir(exist_ok=True)
def snap(i=0):
 if i>=11:
  w.results_table.selectRow(0);w.open_interaction();QTimer.singleShot(3500,final);return
 w.nav.setCurrentRow(i);w.grab().save(str(out/f'page_{i}.png'));QTimer.singleShot(250,lambda:snap(i+1))
def final():
 w.grab().save(str(out/'interaction.png'));w.interaction_viewer.export_png(str(out/'3d_export.png'));QTimer.singleShot(1500,app.quit)
QTimer.singleShot(5000,snap);app.exec();print('UI evidence written')
