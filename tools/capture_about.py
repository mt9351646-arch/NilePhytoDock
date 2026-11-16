import time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from app.gui import Window
app=QApplication([]);w=Window('data/validation/redesign/screening.sqlite');w.show()
deadline=time.monotonic()+60
while w.tasks and time.monotonic()<deadline:app.processEvents();time.sleep(.03)
def capture():
    dialog=app.activeModalWidget()
    if dialog:dialog.grab().save('data/validation/redesign/about.png');dialog.accept()
QTimer.singleShot(700,capture);w.about();w.close();app.processEvents();print('About dialog captured')
