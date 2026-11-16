from PIL import Image,ImageDraw
from pathlib import Path
files=sorted(Path('data/validation/report_render').glob('page-*.png'),key=lambda p:int(p.stem.split('-')[-1]))
out=Image.new('RGB',(4*350,((len(files)+3)//4)*490),'#dce2e5')
for i,f in enumerate(files):
 im=Image.open(f).convert('RGB');im.thumbnail((330,450));x=(i%4)*350;y=(i//4)*490;out.paste(im,(x+10,y+10));ImageDraw.Draw(out).text((x+10,y+465),f.name,fill='black')
out.save('data/validation/report_render/contact.png')
