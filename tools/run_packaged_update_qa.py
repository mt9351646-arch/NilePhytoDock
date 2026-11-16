"""Install and exercise the final Setup with developer runtimes removed from PATH."""
import os,json,time,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from app.branding import VERSION
def main():
 setup=ROOT/f'release/NilePhytoDock-v{VERSION}-Setup.exe';installed=Path(r'C:\Users\PC\AppData\Local\Programs\NilePhytoDockStudio')
 output=Path(r'C:\Users\PC\AppData\Local\NilePhytoDockReleaseQA')/(f'v{VERSION} Results Ω')
 attempt=1
 while output.exists():
  attempt+=1;output=output.parent/(f'v{VERSION} Verified Results {attempt} Ω')
 output.mkdir(parents=True);env=os.environ.copy()
 for name in ['PYTHONPATH','PYTHONHOME','JAVA_HOME','QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH','QML2_IMPORT_PATH','QTWEBENGINEPROCESS_PATH','QT_QPA_PLATFORM']:
  env.pop(name,None)
 env['PATH']=r'C:\Windows\System32;C:\Windows';env['NILEPHYTODOCK_DATA']=str(output/'userdata')
 start=time.monotonic();subprocess.run([str(setup),'--install',str(installed)],env=env,check=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW);installation=time.monotonic()-start
 start=time.monotonic()
 with (output/'packaged-process.log').open('w',encoding='utf-8') as log:
  subprocess.run([str(installed/'NilePhytoDock.exe'),'--verify-installation',str(output),str(ROOT/'tests/fixtures/3PTB.pdb'),'--verify-visual-update'],cwd=installed,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=900)
 evidence=json.loads((output/'verification.json').read_text(encoding='utf-8'));assert evidence['success'] and evidence['frozen'] and evidence['version']==VERSION and evidence['actual_docking_runs']==3
 close=output/'one-close';subprocess.run([str(installed/'NilePhytoDock.exe'),'--verify-close',str(close),str(ROOT/'tests/fixtures/3PTB.pdb')],cwd=installed,env=env,check=True,timeout=70)
 lifecycle=json.loads((close/'verification.json').read_text(encoding='utf-8'));assert lifecycle['success'] and lifecycle['frozen'] and lifecycle['hidden_after_one_close'] and lifecycle['close_seconds']<5
 record={'version':VERSION,'setup_sha256':hashlib.sha256(setup.read_bytes()).hexdigest(),'installed_exe_sha256':hashlib.sha256((installed/'NilePhytoDock.exe').read_bytes()).hexdigest(),'installation_seconds':installation,'native_verification_seconds':time.monotonic()-start,'output':str(output),'restricted_path':True,'evidence':evidence,'lifecycle':lifecycle}
 (ROOT/('data/validation/v'+VERSION.replace('.','_')+'_packaged_verification.json')).write_text(json.dumps(record,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in record.items() if k!='evidence'},indent=2),flush=True)
if __name__=='__main__':main()
