"""Explicit document adapters. No positional layout guessing across sources."""
import csv
import hashlib
import json
import re
from pathlib import Path
from docx import Document
from database.store import connect, insert, counts, rows

GREEK = str.maketrans({"α":"alpha", "β":"beta", "γ":"gamma", "δ":"delta", "τ":"tau", "−":"-", "–":"-", "‐":"-"})
ALIASES = {"1,8-cineole (eucalyptol)":"Eucalyptol", "1,8-cineole":"Eucalyptol", "iso borneol":"Isoborneol", "endo-borneol":"Borneol", "beta-myrcene":"Myrcene", "(-)-alpha-pinene":"(-)-alpha-Pinene", "1s-alpha-pinene (l-alpha-pinene)":"(-)-alpha-Pinene", "1r-alpha-pinene (d-alpha-pinene)":"(+)-alpha-Pinene"}

def standardized(name):
    clean = re.sub(r"\s+", " ", name.translate(GREEK)).strip()
    return ALIASES.get(clean.lower(), clean)

def value(text):
    text = text.strip()
    if not text:
        return None, None, "not_reported"
    if text in {"—", "–", "-"}:
        return None, None, "not_reported_or_not_detected"
    nums = re.findall(r"\d+(?:\.\d+)?", text)
    if not nums:
        return None, None, "review"
    percentage = float(nums[0]); sd = float(nums[1]) if "±" in text and len(nums)>1 else None
    return percentage, sd, "reported_zero" if percentage==0 else "reported"

