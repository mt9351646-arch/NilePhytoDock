from database.store import connect
from visualization.figures import export_pose
from PIL import Image
import json
from pathlib import Path
db=connect('data/validation/redesign/screening.sqlite')
row=db.execute('SELECT p.id FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id WHERE r.compound_id=205 ORDER BY r.protein_id DESC LIMIT 1').fetchone()
path=export_pose(db,row[0],'data/validation/redesign/diagram_examples/thymol_600',600)
im=Image.open(path);assert im.info['dpi'][0]>599 and im.width>5000
report={'dpi':im.info['dpi'],'pixels':im.size,'svg_is_vector':'<image' not in path.with_suffix('.svg').read_text(encoding='utf-8')}
Path('data/validation/redesign/diagram_600dpi.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)
