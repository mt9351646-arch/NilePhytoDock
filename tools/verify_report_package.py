"""Check that the exported numerical formats describe the same real results."""
from pathlib import Path
import csv,json
import sys
from openpyxl import load_workbook
from docx import Document
from pypdf import PdfReader

folder=Path(sys.argv[1] if len(sys.argv)>1 else 'data/validation/relocated_reports')
provenance=json.loads((folder/'reproducibility.json').read_text(encoding='utf-8'))
book=load_workbook(folder/'screening_results.xlsx',read_only=True,data_only=True)
counts={}
for title,items in provenance['tables'].items():
    path=folder/(title.lower().replace(' ','_')+'.csv')
    with path.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
    assert len(rows)==len(items)==book[title].max_row-1,(title,len(rows),len(items))
    if title=='Docking results':
        assert all(float(row['score'])==item['score'] and row['status']=='complete' for row,item in zip(rows,items))
    counts[title]=len(items)
book.close()
doc=Document(folder/'scientific_report.docx');assert len(doc.tables)==len(provenance['tables'])
pdf=PdfReader(folder/'scientific_report.pdf');assert len(pdf.pages)>0
assert all(p.extract_text().strip() for p in pdf.pages)
images=list((folder/'figures').glob('*.png'));assert images and all(p.stat().st_size>1000 for p in images)
result={'tables_match_csv_xlsx_json':True,'rows':counts,'docx_tables':len(doc.tables),'pdf_pages':len(pdf.pages),'actual_chart_pngs':len(images)}
Path('data/validation/report_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(result)