def import_all(source, destination):
    db=connect(destination)
    if db.execute("SELECT count(*) FROM scientific_references").fetchone()[0]:
        raise ValueError("Import destination is already populated; use a new database for a reproducible rebuild.")
    for path in sorted(Path(source).glob("*.docx")):
        doc=Document(path); paras=[p.text for p in doc.paragraphs if p.text.strip()]
        ref=insert(db,"scientific_references",source_document=path.name,citation="\n".join(p for p in paras if any(k in p for k in ["doi", "DOI", "PMCID", "Source:", "Fikry", "Hashad", "Shahat", "Eldahshan", "Ali,", '"Comparative'])),notes="\n".join(paras),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        def profile(species, label, part, method, origin="Egypt", notes=""):
            db.execute("INSERT OR IGNORE INTO plant_species(name) VALUES (?)",(species,))
            sid=db.execute("SELECT id FROM plant_species WHERE name=?",(species,)).fetchone()[0]
            db.execute("INSERT OR IGNORE INTO essential_oils(species_id,name) VALUES (?,?)",(sid,species))
            oid=db.execute("SELECT id FROM essential_oils WHERE name=?",(species,)).fetchone()[0]
            return insert(db,"oil_profiles",oil_id=oid,name=f"{species} — {label}",plant_part=part,method=method,origin=origin,profile_type="Headspace volatile profile" if method=="HS" else "Extracted oil profile",reference_id=ref,notes=notes)
        def record(pid,name,text,ti,ri,row,cls="",note=""):
            if name.lower().startswith("total ") or "chemical class" in note.lower():
                insert(db,"extraction_audit",reference_id=ref,source_table=ti,source_row=ri,original_row=json.dumps(row,ensure_ascii=False),interpretation="Chemical-class total; excluded from compounds",profile_id=pid)
                return
            canon=standardized(name)
            db.execute("INSERT OR IGNORE INTO chemical_compounds(name) VALUES (?)",(canon,))
            cid=db.execute("SELECT id FROM chemical_compounds WHERE name=?",(canon,)).fetchone()[0]
            db.execute("INSERT OR IGNORE INTO compound_aliases(compound_id,original_name) VALUES (?,?)",(cid,name))
            pct,sd,status=value(text)
            flags=[]
            if pct is not None and not 0<=pct<=100: flags.append("percentage outside 0–100")
            if any(s in name.lower() for s in ["pentanediol","ambrial","hexenal","pseudo phytol"]): flags.append("unusual or ambiguous identity; manual review")
            if "Hedychium" in path.name: flags.append("source transcription incomplete; check original article before publication")
            if status=="reported_zero": flags.append("zero reported in source; detection limit/absolute absence unknown")
            insert(db,"profile_compounds",profile_id=pid,compound_id=cid,original_name=name,percentage=pct,sd=sd,value_status=status,chemical_class=cls,reference_id=ref,source_table=ti,source_row=ri,original_row=json.dumps(row,ensure_ascii=False),notes="; ".join([note]+flags),confidence="source transcription",validation_status="review" if flags else "extracted")
            insert(db,"extraction_audit",reference_id=ref,source_table=ti,source_row=ri,original_row=json.dumps(row,ensure_ascii=False),interpretation=status,profile_id=pid,compound_id=cid)
        tables=[[[c.text for c in r.cells] for r in t.rows] for t in doc.tables]
        used=set()
        if path.name.startswith("Lavender"):
            ps={}
            for ri,row in enumerate(tables[0][1:],2):
                label,_,_,name,pct,note=row
                if label not in ps: ps[label]=profile("Lavandula angustifolia",label,"Not specified for commercial product","Not specified for commercial product","Egyptian retail market; cultivation origin not reported")
                record(ps[label],name,pct,1,ri,row,note=note)
            used.add(0)
        elif path.name.startswith("Cotula"):
            ps=[profile("Cotula cinerea",label,"Aerial parts",method,origin) for label,method,origin in [("El Alamein — HD","HD","El Alamein, Egypt"),("El Alamein — MAE","MAE","El Alamein, Egypt"),("Red Sea — HD","HD","Red Sea, Egypt"),("Red Sea — MAE","MAE","Red Sea, Egypt")]]
            for ri,row in enumerate(tables[0][1:],2):
                for j,pid in enumerate(ps): record(pid,row[1],row[j+2],1,ri,row)
            used.add(0)
        elif path.name.startswith("Salvia"):
            ps=[profile("Salvia fruticosa",method,"Aerial parts",method,notes="HS describes headspace volatiles, not extracted oil.") for method in ["HD","HS","SF"]]
            for ri,row in enumerate(tables[0][1:],2):
                for j,pid in enumerate(ps): record(pid,row[1],row[j+2],1,ri,row)
            used.add(0)
        elif path.name.startswith("Rosemary"):
            for ti,species in enumerate(["Rosmarinus officinalis","Artemisia monosperma"]):
                ps=[profile(species,label,"Leaves","Distillation as reported in source",notes="Retains Table 3 values where article prose conflicts.") for label in ["Control","Salt affected"]]
                for ri,row in enumerate(tables[ti][1:],2):
                    for j,pid in enumerate(ps): record(pid,row[1],row[j+3],ti+1,ri,row,cls=row[2],note="RT="+row[0])
                used.add(ti)
        elif path.name.startswith("Hedychium"):
            for ti,table in enumerate(tables):
                species=["Hedychium coronarium","Alpinia zerumbet"][ti//4];part=["Leaves","Rhizomes"][(ti%4)//2];method=["HD","HS"][ti%2]
                pid=profile(species,f"{part} — {method}",part,method,notes="Visible transcription differs from reported abstract counts. Audit against original article required.")
                for ri,row in enumerate(table[1:],2): record(pid,row[1],row[2],ti+1,ri,row)
                used.add(ti)
        elif path.name.startswith(("Melaleuca","Pimenta")):
            ismq=path.name.startswith("Melaleuca")
            pid=profile("Melaleuca quinquenervia" if ismq else "Pimenta racemosa","Egyptian leaves","Leaves","HD" if ismq else "Extraction as reported in source","Shanbari, Oseem, Giza, Egypt" if ismq else "El-Zohrya Garden, Zamalek, Cairo, Egypt",notes="Source internal count/total discrepancy retained in reference notes.")
            for ri,row in enumerate(tables[0][1:],2):record(pid,row[1],row[2],1,ri,row,cls=row[3] if ismq else "")
            used.add(0)
        else: raise ValueError(f"No reviewed layout adapter for {path.name}")
        for ti,table in enumerate(tables):
            if ti in used: continue
            for ri,row in enumerate(table[1:],2): insert(db,"extraction_audit",reference_id=ref,source_table=ti+1,source_row=ri,original_row=json.dumps(row,ensure_ascii=False),interpretation="Reported summary/group total; excluded from compound library")
    db.commit()
    return db

def audit(db,folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    records=rows(db,"""SELECT pc.*,p.name AS profile,p.plant_part,p.method,p.origin,c.name AS standardized_name,r.source_document,r.citation FROM profile_compounds pc JOIN oil_profiles p ON p.id=pc.profile_id JOIN chemical_compounds c ON c.id=pc.compound_id JOIN scientific_references r ON r.id=pc.reference_id""")
    with (folder/"extraction_records.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    duplicates=rows(db,"SELECT profile_id,compound_id,count(*) AS occurrences FROM profile_compounds GROUP BY profile_id,compound_id HAVING count(*)>1")
    unresolved=rows(db,"SELECT c.*,s.status AS structure_status,s.notes FROM chemical_compounds c LEFT JOIN compound_structures s ON s.compound_id=c.id WHERE s.status IS NULL OR s.status!='ready'")
    if unresolved:
        with (folder/'unresolved_compounds.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(unresolved[0]));writer.writeheader();writer.writerows(unresolved)
    sums=rows(db,"SELECT p.id,p.name,sum(pc.percentage) AS reported_sum,count(pc.id) AS records FROM oil_profiles p JOIN profile_compounds pc ON pc.profile_id=p.id GROUP BY p.id")
    report={"counts":counts(db),"documents":rows(db,"SELECT source_document,sha256 FROM scientific_references"),"duplicates":duplicates,"unresolved":unresolved,"profile_totals":sums,"notes":["All values are source-reported relative peak areas, not mass percentages.","Dash status is retained as ambiguous not reported/not detected where the source does not distinguish.","Chemical-class totals are retained in extraction_audit, never screened as compounds.","Hedychium/Alpinia transcription contains 186 listed rows rather than 196 abstract detections; no missing values were invented.","Literature citations are transcribed from supplied documents; bibliographic claims have not been independently authenticated."]}
    report['duplicate_candidate_structures']=rows(db,"SELECT inchikey,count(*) AS name_records,group_concat(compound_id) AS compound_ids FROM compound_structures WHERE inchikey!='' GROUP BY inchikey HAVING count(*)>1")
    report['unique_ready_inchikeys']=db.execute("SELECT count(DISTINCT inchikey) FROM compound_structures WHERE status='ready'").fetchone()[0]
    (folder/"database_validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return report

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--source",default=".");p.add_argument("--database",default="data/nilephytodock.sqlite");a=p.parse_args()
    db=import_all(a.source,a.database);print(json.dumps(audit(db,"data/validation")["counts"]))
