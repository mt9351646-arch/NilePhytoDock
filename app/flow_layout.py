"""Wrapping command bars keep complete button labels at high display scaling."""
from PySide6.QtCore import Qt,QRect,QSize,QPoint
from PySide6.QtWidgets import QLayout

class FlowLayout(QLayout):
    def __init__(self,parent=None,spacing=8):
        super().__init__(parent);self.items=[];self.setContentsMargins(0,0,0,0);self.setSpacing(spacing)
    def addItem(self,item):self.items.append(item)
    def count(self):return len(self.items)
    def itemAt(self,index):return self.items[index] if 0<=index<len(self.items) else None
    def takeAt(self,index):return self.items.pop(index) if 0<=index<len(self.items) else None
    def addStretch(self,*_):pass
    def expandingDirections(self):return Qt.Orientation(0)
    def hasHeightForWidth(self):return True
    def heightForWidth(self,width):return self.arrange(QRect(0,0,width,0),True)
    def setGeometry(self,rect):super().setGeometry(rect);self.arrange(rect,False)
    def sizeHint(self):return self.minimumSize()
    def minimumSize(self):
        size=QSize()
        for item in self.items:size=size.expandedTo(item.minimumSize())
        return size
    def arrange(self,rect,test):
        x=rect.x();y=rect.y();line_height=0;gap=self.spacing()
        for item in self.items:
            if item.isEmpty():continue
            hint=item.sizeHint();next_x=x+hint.width()+gap
            if next_x-gap>rect.right()+1 and line_height>0:x=rect.x();y+=line_height+gap;next_x=x+hint.width()+gap;line_height=0
            if not test:item.setGeometry(QRect(QPoint(x,y),hint))
            x=next_x;line_height=max(line_height,hint.height())
        return y+line_height-rect.y()
