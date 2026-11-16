from pathlib import Path
from database.store import connect,rows
D=connect('data/nilephytodock.sqlite')
assert D.execute('SELECT count(*) FROM analysis_projects').fetchone()[0]==0
assert D.execute('PRAGMA foreign_key_check').fetchall()==[]
print('Delivered seed contains composition data only; no demonstration docking results.')
