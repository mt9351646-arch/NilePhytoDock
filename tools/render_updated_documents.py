import json,subprocess
from pathlib import Path
root=Path('data/validation/redesign');report=json.loads((root/'validation.json').read_text(encoding='utf-8'))
python=Path('C:/Users/PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
renderer=Path('C:/Users/PC/.codex/plugins/cache/openai-primary-runtime/documents/26.1025.11240/skills/documents/render_docx.py')
source=Path(report['project']['folder'])/'Reports'/'scientific_report.docx'
subprocess.run([str(python),str(renderer),str(source),'--output_dir',str((root/'report_render').resolve()),'--emit_pdf'],check=True)
