from pathlib import Path
import json,hashlib,platform
from database.store import connect,rows
from scientific.runtime import health
root=Path('release/NilePhytoDock Portable').resolve()
report={'date':'2026-10-29','windows':'Windows 11 Pro 10.0.26200 x64','entry_point':str(root/'NilePhytoDock.exe'),'exe_sha256':hashlib.sha256((root/'NilePhytoDock.exe').read_bytes()).hexdigest(),'distribution_bytes':sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),'launched_from_windows_explorer':True,'relocated_folder_with_spaces':True,'relocated_gui_opened':True,'library_profiles':25,'ready_compound_records':41,'unique_ready_inchikeys':40,'initial_packaged_defects_corrected':['Excluded incompatible Poppler ICU DLL selected from developer PATH','Included MDAnalysis Cython helper module','Included matplotlib SVG backend'],'preliminary_native_workflow_and_reports_verified':True,'relocated_screening_status':'running','clean_vm_tested':False,'windows_10_tested':False}
Path('data/validation/executable_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('Executable provenance recorded')
