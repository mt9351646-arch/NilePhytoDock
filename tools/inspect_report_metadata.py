import json
from pathlib import Path
from docx import Document
data=json.loads(Path('data/validation/redesign/validation.json').read_text(encoding='utf-8'))
p=Path(data['project']['folder'])/'Reports/scientific_report.docx'
d=Document(p);print('DOCX author:',repr(d.core_properties.author),'last modified by:',repr(d.core_properties.last_modified_by))
