from pathlib import Path
p=Path('data/validation/report_render_final/contact.png')
from PIL import Image,ImageDraw
files=sorted(Path('data/validation/pdf_render').glob('report-*.png'))
print('PDF report render pages',len(files))
print('Native report exports',[(p.name,p.stat().st_size) for p in Path('data/validation/packaged_reports').glob('*') if p.is_file()])
