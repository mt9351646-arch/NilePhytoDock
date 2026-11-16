from pathlib import Path
p=Path('reporting/export.py');s=p.read_text(encoding='utf-8');s=s.replace('Composition records were extracted from the supplied Word documents with original names','Composition records were extracted from the supplied Word documents and supplementary CSV with original names');p.write_text(s,encoding='utf-8')
