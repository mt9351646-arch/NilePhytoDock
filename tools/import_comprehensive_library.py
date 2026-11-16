"""Import reviewed packs and resolve only source-eligible new compound names."""
import json
from pathlib import Path
from database.store import connect,rows,counts
from database.import_literature import import_literature
from database.heritage import import_heritage,qualify_fixed_pools
from scientific.ligands import resolve_library
if __name__=='__main__':
 db=connect('data/nilephytodock.sqlite');summary=import_literature(db,'data/literature/comprehensive_manifest.json');import_heritage(db,'data/literature/heritage_manifest.json');qualify_fixed_pools(db)
 Path('data/validation/comprehensive_import.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(summary,flush=True)
 eligible={r['compound_id'] for r in rows(db,'SELECT DISTINCT compound_id FROM profile_compounds WHERE docking_eligible=1')};new=set(summary['new_compound_ids']);print('Resolve',len(eligible & new),'source-eligible new names',flush=True)
 resolve_library(db,'data/compound_library',lambda s:print(s,flush=True),compound_ids=eligible & new)
 print(counts(db),flush=True);db.close()
