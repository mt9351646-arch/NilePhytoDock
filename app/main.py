import multiprocessing
import sys
from pathlib import Path

def main():
    multiprocessing.freeze_support()
    if sys.platform=='win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('NilePhytoDock.Studio')
    from PySide6.QtCore import Qt,QTimer,QLocale
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app=QApplication.instance() or QApplication(sys.argv)
    QLocale.setDefault(QLocale('en_US'));app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    from app.branding import NAME,VERSION
    from app.paths import resource
    app.setApplicationName(NAME);app.setOrganizationName(NAME);app.setApplicationVersion(VERSION);app.setWindowIcon(QIcon(str(resource('app','resources','brand','NilePhytoDock-Studio.ico'))))
    from app.splash import create_splash
    splash=create_splash();splash.show();splash.showMessage('Loading scientific workspace…',Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter,Qt.GlobalColor.white);app.processEvents()
    def start():
        try:
            from app.gui import Window
            window=Window();app.main_window=window
            if any(flag in sys.argv for flag in ('--verify-installation','--verify-close')):window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
            window.show();splash.finish(window)
            if '--verify-close' in sys.argv:
                from app.lifecycle_check import start as verify_close
                index=sys.argv.index('--verify-close');verify_close(window,app,sys.argv[index+1],sys.argv[index+2])
            if '--verify-network' in sys.argv:
                from app.installation_check import network_check
                index=sys.argv.index('--verify-network');network_check(window,app,sys.argv[index+1])
            if '--benchmark-startup' in sys.argv:
                # Explicit packaging QA only; normal launches create no benchmark files.
                import json,time
                index=sys.argv.index('--benchmark-startup');destination=Path(sys.argv[index+1]);destination.parent.mkdir(parents=True,exist_ok=True)
                def ready():
                    if not window.health_data or window.tasks:QTimer.singleShot(50,ready);return
                    destination.write_text(json.dumps({'version':VERSION,'engines_ready':all(c['ok'] for c in window.health_data.values()),'frozen':bool(getattr(sys,'frozen',False)),'runtime_root':str(resource()),'database_loaded':bool(window.db.execute('SELECT count(*) FROM oil_profiles').fetchone()[0])}),encoding='utf-8');app.exit(0)
                QTimer.singleShot(50,ready)
            if '--verify-installation' in sys.argv:
                from app.installation_check import start as verify_installation
                index=sys.argv.index('--verify-installation');verify_installation(window,app,sys.argv[index+1],sys.argv[index+2])
        except Exception:
            import traceback
            from PySide6.QtWidgets import QMessageBox
            from app.paths import user_data
            error=traceback.format_exc();(user_data()/'startup_error.log').write_text(error,encoding='utf-8');splash.close();QMessageBox.critical(None,'NilePhytoDock startup error',error);app.exit(1)
    QTimer.singleShot(80,start)
    return app.exec()

if __name__=='__main__':
    try:sys.exit(main())
    except Exception:
        import traceback
        from app.paths import user_data
        (user_data()/'startup_error.log').write_text(traceback.format_exc(),encoding='utf-8')
        from PySide6.QtWidgets import QApplication,QMessageBox
        app=QApplication.instance() or QApplication([]);QMessageBox.critical(None,'NilePhytoDock startup error',traceback.format_exc());sys.exit(1)
