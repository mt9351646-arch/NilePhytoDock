"""Corresponding source for a maintenance release, preserving prior archives."""
import hashlib,json,zipfile
from pathlib import Path
from app.branding import VERSION
ROOT=Path(__file__).resolve().parents[1]

def main():
 out=ROOT/'release/source_access';out.mkdir(parents=True,exist_ok=True)
 target=out/f'NilePhytoDock-v{VERSION}-Corresponding-Source.zip'
 files={}
 for folder in ['app','database','scientific','visualization','reporting','tests']:
  for p in (ROOT/folder).rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':files[p.relative_to(ROOT).as_posix()]=p
 for name in ['NilePhytoDock.py','pyproject.toml','requirements.txt','LICENSE','LICENSES.md','LICENSE_AUDIT.md','SOURCE_ACCESS.md','THIRD_PARTY_SOURCES.json','README.md','SOFTWARE_SUMMARY.md','CHANGELOG.md','FOLDER_GUIDE.md','build/NilePhytoDock-release.spec','build/windows_version.txt','build/Setup.cs','tools/build_v1_setup.py','tools/packaging_inputs.py','tools/package_update_sources.py','tools/verify_frozen_source.py','tools/validate_visual_update.py','tools/benchmark_responsiveness.py','tools/run_packaged_update_qa.py',f'docs/Release_Notes_v{VERSION}.md',f'docs/Release_v{VERSION}_EN.md',f'docs/Validation_v{VERSION}.md','docs/README.md']:
  files[name]=ROOT/name
 payload=ROOT/f'build/release_stage/v{VERSION}/application/_internal'
 for folder in ['data','external_tools']:
  for p in (payload/folder).rglob('*'):
   if p.is_file():files[p.relative_to(payload).as_posix()]=p
 files['BUILD_FROM_SOURCE.md']=ROOT/'public_site/source/BUILD_FROM_SOURCE.md'
 for name in ['docs/Release_v1.0.0_EN.md','docs/Packaging_Validation_v1.0.0.md','docs/Release_Notes_v1.0.1.md']:
  files[name]=ROOT/name
 for p in (ROOT/'build/runtime').iterdir():
  if p.is_file():files[p.relative_to(ROOT).as_posix()]=p
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as z:
  for name,p in sorted(files.items()):z.write(p,name)
 with zipfile.ZipFile(target) as z:assert z.testzip() is None
 h=hashlib.sha256(target.read_bytes()).hexdigest()
 record={'version':VERSION,'file':target.name,'bytes':target.stat().st_size,'sha256':h,'dependencies':'https://github.com/ahmedGSoliman99/NilePhytoDock-Source/releases/tag/v1.0.0','note':'Unchanged native and Python dependency sources remain in the v1.0.0 source release; complete pinned Chromium source is linked in THIRD_PARTY_SOURCES.json.'}
 (out/f'SOURCE_ARCHIVES-v{VERSION}.json').write_text(json.dumps(record,indent=2),encoding='utf-8');(out/f'SHA256SUMS-v{VERSION}.txt').write_text(h+'  '+target.name+'\n',encoding='utf-8');print(json.dumps(record,indent=2))
if __name__=='__main__':main()
