import json
from pathlib import Path
from database.store import connect
from reporting.export import export_all
root=Path('data/validation/redesign');report=json.loads((root/'validation.json').read_text(encoding='utf-8'))
db=connect(root/'screening.sqlite');folder=Path(report['project']['folder'])/'Reports';export_all(db,report['project']['id'],folder)
report['interaction_count']=db.execute('SELECT count(*) FROM molecular_interactions').fetchone()[0]
(root/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');db.close()
print('Actual redesigned report package refreshed; contacts:',report['interaction_count'])
