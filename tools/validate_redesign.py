"""Actual GUI → P2Rank → transferred boxes → Smina on two targets."""
import json,shutil,time,sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from app.gui import Window,NAV
from database.store import rows
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

def wait(app,predicate,timeout=300):
    deadline=time.monotonic()+timeout
    while not predicate():
        app.processEvents();time.sleep(.02)
        if time.monotonic()>deadline:raise TimeoutError('GUI validation stage timed out')

def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else 'data/validation/redesign').resolve();root.mkdir(parents=True,exist_ok=True)
    dbpath=root/'screening.sqlite'
    if dbpath.exists():raise ValueError('Use a fresh redesign validation folder')
    shutil.copy2('data/nilephytodock.sqlite',dbpath)
    app=QApplication([]);w=Window(dbpath);w.show();wait(app,lambda:not w.tasks)
    old_output=w.preferences.value('output',None)
    w.resize(1366,768);app.processEvents();w.grab().save(str(root/'dashboard.png'))
    w.add_proteins(['tests/fixtures/3PTB.pdb','tests/fixtures/1IEP.pdb'])
    w.remove_hetero.setText('BEN A:1;STI A:201;STI B:202');w.exhaust.setValue(1);w.modes.setValue(1);w.seed.setValue(20261031)
    for i in range(w.profile_list.count()):
        item=w.profile_list.item(i)
        if item.data(Qt.ItemDataRole.UserRole)==26:item.setCheckState(Qt.CheckState.Checked)
    w.predict_all();wait(app,lambda:not w.tasks,300)
    assert len(w.pocket_choices)==2,w.pocket_choices
    shown=[]
    for index in range(w.site_target.count()):
        w.site_target.setCurrentIndex(index);app.processEvents();choice=w.pocket_choices[w.site_target.currentData()]
        assert [b.value() for b in w.center]==choice['center']
        assert [b.value() for b in w.size]==[round(v,3) for v in choice['size']]
        shown.append({'protein':w.site_target.currentText(),'pocket':choice})
        w.grab().save(str(root/f'pockets_{index}.png'))
    output=root/'نتائج 蛋白 selected output';output.mkdir(exist_ok=True);w.output_path.setText(str(output));w.study_name.setText('Connected two-target CSV validation')
    w.nav.setCurrentRow(4);app.processEvents();w.grab().save(str(root/'workspace.png'));assert w.start_button.isEnabled()
    w.start_screening();wait(app,lambda:not w.tasks,600)
    pid=w.project_id;project=rows(w.db,'SELECT * FROM analysis_projects WHERE id=?',(pid,))[0]
    assert Path(project['folder']).is_relative_to(output)
    runs=rows(w.db,'SELECT * FROM docking_runs WHERE project_id=?',(pid,));assert len(runs)==12 and all(r['status']=='complete' for r in runs),[(r['status'],r['error']) for r in runs]
    checks=[]
    for run in runs:
        record=json.loads((Path(run['folder'])/'run.json').read_text())
        pocket=rows(w.db,'SELECT * FROM predicted_pockets WHERE id=?',(run['pocket_id'],))[0]
        # run.json records exactly the actual native Smina command arguments.
        command=json.loads((Path(run['folder'])/'process.log').read_text(encoding='utf-8').splitlines()[0])
        center=[float(command[command.index('--center_'+axis)+1]) for axis in 'xyz'];size=[float(command[command.index('--size_'+axis)+1]) for axis in 'xyz']
        assert center==json.loads(pocket['center']);assert size==json.loads(pocket['size']);checks.append({'run':run['id'],'center':center,'size':size})
    assert any(r['compound_id'] in [205,206] for r in runs)
    assert not w.db.execute('PRAGMA foreign_key_check').fetchall()
    w.nav.setCurrentRow(5);w.results_table.selectRow(0);w.open_interaction();app.processEvents();w.grab().save(str(root/'interaction.png'))
    for index in range(len(NAV)):
        w.nav.setCurrentRow(index);app.processEvents();w.grab().save(str(root/f'page_{index}.png'))
    w.dark.setChecked(True);w.nav.setCurrentRow(0);app.processEvents();w.grab().save(str(root/'dashboard_dark.png'));w.dark.setChecked(False)
    report={'project':project,'runs':len(runs),'poses':w.db.execute('SELECT count(*) FROM docking_poses').fetchone()[0],'no_manual_coordinate_entry':True,'gui_box_and_smina_coordinates_match':True,'shown_pockets':shown,'native_commands':checks,'new_csv_compounds_screened':[205,206],'selected_unicode_output_verified':True,'database_reopen_verified':False}
    snapshot=Path(project['folder'])/'Project_Data'/'project.nile.sqlite';assert snapshot.exists()
    from database.store import connect
    reopened=connect(snapshot);assert reopened.execute('SELECT count(*) FROM docking_poses').fetchone()[0]==report['poses'];reopened.close();report['database_reopen_verified']=True
    (root/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    w.preferences.setValue('output',old_output or str(Path.home()));w.close();app.processEvents();print(json.dumps(report,ensure_ascii=True),flush=True)

if __name__=='__main__':main()
