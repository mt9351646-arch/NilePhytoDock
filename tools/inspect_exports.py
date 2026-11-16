from pathlib import Path
import pefile
for f in [Path('.venv/Lib/site-packages/PySide6/Qt6Core.dll'),Path('dist/NilePhytoDock/_internal/PySide6/Qt6Core.dll'),Path('dist/NilePhytoDock/_internal/icuuc.dll')]:
 p=pefile.PE(str(f));ex=p.DIRECTORY_ENTRY_EXPORT.symbols;print(str(f),len(ex),[s.name for s in ex[:10]],f.stat().st_size)
for f in Path('dist/NilePhytoDock/_internal').rglob('icu*.dll'):print(str(f),f.stat().st_size)
