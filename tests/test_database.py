import json
from pathlib import Path
import pytest
from database.import_documents import import_all,value,standardized
from database.store import rows

@pytest.fixture(scope='module')
def db(tmp_path_factory):return import_all('data/source_documents',tmp_path_factory.mktemp('database')/'test.sqlite')

def test_profile_and_source_counts(db):
    assert db.execute('SELECT count(*) FROM scientific_references').fetchone()[0]==7
    assert db.execute('SELECT count(*) FROM oil_profiles').fetchone()[0]==25
    assert db.execute('SELECT count(*) FROM profile_compounds').fetchone()[0]==597
    assert db.execute('PRAGMA foreign_key_check').fetchall()==[]

@pytest.mark.parametrize('species,profile,compound,expected',[
    ('Melaleuca quinquenervia','%','1,8-Cineole (Eucalyptol)',31.57),
    ('Pimenta racemosa','%','Eugenol',70.87),
    ('Cotula cinerea','%Red Sea — MAE','Pinocarvone',62.05),
    ('Salvia fruticosa','% — HD','Eucalyptol',43.87),
    ('Rosmarinus officinalis','%Control','α-Pinene',17.52)])
def test_source_regressions(db,species,profile,compound,expected):
    r=db.execute('SELECT pc.percentage FROM profile_compounds pc JOIN oil_profiles p ON p.id=pc.profile_id JOIN essential_oils o ON o.id=p.oil_id WHERE o.name=? AND p.name LIKE ? AND pc.original_name=?',(species,profile,compound)).fetchone()
    assert r and r[0]==expected

def test_no_class_totals_screened(db):
    assert db.execute("SELECT count(*) FROM chemical_compounds WHERE lower(name) LIKE 'total %'").fetchone()[0]==0
    assert db.execute("SELECT count(*) FROM extraction_audit WHERE interpretation LIKE '%total%'").fetchone()[0]>30

def test_stereo_is_separate(db):
    assert standardized('1R-α-Pinene (D-α-Pinene)')!=standardized('1S-α-Pinene (L-α-Pinene)')
    assert len(rows(db,"SELECT * FROM chemical_compounds WHERE name LIKE '%alpha-Pinene%'") )>=3

def test_missing_is_not_zero():
    assert value('—')==(None,None,'not_reported_or_not_detected')
    assert value('')==(None,None,'not_reported')
    assert value('0.00')==(0.,None,'reported_zero')
    assert value('16.21% ± 2.60 SD')==(16.21,2.6,'reported')

def test_headspace_separate(db):
    assert db.execute("SELECT count(*) FROM oil_profiles WHERE profile_type='Headspace volatile profile'").fetchone()[0]==5

