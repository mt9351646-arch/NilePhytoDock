from pathlib import Path
from database.store import connect,rows
from app.paths import user_data
p=user_data()/'nilephytodock.sqlite';db=connect(p)
assert db.execute('SELECT count(*) FROM analysis_projects').fetchone()[0]==1
assert db.execute('SELECT name FROM analysis_projects').fetchone()[0]=='Essential oil screening'
backup=connect('data/validation/first_packaged_trials.sqlite');db.backup(backup);backup.close();db.execute('PRAGMA wal_checkpoint(TRUNCATE)');db.close()
# Only the state created by this development session is reset; trial evidence
# and calculation files remain available for auditing.
import shutil
shutil.copy2('data/nilephytodock.sqlite',p)
print('Preserved first packaged trials and restored the fresh seed for final executable verification.')
