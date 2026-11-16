from pathlib import Path
p=Path('reporting/export.py');s=p.read_text(encoding='utf-8');s=s.replace("keys={'Docking results'","keys={'Pocket boxes':['protein','pocket','center_x','center_y','center_z','dimensions'],'Docking results'")
p.write_text(s,encoding='utf-8')
