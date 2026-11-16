"""Application identity; third-party notices remain separate."""
NAME='NilePhytoDock'
VERSION='1.0.2'
DEVELOPERS='Ahmed G Soliman • Malak Taha'
PURPOSE='Egyptian essential oils • molecular discovery'

def configure_fonts():
    # The Windows offscreen Qt plugin does not populate system fonts reliably.
    # Load installed system fonts without redistributing their font files.
    import os
    from pathlib import Path
    from PySide6.QtGui import QFontDatabase
    for name in ['segoeui.ttf','seguisb.ttf','segoeuib.ttf']:
        path=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/name
        if path.exists():QFontDatabase.addApplicationFont(str(path))
