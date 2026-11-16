import pefile
from pathlib import Path
for f in ['.venv/Lib/site-packages/PySide6/Qt6Core.dll','.venv/Lib/site-packages/PySide6/QtCore.pyd']:
 p=pefile.PE(f); print(f)
 if hasattr(p,'DIRECTORY_ENTRY_IMPORT'):print([d.dll for d in p.DIRECTORY_ENTRY_IMPORT])
 if hasattr(p,'DIRECTORY_ENTRY_EXPORT'):print([s.name for s in p.DIRECTORY_ENTRY_EXPORT.symbols if s.name and b'qVersion' in s.name])
for f in Path('.venv').rglob('icu*.dll'):print(f,f.stat().st_size)
