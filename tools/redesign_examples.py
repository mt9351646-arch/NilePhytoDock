"""Reopen real persisted results and capture settled viewer/diagram examples."""
import json,time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from app.gui import Window
from database.store import rows
from visualization.figures import export_pose

root=Path('data/validation/redesign');report=json.loads((root/'validation.json').read_text(encoding='utf-8'))
assert report['runs']==12 and report['gui_box_and_smina_coordinates_match']
app=QApplication([]);w=Window(root/'screening.sqlite');w.show()
deadline=time.monotonic()+90
while w.tasks and time.monotonic()<deadline:app.processEvents();time.sleep(.03)
w.project_id=report['project']['id'];w.refresh_results()
for compound,label in [(205,'thymol'),(206,'carvacrol'),(20,'myrcene')]:
    row=w.db.execute('SELECT p.id FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id WHERE r.compound_id=? ORDER BY r.protein_id DESC LIMIT 1',(compound,)).fetchone()
    if row:export_pose(w.db,row[0],root/'diagram_examples'/label,300)
w.results_table.selectRow(0);w.open_interaction()
deadline=time.monotonic()+5
while time.monotonic()<deadline:app.processEvents();time.sleep(.03)
w.grab().save(str(root/'interaction_settled.png'))
from app.splash import create_splash
splash=create_splash();splash.grab().save(str(root/'splash.png'))
w.nav.setCurrentRow(0);app.processEvents();w.grab().save(str(root/'dashboard_final.png'))
w.nav.setCurrentRow(4);app.processEvents();w.grab().save(str(root/'workspace_final.png'))
w.db.execute('PRAGMA wal_checkpoint(TRUNCATE)');w.close();app.processEvents()
print('Reopened actual results; diagram and splash examples saved.')
