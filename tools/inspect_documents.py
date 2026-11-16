from docx import Document
from pathlib import Path
import json
out=[]
for p in sorted(Path('data/source_documents').glob('*.docx')):
 d=Document(p); item={'file':p.name,'paragraphs':[x.text for x in d.paragraphs if x.text.strip()],'tables':[[[c.text for c in r.cells] for r in t.rows] for t in d.tables]};out.append(item)
Path('data/validation/source_inventory.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
for x in out:
 print('\nDOCUMENT',x['file'])
 print('\n'.join(x['paragraphs']))
 for i,t in enumerate(x['tables']):
  print('TABLE',i+1,'ROWS',len(t),'COLS',len(t[0])); print('\n'.join(' | '.join(r) for r in t[:6]));print('LAST',t[-3:])
