import json,time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from app.gui import Window,NAV
from database.store import rows

root=Path('data/validation/studio');root.mkdir(parents=True,exist_ok=True)
app=QApplication([]);w=Window('data/validation/studio_workflow/screening.sqlite');w.show();w.dark.setChecked(True);w.resize(1366,850)
deadline=time.monotonic()+90
while w.tasks and time.monotonic()<deadline:app.processEvents();time.sleep(.03)
assert not w.tasks
w.project_id=1;w.refresh_results()
def capture(name):app.processEvents();w.grab().save(str(root/name))
w.nav.setCurrentRow(0);capture('overview.png')
w.add_proteins(['tests/fixtures/3PTB.pdb','tests/fixtures/1IEP.pdb']);w.protein_table.selectRow(0);w.show_protein();w.nav.setCurrentRow(2)
for i in range(w.profile_list.count()):
    item=w.profile_list.item(i)
    if item.data(Qt.ItemDataRole.UserRole)==26:item.setCheckState(Qt.CheckState.Checked)
deadline=time.monotonic()+2
while time.monotonic()<deadline:app.processEvents();time.sleep(.02)
capture('targets.png')
w.remove_hetero.setText('BEN A:1;STI A:201;STI B:202')
for item in rows(w.db,'SELECT t.*,p.rank,p.score,p.probability,p.center,p.size,p.residues,p.method,p.provenance FROM protein_targets t JOIN predicted_pockets p ON p.protein_id=t.id WHERE t.project_id=1 AND p.rank=1'):
    choice={k:item[k] for k in ['rank','score','probability','residues','method','provenance']};choice.update(center=json.loads(item['center']),size=json.loads(item['size']))
    source=next(p for p in w.protein_files if Path(p).stem==item['name']);w.previews[item['sha256']]={'source':source,'prepared':item['prepared_path'],'pockets':[choice]};w.pocket_choices[item['sha256']]=choice
w.site_target.clear()
for key,item in w.previews.items():w.site_target.addItem(Path(item['source']).name,key)
w.show_target_pockets();w.nav.setCurrentRow(3)
deadline=time.monotonic()+2
while time.monotonic()<deadline:app.processEvents();time.sleep(.02)
capture('binding_sites.png');w.nav.setCurrentRow(4);w.protocol_tabs.setCurrentIndex(0);capture('setup_site.png');w.protocol_tabs.setCurrentIndex(1);app.processEvents();w.stack.currentWidget().verticalScrollBar().setValue(w.stack.currentWidget().verticalScrollBar().maximum());capture('setup_protocol.png');w.protocol_tabs.setCurrentIndex(2);capture('setup_receptor.png')
w.results_table.selectRow(0);w.open_interaction()
deadline=time.monotonic()+4
while time.monotonic()<deadline:app.processEvents();time.sleep(.02)
capture('interactions.png');w.nav.setCurrentRow(5);capture('results.png');w.nav.setCurrentRow(7);capture('priorities.png');w.nav.setCurrentRow(9);capture('reports.png')
for index in range(len(NAV)):w.nav.setCurrentRow(index);capture(f'page_{index}.png')
w.dark.setChecked(False);w.nav.setCurrentRow(0);capture('overview_light.png');w.dark.setChecked(True);w.close();app.processEvents();print('Studio screenshots captured from actual saved results')
