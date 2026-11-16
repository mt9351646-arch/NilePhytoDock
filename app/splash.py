from PySide6.QtCore import Qt,QTimer
from PySide6.QtGui import QPixmap,QPainter,QColor,QFont,QIcon
from PySide6.QtWidgets import QSplashScreen,QApplication
from app.paths import resource
from app.branding import NAME,VERSION,DEVELOPERS

def create_splash():
    from app.branding import configure_fonts
    configure_fonts()
    canvas=QPixmap(760,470);canvas.fill(QColor('#102a43'));p=QPainter(canvas);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QColor('#c9a45c'));p.drawLine(35,37,725,37);p.drawLine(35,433,725,433)
    logo=QPixmap(str(resource('app','resources','brand','NilePhytoDock-logo.png'))).scaled(255,225,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
    # A warm ivory panel preserves contrast for the supplied navy logo.
    p.setBrush(QColor('#f8f6f0'));p.setPen(Qt.PenStyle.NoPen);p.drawRoundedRect(38,78,280,275,18,18);p.drawPixmap(50+(255-logo.width())//2,98+(225-logo.height())//2,logo)
    p.setPen(QColor('#ffffff'));p.setFont(QFont('Segoe UI',25,QFont.Weight.DemiBold));p.drawText(350,152,NAME)
    p.setFont(QFont('Segoe UI',12));p.setPen(QColor('#d4e2eb'));p.drawText(350,185,'Egyptian essential oils')
    p.drawText(350,211,'Molecular discovery workspace')
    p.setPen(QColor('#c9a45c'));p.setFont(QFont('Segoe UI',11));p.drawText(350,272,'Developed by')
    p.setPen(QColor('#ffffff'));p.drawText(350,300,'Ahmed G Soliman');p.drawText(350,325,'Malak Taha')
    p.setFont(QFont('Segoe UI',10));p.setPen(QColor('#aec2d1'));p.drawText(350,360,'Version '+VERSION+'  •  P2Rank · Smina · ProLIF');p.end()
    screen=QApplication.primaryScreen().availableGeometry()
    if canvas.width()>screen.width()-40 or canvas.height()>screen.height()-40:canvas=canvas.scaled(screen.width()-40,screen.height()-40,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
    splash=QSplashScreen(canvas,Qt.WindowType.WindowStaysOnTopHint);splash.setWindowIcon(QIcon(str(resource('app','resources','brand','NilePhytoDock-Studio.ico'))))
    return splash
