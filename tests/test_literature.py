import json,hashlib,shutil,sqlite3
from pathlib import Path
import pytest
from database.store import connect,rows
from database.import_literature import import_literature
from scientific.ranking import oil_indices

MANIFEST=Path('data/literature/reviewed_manifest.json')

def test_primary_sources_and_egyptian_scope():
    m=json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert len({p['species'] for p in m['profiles'] if p['geography_status']=='Egyptian collection documented'})>=25
    assert len(m['profiles'])==54 and sum(len(p['observations']) for p in m['profiles'])==830
    for pmc,r in m['references'].items():
        assert hashlib.sha256(Path('data/literature',pmc+'.xml').read_bytes()).hexdigest()==r['sha256']
        tables=json.loads(Path('data/literature',pmc+'.json').read_text(encoding='utf-8'))['tables']
        for p in (p for p in m['profiles'] if p['pmcid']==pmc):
            table=next(t for t in tables if t['id']==p['table_id'])
            for o in p['observations']:assert o['raw']==table['rows'][o['source_row']-1]

def test_import_preserves_existing_source_values_and_is_idempotent(tmp_path):
    path=tmp_path/'literature.sqlite';shutil.copy2('data/validation/pre_literature_seed.sqlite',path);db=connect(path)
    prior=rows(db,'SELECT * FROM profile_compounds ORDER BY id');s=import_literature(db,MANIFEST)
    assert s['observations']==830 and s['profiles']==54
    assert rows(db,'SELECT * FROM profile_compounds WHERE id<=661 ORDER BY id')==prior
    assert import_literature(db,MANIFEST)['already_imported']
    assert db.execute('SELECT count(*) FROM profile_compounds').fetchone()[0]==1491
    assert not db.execute('PRAGMA foreign_key_check').fetchall();db.close()

@pytest.mark.parametrize('species,profile,compound,value,unit',[
    ('Curcuma longa','%Control%','Curcumin',327.25,'ug/mL extract solution'),
    ('Vitis vinifera','%Roumy Ahmer%','gallic',4733.22,'ug/g extract'),
    ('Salvia officinalis','%El-Orman%','Camphor',23.94,'GC peak area %'),
    ('Olea europaea','%Pure olive%','Oleic acid (C18:1)',79.52,'Fatty acid GC area %'),
    ('Mentha spicata','%Giza 2018%','Carvone',42.5,'GC peak area %')])
def test_transcription_and_original_units(species,profile,compound,value,unit):
    db=connect('data/nilephytodock.sqlite')
    r=db.execute('SELECT pc.*,p.ranking_eligible FROM profile_compounds pc JOIN oil_profiles p ON p.id=pc.profile_id JOIN essential_oils o ON o.id=p.oil_id WHERE o.name=? AND p.name LIKE ? AND lower(pc.original_name)=lower(?)',(species,profile,compound)).fetchone()
    assert r and r['reported_value']==pytest.approx(value) and r['reported_unit']==unit
    assert r['percentage']==(value if unit=='GC peak area %' else None)
    if unit!='GC peak area %':assert r['ranking_eligible']==0
    db.close()

def test_other_units_and_qualitative_profiles_cannot_receive_oil_index():
    r=oil_indices({1:[{'compound_id':1,'percentage':None,'reported_value':327.25,'ranking_eligible':0}],2:[{'compound_id':1,'percentage':75,'ranking_eligible':1}]},{1:-8})
    assert next(i for i in r if i['profile_id']==1)['index'] is None
    assert next(i for i in r if i['profile_id']==2)['index']==.5
