from pathlib import Path
import pefile
root=Path('dist/NilePhytoDock/_internal')
for f in [root/'PySide6/Qt6Core.dll',root/'PySide6/QtCore.pyd']:
 pe=pefile.PE(str(f));print('FILE',f.name)
 for dep in pe.DIRECTORY_ENTRY_IMPORT:
  name=dep.dll.decode();candidates=[root/name,root/'PySide6'/name,root/'shiboken6'/name,Path('C:/Windows/System32')/name]
  chosen=next((p for p in candidates if p.exists()),None)
  if not chosen:continue
  try:
   lib=pefile.PE(str(chosen));exports={s.name for s in lib.DIRECTORY_ENTRY_EXPORT.symbols};missing=[s.name.decode(errors='replace') for s in dep.imports if s.name and s.name not in exports]
   if missing:print(name,'missing',missing[:20],str(chosen))
  except Exception:pass
