import csv,collections
with open('data/source_documents/essential_oils_combined (1).csv',encoding='utf-8-sig',newline='') as f:rs=list(csv.DictReader(f))
groups=collections.defaultdict(list)
for r in rs:groups[(r['Plant Species / Oil Name'],r['Country/Region Grown'],r['Specific Condition/Method/Product Name'].split(' - Class:')[0] if not r['Specific Condition/Method/Product Name'].startswith('Class:') else '(class only)')].append(r)
for k,rs in groups.items():print(k,len(rs),'REF:',rs[0]['Reference / Source Document'])
