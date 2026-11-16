"""Import reviewed, hashed literature observations without altering old data."""
import hashlib,json,math
from pathlib import Path
from database.store import insert,rows,counts
from database.import_csv import identity_key
from database.import_documents import standardized

def import_literature(db,path):
    path=Path(path);raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    prior=db.execute('SELECT summary FROM literature_imports WHERE sha256=?',(digest,)).fetchone()
    if prior:return {**json.loads(prior[0]),'already_imported':True}
    manifest=json.loads(raw);before=counts(db);refs={};new_ids=[];observations=0
    # Validate the complete input before any mutation.
    for p in manifest['profiles']:
        assert p['pmcid'] in manifest['references'] and p['species'] and p['observations']
        for o in p['observations']:
            v=o['value'];assert v is None or (math.isfinite(v) and v>=0)
            if o['unit']=='GC peak area %' and v is not None:assert v<=100
            assert o['name'] and o['source_row']>0
    db.execute('SAVEPOINT literature')
    try:
        compounds={identity_key(r['name']):r['id'] for r in rows(db,'SELECT id,name FROM chemical_compounds')}
        for pmc,r in manifest['references'].items():
            key=pmc+' source '+r['sha256'][:12]
            prior_ref=db.execute('SELECT id FROM scientific_references WHERE source_document=?',(key,)).fetchone()
            refs[pmc]=prior_ref[0] if prior_ref else insert(db,'scientific_references',source_document=key,citation=r['title']+' | DOI '+r['doi']+' | '+r['url'],sha256=r['sha256'],notes='NCBI PMC primary study; retained JATS or explicitly transcribed source PDF and source hashes. '+r['license'])
        for p in manifest['profiles']:
            db.execute('INSERT OR IGNORE INTO plant_species(name) VALUES (?)',(p['species'],));sid=db.execute('SELECT id FROM plant_species WHERE name=?',(p['species'],)).fetchone()[0]
            db.execute('INSERT OR IGNORE INTO essential_oils(species_id,name) VALUES (?,?)',(sid,p['species']));oid=db.execute('SELECT id FROM essential_oils WHERE name=?',(p['species'],)).fetchone()[0]
            if p.get('common_name'):db.execute('UPDATE essential_oils SET common_name=COALESCE(common_name,?) WHERE id=?',(p['common_name'],oid))
            pname=p['species']+' — '+p['label']+' ['+p['pmcid']+']'
            if db.execute('SELECT 1 FROM oil_profiles WHERE name=?',(pname,)).fetchone():raise ValueError('Profile exists under a different manifest hash: '+pname)
            pid=insert(db,'oil_profiles',oil_id=oid,name=pname,plant_part=p['part'],method=p['method'],origin=p['origin'],profile_type=p['type'],reference_id=refs[p['pmcid']],notes=p['notes'],quantitation_basis=p['basis'],ranking_eligible=int(p['rankable']),geography_status=p['geography_status'],extraction_method=p.get('extraction_method'),analytical_method=p.get('analytical_method'))
            category=p.get('category') or ('Fixed Oils' if 'fatty' in p['type'].lower() or 'fixed' in p['type'].lower() else 'Essential Oils' if p['type'] in ['Essential oil','Extracted oil profile'] else 'Resins and Aromatic Preparations' if 'resin' in p['type'].lower() else 'Botanical Extracts')
            if category not in ['Essential Oils','Fixed Oils','Botanical Extracts','Resins and Aromatic Preparations','Individual Natural Compounds']:raise ValueError('Unknown botanical preparation category')
            db.execute('UPDATE oil_profiles SET preparation_category=? WHERE id=?',(category,pid))
            for o in p['observations']:
                key=identity_key(o['name'])
                if key not in compounds:
                    cid=insert(db,'chemical_compounds',name=standardized(o['name']),identity_status='unresolved',identity_notes='Published annotation; structure identity and stereochemistry require validation');compounds[key]=cid;new_ids.append(cid)
                cid=compounds[key];pct=o['value'] if o['unit']=='GC peak area %' else None
                insert(db,'profile_compounds',profile_id=pid,compound_id=cid,original_name=o['original_name'],percentage=pct,sd=o.get('sd'),value_status=o['status'],chemical_class=o.get('class',''),reference_id=refs[p['pmcid']],source_table=p['table_number'],source_row=o['source_row'],original_row=json.dumps(o['raw'],ensure_ascii=False),notes='Table '+p['table_id']+'; '+o.get('notes',''),confidence='Published analytical annotation; not independent experimental confirmation',validation_status='literature_transcribed',reported_value=o['value'],reported_unit=o['unit'],annotation_level=o['annotation'])
                if o.get('formula'):db.execute('UPDATE profile_compounds SET reported_formula=? WHERE id=last_insert_rowid()',(o['formula'],))
                if o.get('docking_eligible') is False:db.execute('UPDATE profile_compounds SET docking_eligible=0 WHERE id=last_insert_rowid()')
                observations+=1
        summary={'manifest':path.name,'sha256':digest,'before':before,'after':counts(db),'new_compound_ids':new_ids,'observations':observations,'profiles':len(manifest['profiles']),'references':len(refs)}
        insert(db,'literature_imports',sha256=digest,manifest_name=path.name,summary=json.dumps(summary));db.execute('RELEASE SAVEPOINT literature');db.commit();return summary
    except BaseException:db.execute('ROLLBACK TO SAVEPOINT literature');db.execute('RELEASE SAVEPOINT literature');raise
