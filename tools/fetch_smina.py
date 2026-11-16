import urllib.request,json,concurrent.futures,hashlib
from pathlib import Path
repo='fhh2626/BFEE-Docking'
commit=json.loads(Path('external_tools/smina/provenance.json').read_text())['commit'] if Path('external_tools/smina/provenance.json').exists() else '6bb8d06df67e8ca3077622bbb208fac51be0bb30'
tree=json.load(urllib.request.urlopen(f'https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1'))['tree']
files=[x for x in tree if x['path'].startswith('bfee_docking/third_party/smina/') and x['type']=='blob' and not x['path'].endswith('/smina')]
dest=Path('external_tools/smina');dest.mkdir(parents=True,exist_ok=True)
def fetch(x):
 name=Path(x['path']).name;p=dest/name
 if not p.exists():urllib.request.urlretrieve(f"https://raw.githubusercontent.com/{repo}/{commit}/{x['path']}",p)
 return {'file':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'upstream_path':x['path']}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: records=list(pool.map(fetch,files))
Path('external_tools/smina/provenance.json').write_text(json.dumps({'repository':repo,'commit':commit,'files':records},indent=2))
print('Downloaded',len(records),'native runtime files at',commit)
