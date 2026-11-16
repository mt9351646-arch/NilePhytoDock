from PySide6.QtWidgets import QApplication
from app.gui import Window
from PySide6.QtCore import QTimer
app=QApplication([])
w=Window('data/nilephytodock.sqlite');w.show()
QTimer.singleShot(15000,lambda:(w.grab().save('data/validation/gui_smoke.png'),app.quit()))
app.exec()
print('GUI smoke OK')
