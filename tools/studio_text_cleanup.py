from pathlib import Path
p=Path('app/studio.py');s=p.read_text(encoding='utf-8').replace('Quick guide ↗','Quick guide').replace('＋  New screening','New screening');p.write_text(s,encoding='utf-8')
p=Path('reporting/export.py');s=p.read_text(encoding='utf-8').replace("d.core_properties.last_modified_by='NilePhytoDock 0.2.0'","d.core_properties.last_modified_by='NilePhytoDock 0.3.0'");p.write_text(s,encoding='utf-8')
