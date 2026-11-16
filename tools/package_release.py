"""Package a verified portable release, tracked source and complete case evidence."""
from pathlib import Path
import hashlib,json,subprocess,zipfile

from app.branding import VERSION
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'release'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write_zip(path,items):
 if path.exists():raise FileExistsError('Preserve prior archives: '+str(path))
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as archive:
  for p,name in sorted(items,key=lambda x:x[1]):archive.write(p,name)
 with zipfile.ZipFile(path) as archive:
  assert archive.testzip() is None
 print(path.name,path.stat().st_size,'bytes',len(items),'files',flush=True)
 return {'name':path.name,'bytes':path.stat().st_size,'sha256':sha(path)}
def main():
 verified=json.loads((ROOT/'data/validation'/('release_'+VERSION)/'verification.json').read_text());assert verified['native_installation']['success']
 portable=OUT/f'NilePhytoDock Studio {VERSION}';assert sha(portable/'NilePhytoDock.exe')==verified['exe_sha256']
 artifacts=[]
 artifacts.append(write_zip(OUT/f'NilePhytoDock-{VERSION}-Windows-x64.zip',[(p,p.relative_to(OUT).as_posix()) for p in portable.rglob('*') if p.is_file() and p.suffix.lower()!='.lnk']))
 git=r'C:\Program Files\Git\cmd\git.exe';tracked=subprocess.check_output([git,'ls-files','-z'],cwd=ROOT).decode('utf-8').split('\0');source={ROOT/name:name for name in tracked if name}
 for p in (ROOT/'external_tools').rglob('*'):
  if p.is_file():source[p]=p.relative_to(ROOT).as_posix()
 artifacts.append(write_zip(OUT/f'NilePhytoDock-{VERSION}-source.zip',[(p,f'NilePhytoDock-{VERSION}-source/'+name) for p,name in source.items()]))
 case=ROOT/'data/validation/case_study_final';caseitems=[(p,'case_study_final/'+p.relative_to(case).as_posix()) for p in case.rglob('*') if p.is_file() and not p.name.endswith(('-wal','-shm'))]
 artifacts.append(write_zip(OUT/f'NilePhytoDock-{VERSION}-case-data.zip',caseitems))
 docs=portable/'Documentation';artifacts.append(write_zip(OUT/f'NilePhytoDock-{VERSION}-Documentation.zip',[(p,'Documentation/'+p.name) for p in docs.iterdir() if p.is_file()]))
 manifest={'version':VERSION,'developers':['Ahmed G Soliman','Malak Taha'],'source_commit':subprocess.check_output([git,'rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'executable_sha256':verified['exe_sha256'],'assets':artifacts}
 (OUT/f'release-manifest-{VERSION}.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 entries=artifacts+[{'name':f'release-manifest-{VERSION}.json','sha256':sha(OUT/f'release-manifest-{VERSION}.json')}]
 (OUT/f'SHA256SUMS-{VERSION}.txt').write_text(''.join(a['sha256']+'  '+a['name']+'\n' for a in entries),encoding='utf-8')
 print('All four archives verified by full CRC and hashed',flush=True)
if __name__=='__main__':main()
