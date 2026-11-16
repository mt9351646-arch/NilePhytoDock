from pathlib import Path
for name in ['app/main.py','app/redesign.py','app/splash.py']:
    p=Path(name);s=p.read_text(encoding='utf-8').replace("'NilePhytoDock.ico'","'NilePhytoDock-Studio.ico'");p.write_text(s,encoding='utf-8')
