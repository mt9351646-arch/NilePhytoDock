from pathlib import Path
from PIL import Image,ImageDraw
files=sorted(Path('data/validation/report_render_final').glob('page-*.png'),key=lambda p:int(p.stem.split('-')[-1]))
print('Verified DOCX pages:',len(files))
for f in files:assert Image.open(f).width>0
