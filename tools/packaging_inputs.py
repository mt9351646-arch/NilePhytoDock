"""Native files used by Smina; original tool installation stays untouched."""
from pathlib import Path

def p2rank_jar_keep(name):
 name=Path(name).name
 if name in ['openchart-1.4.2.jar','vecmath-1.3.1.jar']:return False
 if '-natives.jar' in name and any(v in name for v in ['-linux-','-osx-','-win-i686-']):return False
 return True

def smina_files(folder):
 import pefile
 folder=Path(folder);lookup={p.name.lower():p for p in folder.iterdir() if p.is_file()}
 # Cairo drawing plugins are unused by the docking engine. Other OpenBabel
 # plugins remain available for molecular formats, charges and force fields.
 todo=['smina.exe']+[p.name for p in lookup.values() if p.suffix=='.obf' and p.name!='formats_cairo.obf'];seen=set()
 while todo:
  name=todo.pop().lower()
  if name in seen or name not in lookup:continue
  seen.add(name);pe=pefile.PE(str(lookup[name]),fast_load=True);pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT']])
  todo += [e.dll.decode().lower() for e in getattr(pe,'DIRECTORY_ENTRY_IMPORT',[])]+[e.dll.decode().lower() for e in getattr(pe,'DIRECTORY_ENTRY_DELAY_IMPORT',[])];pe.close()
 return [p for n,p in lookup.items() if n in seen or n=='provenance.json']
