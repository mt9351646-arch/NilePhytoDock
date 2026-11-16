from database.store import connect
from database.import_documents import audit
from scientific.ligands import resolve_library
if __name__=='__main__':
 db=connect('data/nilephytodock.sqlite')
 print(resolve_library(db,'data/compound_library',lambda s:print(s,flush=True)))
 print(audit(db,'data/validation')['counts'])
