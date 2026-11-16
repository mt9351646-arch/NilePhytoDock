from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def main():
    fonts=Path('C:/Windows/Fonts')
    pdfmetrics.registerFont(TTFont('Guide',str(fonts/'calibri.ttf')))
    pdfmetrics.registerFont(TTFont('GuideBold',str(fonts/'calibrib.ttf')))
    styles=getSampleStyleSheet()
    for s in styles.byName.values():s.fontName='Guide';s.textColor=colors.HexColor('#203b48')
    styles['Title'].fontName='GuideBold';styles['Title'].fontSize=26
    styles['Heading1'].fontName='GuideBold';styles['Heading1'].fontSize=15;styles['Heading1'].spaceBefore=18;styles['Heading1'].textColor=colors.black
    styles['Heading1'].keepWithNext=True
    styles['BodyText'].fontSize=10.5;styles['BodyText'].leading=15;styles['BodyText'].spaceAfter=9
    text=Path('docs/USER_GUIDE.md').read_text(encoding='utf-8');flow=[]
    for paragraph in text.split('\n\n'):
        if paragraph.startswith('!['):
            p=Path('data/validation/gui_smoke.png')
            from PIL import Image as PILImage
            width,height=PILImage.open(p).size
            flow.extend([Paragraph('The desktop application',styles['Heading1']),Image(str(p),width=480,height=480*height/width)]);continue
        style='Title' if paragraph.startswith('# ') else 'Heading1' if paragraph.startswith('## ') else 'BodyText'
        p=paragraph.removeprefix('## ').removeprefix('# ')
        flow.append(Paragraph(escape(p).replace('`',''),styles[style]))
    def footer(canvas,doc):
        canvas.setFont('Guide',8);canvas.setFillColor(colors.HexColor('#58717d'));canvas.drawString(54,30,'NilePhytoDock 0.2.0  |  Ahmed G soliman • malak Taha');canvas.drawRightString(540,30,str(doc.page))
    SimpleDocTemplate('docs/USER_GUIDE.pdf',title='NilePhytoDock user guide',author='Ahmed G soliman and malak Taha',leftMargin=54,rightMargin=54,topMargin=48,bottomMargin=48).build(flow,onFirstPage=footer,onLaterPages=footer)

if __name__=='__main__':main()
