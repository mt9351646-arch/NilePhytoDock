"""Compare all own modules in a final PyInstaller archive with current source."""
import sys,json,hashlib
from pathlib import Path
from types import CodeType
from PyInstaller.archive.readers import ZlibArchiveReader
ROOT=Path(__file__).resolve().parents[1]
def signature(c):
 if isinstance(c,CodeType):return (c.co_code,c.co_names,c.co_varnames,c.co_argcount,c.co_kwonlyargcount,c.co_flags,tuple(signature(x) for x in c.co_consts),c.co_exceptiontable)
 return c
def main():
 path=Path(sys.argv[1] if len(sys.argv)>1 else 'build/pyinstaller_release_verified/NilePhytoDock/PYZ-00.pyz');archive=ZlibArchiveReader(str(path));checked=[]
 for folder in ['app','database','scientific','visualization','reporting']:
  for p in (ROOT/folder).rglob('*.py'):
   module='.'.join(p.relative_to(ROOT).with_suffix('').parts)
   if module.endswith('.__init__'):module=module[:-9]
   if module not in archive.toc:continue
   assert signature(archive.extract(module))==signature(compile(p.read_bytes(),str(p),'exec')),module
   checked.append(module)
 assert 'visualization.functional_map' in checked and 'app.projects' in checked
 assert {'app.result_workspace','app.viewer_window','scientific.result_summary'}<=set(checked),'New result modules must be frozen'
 result={'own_modules_identical_to_final_source':checked,'module_count':len(checked),'pyinstaller_archive_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 output=Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'data/validation/final_frozen_source_match.json';output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2));print(len(checked),'current modules match frozen source')
if __name__=='__main__':main()
