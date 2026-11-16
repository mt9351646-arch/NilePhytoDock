import json,sys
from pathlib import Path
from database.store import connect,counts
from scientific.ligands import resolve_library
sys.stdout.reconfigure(encoding='utf-8')
db=connect('data/nilephytodock.sqlite')
ids=set(json.loads(Path(sys.argv[1] if len(sys.argv)>1 else 'data/validation/literature_import_summary.json').read_text())['new_compound_ids'])
print(resolve_library(db,'data/compound_library',lambda s:print(s,flush=True),compound_ids=ids),flush=True)
# Packaged libraries must be relocatable.
for r in db.execute('SELECT compound_id,sdf_path,pdbqt_path FROM compound_structures').fetchall():
    vals=[]
    for path in r[1:]:
        p=Path(path) if path else None
        vals.append(p.relative_to(Path('.').resolve()).as_posix() if p and p.is_absolute() and p.is_relative_to(Path('.').resolve()) else path)
    db.execute('UPDATE compound_structures SET sdf_path=?,pdbqt_path=? WHERE compound_id=?',(*vals,r[0]))
db.commit();print(counts(db),flush=True);db.close()
