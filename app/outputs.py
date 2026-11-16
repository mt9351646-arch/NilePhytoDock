import re,shutil,tempfile,time,uuid
from pathlib import Path

FOLDERS=['Proteins','Prepared_Proteins','P2Rank','Docking','Docked_Ligands','Complexes','Interactions','2D_Figures','3D_Figures','Heatmaps','Rankings','Reports','Logs','Project_Data']

def validate_destination(path):
    path=Path(path).expanduser().resolve()
    if not path.is_dir():raise ValueError('Select an existing output directory or create one first')
    with tempfile.NamedTemporaryFile(prefix='.nile_write_check_',dir=path):pass
    return path,shutil.disk_usage(path).free

def project_folder(parent,title):
    parent,_=validate_destination(parent)
    name=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',title).strip(' .')[:70] or 'Screening'
    folder=parent/(name+'_'+time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6]);folder.mkdir()
    for part in FOLDERS:(folder/part).mkdir()
    return folder
