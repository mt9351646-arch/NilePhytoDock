"""Use Qt's supported shared-context setup before pytest creates QApplication."""
from PySide6.QtCore import QCoreApplication,Qt
QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
