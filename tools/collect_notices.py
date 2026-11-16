from pathlib import Path
import importlib.metadata as md,shutil,json,platform,hashlib
out=Path('external_tools/licenses/python_packages');out.mkdir(parents=True,exist_ok=True)
for dist in md.distributions():
 for f in dist.files or []:
  if any(word in Path(str(f)).name.lower() for word in ['license','copying','notice']) and ('.dist-info/' in str(f).replace('\\','/') or '.egg-info/' in str(f).replace('\\','/')):
   src=dist.locate_file(f)
   if src.is_file():
    dest=out/dist.metadata['Name']/Path(str(f)).name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
manifest={'platform':platform.platform(),'python':platform.python_version(),'packages':{d.metadata['Name']:d.version for d in md.distributions()},'assets':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('app/resources/3Dmol-min.js'),Path('external_tools/p2rank/bin/p2rank.jar'),Path('external_tools/smina/smina.exe')]}}
Path('data/validation/environment.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
