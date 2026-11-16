from pathlib import Path
from PIL import Image,ImageDraw
import sys
folder=Path(sys.argv[1] if len(sys.argv)>1 else 'data/validation/verified_report_render')
files=sorted(folder.glob('page-*.png'),key=lambda p:int(p.stem.split('-')[-1]))
out=Image.new('RGB',(1400,((len(files)+3)//4)*490),'#dce2e5')
for i,f in enumerate(files):
    im=Image.open(f).convert('RGB');im.thumbnail((330,450))
    x=(i%4)*350;y=(i//4)*490;out.paste(im,(x+10,y+10))
    ImageDraw.Draw(out).text((x+10,y+465),f.name,fill='black')
out.save(folder/'contact.png')
print(len(files),'pages')
