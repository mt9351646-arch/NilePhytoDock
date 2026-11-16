import json
from pathlib import Path
from database.store import connect
from database.import_csv import import_csv
from database.import_documents import audit
db=connect('data/nilephytodock.sqlite')
backup=Path('data/validation/pre_csv_library.sqlite')
if not backup.exists():
    out=connect(backup);db.backup(out);out.close()
source=Path('data/source_documents/essential_oils_combined (1).csv')
report=import_csv(db,source);audit(db,'data/validation')
Path('data/validation/csv_import_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
db.execute('PRAGMA wal_checkpoint(TRUNCATE)');db.close();print(report)
