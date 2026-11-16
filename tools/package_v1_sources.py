"""Provide GPL build inputs separately from the researcher-facing setup download."""
from pathlib import Path
import hashlib,json,zipfile,subprocess

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'release/source_access';OUT.mkdir(exist_ok=True)
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def archive(path,items):
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as z:
  for file,name in items:z.write(file,name)
 with zipfile.ZipFile(path) as z:assert z.testzip() is None
 return {'file':path.name,'bytes':path.stat().st_size,'sha256':digest(path)}
def main():
 items=[]
 for folder in ['app','database','scientific','visualization','reporting']:
  items += [(p,p.relative_to(ROOT).as_posix()) for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
 for name in ['NilePhytoDock.py','pyproject.toml','requirements.txt','LICENSE','LICENSES.md','LICENSE_AUDIT.md','SOURCE_ACCESS.md','THIRD_PARTY_SOURCES.json','README.md','SOFTWARE_SUMMARY.md','CHANGELOG.md','build/NilePhytoDock-release.spec','build/windows_version.txt','build/Setup.cs','tools/build_v1_setup.py','tools/packaging_inputs.py','tools/package_v1_sources.py','tools/verify_frozen_source.py','docs/Release_v1.0.0_EN.md','docs/Packaging_Validation_v1.0.0.md']:
  items.append((ROOT/name,name))
 # Only shipped application data/native runtime; no user databases or QA records.
 payload=ROOT/'build/release_stage/v1.0.0/application/_internal'
 for folder in ['data','external_tools']:
  items += [(p,p.relative_to(payload).as_posix()) for p in (payload/folder).rglob('*') if p.is_file()]
 source_readme=ROOT/'public_site/source/BUILD_FROM_SOURCE.md'
 if not source_readme.exists():source_readme=ROOT/'BUILD_FROM_SOURCE.md'
 items.append((source_readme,'BUILD_FROM_SOURCE.md'))
 manifests=[archive(OUT/'NilePhytoDock-v1.0.0-Corresponding-Source.zip',items)]
 declared=json.loads((ROOT/'THIRD_PARTY_SOURCES.json').read_text())['archives'];vendors=[(ROOT/'external_tools/source_archives'/r['file'],'vendor_sources/'+r['file']) for r in declared];vendors += [(ROOT/'THIRD_PARTY_SOURCES.json','THIRD_PARTY_SOURCES.json'),(ROOT/'LICENSE_AUDIT.md','LICENSE_AUDIT.md')]
 manifests.append(archive(OUT/'NilePhytoDock-v1.0.0-Dependency-Sources.zip',vendors))
 for version in ['0.6.0','0.6.1']:
  original=ROOT/f'release/NilePhytoDock-{version}-source.zip';target=OUT/f'NilePhytoDock-{version}-Historical-Corresponding-Source.zip'
  if not original.exists():
   # Workspace cleanup keeps the already verified legal archive instead of
   # retaining a second full copy of every obsolete development distribution.
   if not target.exists():raise FileNotFoundError('Historical corresponding source is required: '+str(target))
   with zipfile.ZipFile(target) as z:assert z.testzip() is None
   manifests.append({'file':target.name,'bytes':target.stat().st_size,'sha256':digest(target)})
   continue
  with zipfile.ZipFile(original) as src,zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as dst:
   for n in src.namelist():
    rel='/'.join(n.split('/')[1:]);first=rel.split('/')[0]
    if not rel or n.endswith('/'):continue
    allowed=first in ['app','database','scientific','visualization','reporting','external_tools','build'] or rel in ['NilePhytoDock.py','pyproject.toml','requirements.txt','LICENSE','LICENSES.md'] or rel.startswith(('data/compound_library/','data/source_documents/','data/literature/')) or rel in ['data/nilephytodock.sqlite','data/validation/database_validation.json','data/validation/extraction_records.csv','data/validation/gui_smoke.png']
    if allowed and '__pycache__' not in rel and not rel.endswith(('.pyc','.log')):dst.writestr(rel,src.read(n))
   dst.writestr('SOURCE_ACCESS.md',(ROOT/'SOURCE_ACCESS.md').read_bytes());dst.writestr('HISTORICAL_BUILD.md',f'Original {version} application/build inputs, preserved without relabeling. User study outputs and unrelated development records are omitted. Native dependency sources and provenance are also available in the v1.0.0 dependency-source release.\n')
  with zipfile.ZipFile(target) as z:assert z.testzip() is None
  manifests.append({'file':target.name,'bytes':target.stat().st_size,'sha256':digest(target)})
 (OUT/'SOURCE_ARCHIVES.json').write_text(json.dumps({'release':'1.0.0','archives':manifests},indent=2));(OUT/'SHA256SUMS.txt').write_text(''.join(r['sha256']+'  '+r['file']+'\n' for r in manifests));print(json.dumps(manifests,indent=2))
if __name__=='__main__':main()
