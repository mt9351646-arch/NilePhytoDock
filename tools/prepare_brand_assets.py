from pathlib import Path
from PIL import Image
root=Path('app/resources/brand');root.mkdir(parents=True,exist_ok=True)
source=root/'NilePhytoDock-logo.png'
image=Image.open(source).convert('RGBA');image.thumbnail((256,256),Image.Resampling.LANCZOS)
canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(image,((256-image.width)//2,(256-image.height)//2))
canvas.save(root/'NilePhytoDock.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print(source,Image.open(source).size,'preserved; multiresolution ICO created')
