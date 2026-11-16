"""Package the already frozen application as one per-user Windows setup download."""
from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile,html,re

ROOT=Path(__file__).resolve().parents[1]
from app.branding import VERSION
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def main():
 stage=ROOT/('build/release_stage/v'+VERSION);stage.mkdir(parents=True,exist_ok=True)
 app=stage/'application';shutil.copytree(ROOT/'dist_v1_install/NilePhytoDock',app,dirs_exist_ok=True)
 from tools.packaging_inputs import smina_files,p2rank_jar_keep
 native=app/'_internal/external_tools/smina';allowed={p.name.lower() for p in smina_files(ROOT/'external_tools/smina')}
 for p in native.iterdir():
  assert p.resolve().is_relative_to(stage.resolve())
  if p.is_file() and p.name.lower() not in allowed:p.unlink()
 for p in (app/'_internal/external_tools/p2rank/bin/lib').glob('*.jar'):
  assert p.resolve().is_relative_to(stage.resolve())
  if not p2rank_jar_keep(p.name):p.unlink()
 docs=app/'Documentation';docs.mkdir(exist_ok=True)
 for name in ['LICENSE','LICENSES.md','SOURCE_ACCESS.md','LICENSE_AUDIT.md','THIRD_PARTY_SOURCES.json']:
  if (ROOT/name).exists():shutil.copy2(ROOT/name,docs/name)
 shutil.copy2(ROOT/('docs/Release_v'+VERSION+'_EN.md'),docs/'User_Guide_EN.md')
 text=(docs/'User_Guide_EN.md').read_text(encoding='utf-8');blocks=[]
 for para in text.split('\n\n'):
  escaped=html.escape(para);escaped=re.sub(r'\[([^\]]+)\]\((https://[^)]+)\)',r'<a href="\2">\1</a>',escaped);escaped=re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',escaped);escaped=re.sub(r'`([^`]+)`',r'<code>\1</code>',escaped)
  if para.startswith('# '):blocks.append('<h1>'+escaped[2:]+'</h1>')
  elif para.startswith('## '):blocks.append('<h2>'+escaped[3:]+'</h2>')
  else:blocks.append('<p>'+escaped.replace('\n','<br>')+'</p>')
 (docs/'User_Guide_EN.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>NilePhytoDock Studio v'+VERSION+' — User Guide</title><style>body{font:16px/1.65 "Segoe UI",sans-serif;max-width:960px;margin:45px auto;padding:0 28px;color:#22364b}h1,h2{color:#087f83}h2{margin-top:35px}a{color:#00779b}code{background:#eef3f8;padding:2px 5px}</style>'+''.join(blocks)+'</html>',encoding='utf-8')
 # Collect the complete retained notices after freezing, including JAR license texts.
 license_target=app/'_internal/external_tools/licenses'
 assert license_target.resolve().is_relative_to(stage.resolve())
 if license_target.exists():shutil.rmtree(license_target)
 shutil.copytree(ROOT/'external_tools/licenses',license_target)
 for name in ['LICENSE','LICENSES.md','SOURCE_ACCESS.md']:
  shutil.copy2(ROOT/name,app/'_internal/legal'/name)
 compiler=Path(r'C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe')
 common=[str(compiler),'/nologo','/target:winexe','/platform:x64','/codepage:65001','/reference:System.IO.Compression.dll','/reference:System.IO.Compression.FileSystem.dll','/reference:System.Drawing.dll','/reference:System.Windows.Forms.dll']
 subprocess.run(common+['/out:'+str(app/'NilePhytoDockMaintenance.exe'),str(ROOT/'build/Setup.cs')],check=True)
 payload=stage/'payload.zip';files=[p for p in app.rglob('*') if p.is_file()]
 with zipfile.ZipFile(payload,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for p in sorted(files):z.write(p,p.relative_to(app).as_posix())
 with zipfile.ZipFile(payload) as z:assert z.testzip() is None
 final=ROOT/('release/NilePhytoDock-v'+VERSION+'-Setup.exe')
 subprocess.run(common+['/out:'+str(final),'/win32icon:'+str(ROOT/'app/resources/brand/NilePhytoDock-Studio.ico'),'/resource:'+str(payload)+',NilePhytoDock.Payload','/resource:'+str(ROOT/'app/resources/brand/NilePhytoDock-Studio.ico')+',NilePhytoDock.Icon','/resource:'+str(ROOT/'app/resources/brand/NilePhytoDock-logo.png')+',NilePhytoDock.Logo','/resource:'+str(ROOT/'SOURCE_ACCESS.md')+',NilePhytoDock.License',str(ROOT/'build/Setup.cs')],check=True)
 record={'version':VERSION,'setup':str(final),'download_bytes':final.stat().st_size,'download_file_count':1,'sha256':sha(final),'installed_payload_files':len(files),'installed_payload_bytes':sum(p.stat().st_size for p in files),'payload_zip_bytes':payload.stat().st_size,'application_sha256':sha(app/'NilePhytoDock.exe'),'method':'PyInstaller onedir with a single .NET Framework per-user setup executable','developers':['Ahmed G Soliman','Malak Taha']}
 (ROOT/('data/validation/v'+VERSION.replace('.','_')+'_setup_build.json')).write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
if __name__=='__main__':main()
