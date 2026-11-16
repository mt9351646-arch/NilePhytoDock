"""Reviewed adapter for the supplied combined CSV, preserving prior sources."""
import csv,hashlib,json,math,re
from pathlib import Path
from database.store import insert,rows,counts
from database.import_documents import standardized

HEADERS=['Plant Species / Oil Name','Scientific Name','Part Used','Country/Region Grown','Specific Condition/Method/Product Name','Compound Name','Relative Percentage (%)','Standard Deviation (SD) / Range / Note','Reference / Source Document']

def identity_key(name):
    return re.sub(r'\s+',' ',standardized(name)).casefold()

def profile_identity(r):
    oil=r[HEADERS[0]];method=r[HEADERS[4]];region=r[HEADERS[3]]
    species=next((s for s in ['Origanum syriacum','Hedychium coronarium','Alpinia zerumbet','Pimenta racemosa','Artemisia monosperma','Salvia fruticosa','Cotula cinerea','Melaleuca quinquenervia'] if s in r[HEADERS[1]]),None)
    if species is None:species='Nigella sativa' if 'Nigella' in r[HEADERS[1]] else 'Rosmarinus officinalis'
    if species in ['Hedychium coronarium','Alpinia zerumbet']:
        m='HS' if 'Headspace' in method else 'HD';label=('Leaves' if 'Leaves' in oil else 'Rhizomes')+' — '+m
    elif species=='Cotula cinerea':m='MAE' if 'Microwave' in method else 'HD';label=('Red Sea' if 'Red Sea' in region else 'El Alamein')+' — '+m
    elif species=='Salvia fruticosa':m='HS' if 'Headspace' in method else 'SF' if 'Supercritical' in method else 'HD';label=m
    elif species in ['Artemisia monosperma','Rosmarinus officinalis'] and 'El-Gamal' not in oil:m='Distillation as reported in source';label='Salt affected' if 'Salt-affected' in oil else 'Control'
    elif species in ['Melaleuca quinquenervia','Pimenta racemosa']:m='HD' if 'Melaleuca' in species else 'Extraction as reported in source';label='Egyptian leaves'
    else:m=method;label=oil+' — '+method
    return species,f'{species} — {label}',m

def import_csv(db,path):
    path=Path(path);digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=HEADERS:raise ValueError('CSV headers differ from the reviewed combined-oils schema')
        records=list(reader)
    for n,r in enumerate(records,2):
        try:v=float(r[HEADERS[6]])
        except ValueError:raise ValueError(f'CSV row {n}: invalid percentage')
        if not math.isfinite(v) or not 0<=v<=100:raise ValueError(f'CSV row {n}: percentage outside 0–100')
        if not r[HEADERS[5]].strip():raise ValueError(f'CSV row {n}: missing compound name')
    prior=db.execute('SELECT summary FROM csv_imports WHERE sha256=?',(digest,)).fetchone()
    if prior:return {**json.loads(prior[0]),'already_imported':True}
    before=counts(db);summary={'source':path.name,'sha256':digest,'source_rows':len(records),'duplicate_records':0,'review_records':0,'new_composition_records':0}
    db.execute('SAVEPOINT csv_import')
    try:
        ref=insert(db,'scientific_references',source_document=path.name+' [sha256 '+digest[:12]+']',citation='\n'.join(dict.fromkeys(r[HEADERS[8]] for r in records)),sha256=digest,notes='Supplied combined CSV; original seven Word datasets preserved. All CSV rows retained in csv_composition_records. Non-identical records for pre-existing profiles require review and do not overwrite or double-weight the original composition.')
        existing_profiles={r['name']:r['id'] for r in rows(db,'SELECT id,name FROM oil_profiles')};new_profiles=set()
        compound_map={identity_key(r['name']):r['id'] for r in rows(db,'SELECT id,name FROM chemical_compounds')}
        for r in rows(db,'SELECT original_name,compound_id FROM compound_aliases'):compound_map.setdefault(identity_key(r['original_name']),r['compound_id'])
        for n,r in enumerate(records,2):
            species,pname,method=profile_identity(r)
            if pname not in existing_profiles:
                db.execute('INSERT OR IGNORE INTO plant_species(name) VALUES (?)',(species,));sid=db.execute('SELECT id FROM plant_species WHERE name=?',(species,)).fetchone()[0]
                db.execute('INSERT OR IGNORE INTO essential_oils(species_id,name) VALUES (?,?)',(sid,species));oid=db.execute('SELECT id FROM essential_oils WHERE name=?',(species,)).fetchone()[0]
                pid=insert(db,'oil_profiles',oil_id=oid,name=pname,plant_part=r[HEADERS[2]],method=method,origin=r[HEADERS[3]],profile_type='Headspace volatile profile' if method=='HS' else 'Extracted oil profile',reference_id=ref,notes='Imported from supplied combined CSV; oil content is separate metadata, not a constituent percentage.')
                existing_profiles[pname]=pid;new_profiles.add(pid)
            pid=existing_profiles[pname];name=r[HEADERS[5]].strip();key=identity_key(name)
            if key not in compound_map:
                cid=insert(db,'chemical_compounds',name=standardized(name),identity_status='unresolved',identity_notes='New CSV identity requires structure validation');compound_map[key]=cid
            cid=compound_map[key];db.execute('INSERT OR IGNORE INTO compound_aliases(compound_id,original_name) VALUES (?,?)',(cid,name))
            pct=float(r[HEADERS[6]]);original=json.dumps(r,ensure_ascii=False)
            matches=rows(db,'SELECT id,percentage FROM profile_compounds WHERE profile_id=? AND compound_id=?',(pid,cid))
            same=next((m for m in matches if m['percentage'] is not None and abs(m['percentage']-pct)<1e-7),None)
            pcid=same['id'] if same else None
            if same:status='corroborated_existing';summary['duplicate_records']+=1
            elif pid in new_profiles:
                pcid=insert(db,'profile_compounds',profile_id=pid,compound_id=cid,original_name=name,percentage=pct,sd=None,value_status='reported_zero' if pct==0 else 'reported',chemical_class='',reference_id=ref,source_table=1,source_row=n,original_row=original,notes=r[HEADERS[7]],confidence='CSV transcription',validation_status='extracted')
                status='added';summary['new_composition_records']+=1
            else:status='source_difference_review';summary['review_records']+=1
            insert(db,'csv_composition_records',source_sha256=digest,source_row=n,profile_id=pid,compound_id=cid,profile_compound_id=pcid,percentage=pct,original_row=original,status=status)
        after=counts(db);summary.update(new_species=after['species']-before['species'],new_profiles=after['profiles']-before['profiles'],new_compounds=after['compounds']-before['compounds'],before=before,after=after)
        insert(db,'csv_imports',sha256=digest,source_name=path.name,summary=json.dumps(summary,ensure_ascii=False));db.execute('RELEASE SAVEPOINT csv_import');db.commit()
    except BaseException:db.execute('ROLLBACK TO SAVEPOINT csv_import');db.execute('RELEASE SAVEPOINT csv_import');raise
    return summary
