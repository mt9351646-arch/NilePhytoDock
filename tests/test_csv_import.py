from pathlib import Path
import csv,pytest
from database.store import connect,rows
from database.import_documents import import_all
from database.import_csv import import_csv

def test_combined_csv_preserves_sources_and_is_idempotent(tmp_path):
    db=import_all('data/source_documents',tmp_path/'library.sqlite')
    original=rows(db,'SELECT * FROM profile_compounds ORDER BY id')
    result=import_csv(db,'data/source_documents/essential_oils_combined (1).csv')
    assert result['source_rows']==583 and result['new_profiles']==4 and result['new_compounds']==18
    assert result['duplicate_records']==434 and result['review_records']==85
    assert rows(db,'SELECT * FROM profile_compounds WHERE id<=597 ORDER BY id')==original
    assert db.execute('SELECT count(*) FROM csv_composition_records').fetchone()[0]==583
    assert import_csv(db,'data/source_documents/essential_oils_combined (1).csv')['already_imported']
    assert db.execute('SELECT count(*) FROM profile_compounds').fetchone()[0]==661
    assert not db.execute('PRAGMA foreign_key_check').fetchall()

def test_bad_csv_does_not_partially_import(tmp_path):
    path=tmp_path/'bad.csv'
    with open('data/source_documents/essential_oils_combined (1).csv',encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);headers=reader.fieldnames;data=list(reader)
    data[-1]['Relative Percentage (%)']='nan'
    with path.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=headers);w.writeheader();w.writerows(data)
    db=connect(tmp_path/'empty.sqlite')
    with pytest.raises(ValueError,match='outside'):import_csv(db,path)
    assert db.execute('SELECT count(*) FROM plant_species').fetchone()[0]==0
