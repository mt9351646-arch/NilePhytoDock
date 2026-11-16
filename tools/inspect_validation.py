from scientific.proteins import inspect
from database.store import connect,rows
print(inspect('tests/fixtures/1IEP.pdb'))
db=connect('data/nilephytodock.sqlite')
print(rows(db,"SELECT p.id,p.name,count(DISTINCT pc.compound_id) AS ready FROM oil_profiles p JOIN profile_compounds pc ON pc.profile_id=p.id JOIN compound_structures s ON s.compound_id=pc.compound_id WHERE s.status='ready' AND pc.percentage>0 GROUP BY p.id ORDER BY ready"))
