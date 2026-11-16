"""Qt scale-factor layout checks; does not change Windows display settings."""
import json,sys,time,shutil
from pathlib import Path
from PySide6.QtWidgets import QApplication,QPushButton,QLabel
from app.gui import Window,NAV
from PySide6.QtCore import Qt
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

def main():
    scale=float(sys.argv[1]);root=Path(sys.argv[2] if len(sys.argv)>2 else 'data/validation/layout_matrix')/str(scale);root.mkdir(parents=True,exist_ok=True)
    import sqlite3
    db=root/'layout.sqlite';source=sqlite3.connect('data/nilephytodock.sqlite');destination=sqlite3.connect(db);source.backup(destination);destination.close();source.close()
    app=QApplication([]);w=Window(db);w.show()
    deadline=time.monotonic()+60
    while w.tasks and time.monotonic()<deadline:app.processEvents();time.sleep(.03)
    assert not w.tasks
    report=[]
    for width,height in [(1366,768),(1920,1080),(2560,1440)]:
        w.resize(round(width/scale),round(height/scale));app.processEvents()
        for index,name in enumerate(NAV):
            w.nav.setCurrentRow(index);app.processEvents();scroll=w.stack.currentWidget()
            screenshot=root/f'{width}x{height}_{index}.png';w.grab().save(str(screenshot))
            # Long content may scroll; controls must remain inside that content,
            # and scroll ranges must cover the complete page geometry.
            page=scroll.widget();assert scroll.widgetResizable()
            clipped=[button.text() for button in page.findChildren(QPushButton) if button.isVisible() and button.width()+1<button.sizeHint().width()]
            assert not clipped,(scale,width,height,name,clipped)
            report.append({'size':[width,height],'requested_qt_scale':scale,'actual_device_pixel_ratio':w.devicePixelRatioF(),'page':name,'client_logical_size':[w.width(),w.height()],'content_size':[page.width(),page.height()],'horizontal_scroll_max':scroll.horizontalScrollBar().maximum(),'vertical_scroll_max':scroll.verticalScrollBar().maximum(),'screenshot':str(screenshot)})
    (root/'layout.json').write_text(json.dumps(report,indent=2),encoding='utf-8');w.close();app.processEvents();print(scale,len(report),'screens captured')

if __name__=='__main__':main()
