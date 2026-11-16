from database.store import connect,rows
db=connect('data/nilephytodock.sqlite')
print(rows(db,"SELECT c.id,c.name,s.status,s.inchikey FROM chemical_compounds c LEFT JOIN compound_structures s ON s.compound_id=c.id WHERE c.id>202"))
print(rows(db,"SELECT p.id,p.name,count(s.id) AS ready FROM oil_profiles p JOIN profile_compounds pc ON pc.profile_id=p.id LEFT JOIN compound_structures s ON s.compound_id=pc.compound_id AND s.status='ready' WHERE p.id>25 GROUP BY p.id"))
