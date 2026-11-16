from database.store import connect
from database.import_documents import audit
r=audit(connect('data/nilephytodock.sqlite'),'data/validation')
print(r['counts']);print('Unique ready molecular keys:',r['unique_ready_inchikeys']);print('Duplicate candidate keys:',len(r['duplicate_candidate_structures']))
