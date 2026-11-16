from database.store import connect,rows
db=connect('data/validation/redesign/screening.sqlite')
print(rows(db,'SELECT id,status,folder FROM analysis_projects'))
print(rows(db,'SELECT protein_id,compound_id,status,error FROM docking_runs'))
print(rows(db,'SELECT name,status,error FROM protein_targets'))
