from PySide6.QtCore import QByteArray,Qt
from PySide6.QtWidgets import QGraphicsView,QGraphicsScene
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPixmap

class DiagramView(QGraphicsView):
    def __init__(self):
        super().__init__();self.setScene(QGraphicsScene(self));self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag);self.setMinimumSize(320,240);self.renderer=None
        self.setStyleSheet('QGraphicsView{background:white;border:1px solid #d8e2e9;border-radius:10px;}')
    def set_svg(self,svg):
        self.scene().clear();self.renderer=QSvgRenderer(QByteArray(svg.encode('utf-8')),self)
        item=QGraphicsSvgItem();item.setSharedRenderer(self.renderer);self.scene().addItem(item);self.scene().setSceneRect(item.boundingRect());self.fit()
    def setPixmap(self,pixmap):
        self.scene().clear();self.scene().addPixmap(pixmap);self.scene().setSceneRect(self.scene().itemsBoundingRect());self.fit()
    def fit(self):self.fitInView(self.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)
    def zoom(self,factor):self.scale(factor,factor)
    def wheelEvent(self,event):self.zoom(1.18 if event.angleDelta().y()>0 else 1/1.18);event.accept()
    def resizeEvent(self,event):super().resizeEvent(event);self.fit()
