from pathlib import Path
import shutil
paths=[
'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
'<path d="M12 3c5 5 7 8 7 11a7 7 0 0 1-14 0c0-3 2-6 7-11Z"/><path d="M8 15a4 4 0 0 0 4 4"/>',
'<path d="M4 5c9 0 7 14 16 14M4 19C13 19 11 5 20 5M7 6h10M8 10h8M8 14h8M7 18h10"/>',
'<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M1 12h4M19 12h4"/>',
'<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="9" cy="6" r="2" fill="#0e192a"/><circle cx="16" cy="12" r="2" fill="#0e192a"/><circle cx="8" cy="18" r="2" fill="#0e192a"/>',
'<path d="M4 4h16v16H4zM4 9h16M10 9v11"/><path d="m13 14 2 2 3-4"/>',
'<circle cx="5" cy="12" r="3"/><circle cx="18" cy="5" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8 11 7-5M8 13l7 5"/>',
'<path d="M5 20V13M12 20V7M19 20V3M2 20h20"/>',
'<path d="M3 3v18h18M6 16l4-5 4 2 5-7"/><circle cx="10" cy="11" r="1"/><circle cx="19" cy="6" r="1"/>',
'<path d="M6 3h9l4 4v14H6zM15 3v5h4M9 12h7M9 16h7"/>',
'<path d="m9 3-1 3-3 1 1 3-2 2 2 2-1 3 3 1 1 3h6l1-3 3-1-1-3 2-2-2-2 1-3-3-1-1-3z"/><circle cx="12" cy="12" r="3"/>'
]
folder=Path('app/resources/nav');folder.mkdir(parents=True,exist_ok=True)
for i,body in enumerate(paths):(folder/f'{i}.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#9fb7d2" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'+body+'</svg>',encoding='utf-8')
shutil.copy2('app/resources/brand/NilePhytoDock.ico','app/resources/brand/NilePhytoDock-Studio.ico')
p=Path('build/windows_version.txt');s=p.read_text();s=s.replace('(0,2,0,0)','(0,3,0,0)').replace('0.2.0','0.3.0');p.write_text(s,encoding='utf-8')
p=Path('build/NilePhytoDock.spec');s=p.read_text();s=s.replace('brand/NilePhytoDock.ico','brand/NilePhytoDock-Studio.ico');p.write_text(s,encoding='utf-8')
