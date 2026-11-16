from pathlib import Path
import csv,collections,json
p=Path('data/source_documents/essential_oils_combined (1).csv')
with p.open(encoding='utf-8-sig',newline='') as stream:
    reader=csv.DictReader(stream);data=list(reader);print('Headers:',reader.fieldnames)
print('Rows:',len(data))
for k in ['Plant Species / Oil Name','Scientific Name','Specific Condition/Method/Product Name']:
    print(k,collections.Counter(r[k] for r in data))
print('Values',collections.Counter(r['Relative Percentage (%)'] for r in data if not r['Relative Percentage (%)'].replace('.','',1).isdigit()))
print('Notes',collections.Counter(r['Standard Deviation (SD) / Range / Note'] for r in data if r['Standard Deviation (SD) / Range / Note']))
print('Names',len({r['Compound Name'] for r in data}))
