from PIL import Image,ImageOps,ImageDraw
from pathlib import Path
files=sorted(Path('data/validation/pdf_render').glob('guide-*.png'))
thumbs=[]
for f in files:
 im=Image.open(f).convert('RGB');im.thumbnail((420,580));canvas=Image.new('RGB',(440,620),'#d6dee2');canvas.paste(im,((440-im.width)//2,20));ImageDraw.Draw(canvas).text((10,600),f.name,fill='black');thumbs.append(canvas)
out=Image.new('RGB',(440*3,620*((len(thumbs)+2)//3)),'white')
for i,im in enumerate(thumbs):out.paste(im,((i%3)*440,(i//3)*620))
out.save('data/validation/pdf_render/guide_contact_sheet.png')
