"""Verify the final Windows distribution against native installation evidence."""
import json,hashlib,sqlite3,struct
from pathlib import Path
import pefile
from rdkit import Chem
from database.store import counts
from app.branding import VERSION
ROOT=Path(__file__).resolve().parents[1]
qa=ROOT/'data/validation'/('release_'+VERSION)
root=ROOT/('release/NilePhytoDock Studio '+VERSION);exe=root/'NilePhytoDock.exe';pe=pefile.PE(str(exe));props={}
for group in pe.FileInfo:
 for entry in group:
  for table in getattr(entry,'StringTable',[]):props.update({k.decode():v.decode() for k,v in table.entries.items()})
assert props['ProductVersion']==VERSION and props['CompanyName']=='Ahmed G Soliman; Malak Taha',props
ico=(root/'NilePhytoDock.ico').read_bytes();n=struct.unpack_from('<H',ico,4)[0];assert n==7;embedded=[]
for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries:
 if kind.id==3:
  for name in kind.directory.entries:
   for lang in name.directory.entries:
    s=lang.data.struct;embedded.append(pe.get_data(s.OffsetToData,s.Size))
for i in range(n):
 size,offset=struct.unpack_from('<II',ico,6+16*i+8);assert ico[offset:offset+size] in embedded
shortcuts=json.loads((qa/'shortcuts.json').read_text(encoding='utf-8-sig'));assert len(shortcuts)==2
assert all(Path(s['Target']).resolve()==exe.resolve() for s in shortcuts)
assert all(s['Icon'].lower()==(str(root/'NilePhytoDock.ico')+',0').lower() for s in shortcuts)
assert not (root/'_internal/docs').exists()
guides={}
for source in (ROOT/'docs').iterdir():
 if not source.is_file() or '_AR.' in source.name or source.name in {'USER_GUIDE.pdf','IMPLEMENTATION_PLAN.md'}:continue
 destination=root/'Documentation'/source.name
 assert destination.exists(),destination
 digest=hashlib.sha256(source.read_bytes()).hexdigest();assert hashlib.sha256(destination.read_bytes()).hexdigest()==digest;guides[source.name]=digest
assert not list((root/'Documentation').glob('*_AR*'))
native=json.loads((qa/'install/verification.json').read_text());assert native['success'] and native['frozen'] and native['version']==VERSION and native['actual_docking_runs']==3,native
assert all(native[k] for k in ['oil_first_results_verified','functional_group_summary_verified','dedicated_3d_page','separate_fullscreen_3d_window'])
seed=sqlite3.connect((root/'_internal/data/nilephytodock.sqlite').as_uri()+'?mode=ro',uri=True);seed.row_factory=sqlite3.Row
assert seed.execute('SELECT count(*) FROM analysis_projects').fetchone()[0]==0
assert seed.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and not seed.execute('PRAGMA foreign_key_check').fetchall()
c=counts(seed);assert c=={'botanical_oils':57,'essential_oils':46,'fixed_oils':11,'species':68,'profiles':119,'compounds':819,'ready':186,'unique_ready':164,'records':2109},c
keys=set()
for structure in seed.execute("SELECT * FROM compound_structures WHERE status='ready'"):
 for key in ['sdf_path','pdbqt_path']:assert not Path(structure[key]).is_absolute() and (root/'_internal'/structure[key]).exists()
 assert Chem.MolToInchiKey(Chem.MolFromSmiles(structure['smiles']))==structure['inchikey'];keys.add(structure['inchikey'])
assert len(keys)==164;seed.close()
resources=[]
for p in (ROOT/'app/resources').rglob('*'):
 if p.is_file():
  dest=root/'_internal'/p.relative_to(ROOT);assert dest.exists() and hashlib.sha256(dest.read_bytes()).digest()==hashlib.sha256(p.read_bytes()).digest();resources.append(p.relative_to(ROOT).as_posix())
result={'version':VERSION,'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'entry_point':str(exe),'properties':props,'matching_embedded_icon_sizes':n,'shortcut_icons_verified':True,'external_english_documentation':guides,'manuals_not_embedded':True,'counts':c,'seed_contains_no_projects':True,'ready_structure_inchikeys_and_portable_files_verified':len(keys),'own_resources_match_source':resources,'native_installation':native,'windows_10_tested':False,'clean_vm_tested':False,'code_signed':False}
(qa/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('Final '+VERSION+' release verified: 164 structures, actual frozen P2Rank/Smina, seven icon sizes and external documentation')
