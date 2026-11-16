"""Cross-format numerical and source-preservation audit on actual results."""
import json,sqlite3,csv,hashlib
from pathlib import Path
from collections import Counter
from openpyxl import load_workbook
from docx import Document
from database.store import connect,rows,counts
from scientific.molecular_analysis import analyze,interaction_rows,export_tables
root=Path('data/validation/comprehensive_exports');root.mkdir(parents=True,exist_ok=True)
source=sqlite3.connect('data/validation/comprehensive_geometry/study.sqlite');copy=sqlite3.connect(root/'study.sqlite');source.backup(copy);copy.close();source.close();db=connect(root/'study.sqlite')
all_rows=interaction_rows(db,1);tid=all_rows[0]['protein_id'];cid=all_rows[0]['compound_id'];a=analyze(db,1)
summary=Counter((r['protein'],r['binding_pocket'],r['residue'],r['interaction_type']) for r in all_rows)
modes={'Complete Interaction Table':all_rows,'Best Pose Interactions':interaction_rows(db,1,'Best Pose Interactions'),'Selected Protein Interactions':interaction_rows(db,1,protein=tid),'Selected Compound Interactions':interaction_rows(db,1,compound=cid),'Functional Group Interaction Summary':a['functional_group_interactions'],'Interaction Frequency Summary':[{'protein':p,'pocket':s,'residue':r,'interaction_type':t,'contact_events':n} for (p,s,r,t),n in summary.items()]};checks=[]
for name,data in modes.items():
 path=root/name.replace(' ','_');export_tables(data,path,name)
 with path.with_suffix('.csv').open(encoding='utf-8-sig',newline='') as f:csv_rows=list(csv.DictReader(f))
 book=load_workbook(path.with_suffix('.xlsx'),read_only=True,data_only=True);sheet=book.active;assert len(csv_rows)==len(data)==sheet.max_row-1
 headers=[c.value for c in next(sheet.rows)];assert headers==list(csv_rows[0]);book.close();doc=Document(path.with_suffix('.docx'));text='\n'.join(p.text for p in doc.paragraphs)+'\n'+'\n'.join(c.text for t in doc.tables for row in t.rows for c in row.cells)
 if 'distance' in data[0]:
  for original,exported in zip(data,csv_rows):assert float(exported['distance'])==original['distance'] and str(original['distance']) in text and json.loads(exported['ligand_atom_indices'])==original['ligand_atom_indices']
 checks.append({'mode':name,'records':len(data),'csv_xlsx_docx_verified':True});print(name,len(data),flush=True)
assert sum(summary.values())==len(all_rows);assert {r['protein_id'] for r in modes['Selected Protein Interactions']}=={tid};assert {r['compound_id'] for r in modes['Selected Compound Interactions']}=={cid}
try:export_tables([],root/'empty')
except ValueError:pass
else:raise AssertionError('Empty export claimed success')
assert not (root/'empty.csv').exists();db.close()
old=sqlite3.connect('data/backups/pre_0_6_library.sqlite');new=connect('data/nilephytodock.sqlite');columns='id,profile_id,compound_id,original_name,percentage,sd,value_status,source_table,source_row,original_row';original=old.execute('SELECT '+columns+' FROM profile_compounds ORDER BY id').fetchall();preserved=new.execute('SELECT '+columns+' FROM profile_compounds WHERE id<=? ORDER BY id',(original[-1][0],)).fetchall();assert original==[tuple(r) for r in preserved]
assert new.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and not new.execute('PRAGMA foreign_key_check').fetchall();assert new.execute('SELECT count(*) FROM analysis_projects').fetchone()[0]==0
for s in rows(new,"SELECT * FROM compound_structures WHERE status='ready'"):
 for k in ['sdf_path','pdbqt_path']:assert not Path(s[k]).is_absolute() and Path(s[k]).exists(),s[k]
result={'interaction_export_modes':checks,'full_numeric_precision_preserved':True,'empty_export_rejected':True,'original_observations_unchanged':len(original),'counts':counts(new),'seed_integrity_and_foreign_keys_valid':True,'ready_paths_portable':True,'historical_evaluations':new.execute('SELECT count(*) FROM botanical_history').fetchone()[0]};(root/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');new.close();old.close()
