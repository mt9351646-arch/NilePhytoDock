from pathlib import Path
from PIL import Image,ImageDraw
root=Path('data/validation/layout_matrix')
for directory in root.iterdir():
    if not directory.is_dir():continue
    for size in ['1366x768','1920x1080','2560x1440']:
        files=sorted(directory.glob(size+'_*.png'),key=lambda p:int(p.stem.split('_')[-1]))
        if not files:continue
        out=Image.new('RGB',(4*400,3*260),'#dce2e5')
        for i,path in enumerate(files):
            image=Image.open(path).convert('RGB');image.thumbnail((390,230));x=i%4*400;y=i//4*260;out.paste(image,(x+5,y+5));ImageDraw.Draw(out).text((x+5,y+240),path.name,fill='black')
        out.save(directory/(size+'_contact.jpg'),quality=90)
print('Contact sheets written')
