"""Independent maximized 3D window with no result tables or split canvas."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence,QShortcut
from PySide6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QLabel
from visualization.viewer import MolecularViewer
from app.flow_layout import FlowLayout

class ViewerWindow(QMainWindow):
 def __init__(self,owner):
  super().__init__(owner,Qt.WindowType.Window);self.owner=owner;self.setWindowIcon(owner.windowIcon());self.resize(1500,950);self.setMinimumSize(700,500)
  self.viewer=owner.interaction_viewer;self.home=self.viewer.parentWidget()
  root=QWidget();layout=QVBoxLayout(root);layout.setContentsMargins(8,8,8,8);self.toolbar=QWidget();bar=FlowLayout(self.toolbar);self.title=QLabel();self.title.setWordWrap(True);bar.addWidget(self.title);owner.button('Full screen (F11)',self.toggle_fullscreen,bar);owner.button('Export PNG',lambda:owner.export_view(self.viewer),bar);owner.button('Close 3D window',self.close,bar);layout.addWidget(self.toolbar);self.setCentralWidget(root)
  self.fullscreen_shortcut=QShortcut(QKeySequence('F11'),self);self.fullscreen_shortcut.activated.connect(self.toggle_fullscreen);self.escape_shortcut=QShortcut(QKeySequence('Escape'),self);self.escape_shortcut.activated.connect(lambda:self.presentation(False) if self.isFullScreen() else self.close())
 def display(self,pose,contacts,context):
  self.toolbar.show();self.setWindowTitle(f"{pose['compound']} | {pose['protein']} | NilePhytoDock 3D");self.title.setText(f"{pose['compound']}  ·  {pose['protein']}  ·  pocket {pose['pocket']}  ·  {pose['score']:.3f} kcal/mol");self.centralWidget().layout().addWidget(self.viewer,1);self.viewer.show()
 def closeEvent(self,event):
  # Reparent the same scene; a second WebGL context and duplicate surfaces
  # are unnecessary for the full-window view.
  self.home.layout().addWidget(self.viewer,1);self.viewer.show();event.accept()
 def toggle_fullscreen(self):self.presentation(not self.isFullScreen())
 def presentation(self,enabled):
  import json
  self.toolbar.setVisible(not enabled);self.centralWidget().layout().setContentsMargins(*([0]*4 if enabled else [8]*4))
  self.showFullScreen() if enabled else self.showMaximized()
  self.viewer.page().runJavaScript('document.querySelectorAll(".toolbar,#legend").forEach(e=>e.style.display='+json.dumps('none' if enabled else '')+');{const h=document.getElementById("fullscreenHint");if(h)h.style.display='+json.dumps('block' if enabled else 'none')+';}window.viewer&&window.viewer.resize();')
