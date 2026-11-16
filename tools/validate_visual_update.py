"""Exercise the update against an isolated copy of the retained verification study."""
import os,sqlite3,json
from pathlib import Path
out=Path('data/validation/v1_0_1_visual').resolve();out.mkdir(parents=True,exist_ok=True);os.environ['NILEPHYTODOCK_DATA']=str(out/'userdata')
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
from database.store import connect
from app.projects import relocate_saved_project
source=sqlite3.connect('data/validation/case_study_final/case_study.sqlite');target=sqlite3.connect(out/'study.sqlite');source.backup(target);source.close();target.close()
db=connect(out/'study.sqlite');relocate_saved_project(db,Path('data/validation/case_study_final/screening/Project_Data/project.nile.sqlite'));db.close()
from app.gui import Window
from app.visual_verification import verify
app=QApplication([]);window=Window(out/'study.sqlite');window.project_id=1;window.show();window.resize(1500,1000)
try:print(json.dumps(verify(window,app,out),indent=2),flush=True)
finally:
 while window.tasks:app.processEvents()
 window.close();app.processEvents()
