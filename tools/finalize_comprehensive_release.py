"""Collect release evidence without altering research observations."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=ROOT/'validation/0.6.0';out.mkdir(parents=True,exist_ok=True)
 evidence=['comprehensive_pytest.xml','final_svg_pytest.log','comprehensive_import.json','source_quality_review.json','standard_scope_review.json','formula_verification.json','final_frozen_source_match.json','comprehensive_shortcuts.json','release_verification.json','document_qa.json','resume_inventory.json','environment.json','source_inventory.json','database_validation.json','path_verification.json']
 evidence += [f'{folder}/verification.json' for folder in ['comprehensive_geometry','comprehensive_appearance','comprehensive_charts','comprehensive_exports','final_workspace','release_install']]
 evidence += ['comprehensive_layout/1.0/layout.json','comprehensive_layout/1.5/layout.json','case_study_final/validation.json']
 for rel in evidence:
  src=ROOT/'data/validation'/rel
  if src.exists():
   dest=out/rel
   if dest.suffix=='.log':dest=dest.with_suffix('.txt')
   dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
 for rel in ['final_workspace/molecular_workspace.png','final_workspace/Functional_group_participation.png','comprehensive_appearance/Scientific_Classic.png']:
  src=ROOT/'data/validation'/rel
  if src.exists():
   dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
 inventory=[]
 for p in (ROOT/'data/literature').glob('*'):
  if p.is_file() and p.name!='SOURCE_INVENTORY.json':inventory.append({'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'source':'https://pmc.ncbi.nlm.nih.gov/articles/'+p.name.split('_')[0].split('.')[0]+'/' if p.name.startswith('PMC') else 'Reviewed local transcription/manifest'})
 (ROOT/'data/literature/SOURCE_INVENTORY.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
 (out/'README.md').write_text('''# Verification evidence for 0.6.0

Records from native Windows executions, not a fresh execution on the reader's machine. Original paths describe the development host. See docs/VALIDATION_REPORT.md for interpretation. The case-data release asset contains commands, poses, complexes, tables, analyses and a reopenable project. Full screenshots and raw outputs remain in the preserved workspace.

resume_inventory.json records the existing source inventory before this continuation. No Git history existed. The initial repository commit preserves the verified snapshot; no earlier commit history is reconstructed.
''',encoding='utf-8')
 files=[{'file':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='EVIDENCE_SHA256.json']
 (out/'EVIDENCE_SHA256.json').write_text(json.dumps(files,indent=2),encoding='utf-8');print('Curated',len(files),'verification files')
if __name__=='__main__':main()
