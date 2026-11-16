from app.gui import Window,NAV
from database.store import connect
from pathlib import Path

def test_navigation_selection_and_multi_import(qtbot,tmp_path):
    # Use a private database copy, so GUI tests never mutate the delivered library.
    import sqlite3
    target=tmp_path/'gui.sqlite'
    source=sqlite3.connect('data/nilephytodock.sqlite');copy=sqlite3.connect(target);source.backup(copy);copy.close();source.close()
    w=Window(target);qtbot.addWidget(w);w.show()
    initial_dark=w.dark.isChecked()
    for i in range(len(NAV)):
        w.nav.setCurrentRow(i);assert w.stack.currentIndex()==i
    w.set_all_profiles(True);assert len(w.selected_profiles())==w.db.execute('SELECT count(*) FROM oil_profiles').fetchone()[0]
    from PySide6.QtWidgets import QLabel,QPushButton
    import re
    assert not any(re.search(r'[\u0600-\u06ff]',v.text()) for v in w.findChildren(QLabel)+w.findChildren(QPushButton))
    assert not any('guide' in v.text().lower() for v in w.findChildren(QPushButton))
    w.add_proteins(['tests/fixtures/3PTB.pdb','tests/fixtures/1W6Q.pdb']);assert len(w.protein_files)==2
    w.dark.setChecked(True);w.dark.setChecked(False)
    qtbot.waitUntil(lambda:not w.tasks,timeout=60000)
    assert all(v['ok'] for v in w.health_data.values())
    assert not w.start_button.isEnabled()  # Automatic mode requires predictions.
    w.pocket_mode.setCurrentText('Custom box');assert w.start_button.isEnabled()
    assert all(not field.isReadOnly() for field in w.center)
    w.pocket_mode.setCurrentText('Automatic');assert not w.start_button.isEnabled()
    assert all(field.isReadOnly() for field in w.center)
    w.dark.setChecked(initial_dark)
    w.close()
