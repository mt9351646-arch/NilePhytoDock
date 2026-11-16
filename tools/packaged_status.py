from database.store import connect,rows
from app.paths import user_data
D=connect(user_data()/'nilephytodock.sqlite');print(rows(D,'SELECT id,name,status,folder FROM analysis_projects'));print(rows(D,'SELECT status,error,elapsed FROM docking_runs'))
