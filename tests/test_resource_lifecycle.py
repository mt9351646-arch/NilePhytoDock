"""Workstation responsiveness and owned-process cleanup regressions."""
import json,os,subprocess,sys,threading,time
from pathlib import Path
import psutil,pytest
from scientific.runtime import Runner,Cancelled,task_context
from app.resource_policy import cpu_budget,configure_environment,java_heap_mb

def test_resource_budget_and_scientific_threads(monkeypatch):
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):monkeypatch.setenv(name,'32')
    configure_environment()
    assert 1<=cpu_budget()<=2 and 256<=java_heap_mb()<=1024
    assert all(os.environ[n]=='1' for n in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'))

def test_nested_runner_inherits_task_cancellation():
    owner=Runner()
    with task_context(owner):
        nested=Runner();assert nested.cancelled is owner.cancelled
        owner.cancelled.set()
        with pytest.raises(Cancelled):nested.checkpoint()

def test_cancel_terminates_only_owned_process_tree(tmp_path):
    marker=tmp_path/'child.json';runner=Runner();errors=[]
    code="import subprocess,sys,time,json;from pathlib import Path;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);Path(sys.argv[1]).write_text(json.dumps([__import__(\"os\").getpid(),p.pid]));time.sleep(60)"
    def work():
        try:runner.run([sys.executable,'-c',code,marker],tmp_path/'owned.log')
        except Exception as e:errors.append(e)
    thread=threading.Thread(target=work);thread.start();deadline=time.monotonic()+15
    while not marker.exists() and time.monotonic()<deadline:time.sleep(.02)
    assert marker.exists();pids=json.loads(marker.read_text());process=psutil.Process(pids[0])
    if os.name=='nt':
        assert len(process.cpu_affinity())<=cpu_budget()
        assert process.nice()==psutil.BELOW_NORMAL_PRIORITY_CLASS
    start=time.monotonic();runner.cancelled.set();thread.join(5)
    assert not thread.is_alive() and time.monotonic()-start<3
    assert len(errors)==1 and isinstance(errors[0],Cancelled)
    _,alive=psutil.wait_procs([p for pid in pids if psutil.pid_exists(pid) for p in [psutil.Process(pid)]],timeout=3)
    assert not alive

def test_serial_tasks_and_single_close_finish(qtbot,tmp_path,monkeypatch):
    import sqlite3
    from app.gui import Window
    source=sqlite3.connect('data/nilephytodock.sqlite');target=sqlite3.connect(tmp_path/'ui.sqlite');source.backup(target);target.close();source.close()
    from PySide6.QtWidgets import QApplication
    quit_requests=[];monkeypatch.setattr(QApplication.instance(),'quit',lambda:quit_requests.append(True))
    window=Window(tmp_path/'ui.sqlite');qtbot.addWidget(window);window.show();window.error=lambda s:pytest.fail(str(s))
    qtbot.waitUntil(lambda:not window.tasks,timeout=60000)
    running=threading.Event();completed=[]
    def active(emit):
        running.set()
        from scientific.runtime import checkpoint
        while True:checkpoint();time.sleep(.02)
    window.run_task(active,lambda _:completed.append('active'))
    window.run_task(lambda emit:completed.append('queued'))
    qtbot.waitUntil(running.is_set,timeout=5000)
    assert sum(t.isRunning() for t in window.tasks)==1
    start=time.monotonic();window.close()
    qtbot.waitUntil(lambda:not window.tasks,timeout=5000)
    qtbot.waitUntil(lambda:not window.isVisible(),timeout=1000)
    qtbot.waitUntil(lambda:bool(quit_requests),timeout=1000)
    assert time.monotonic()-start<3 and not completed

def test_table_retains_record_once_and_selection(qtbot):
    from app.gui import Table
    from PySide6.QtCore import Qt
    table=Table();qtbot.addWidget(table);record={'name':'Ligand','score':-5.2,'metadata':'x'*10000};table.populate([record],['name','score']);table.selectRow(0)
    assert table.selected()==record and table.item(0,1).data(Qt.ItemDataRole.UserRole) is None
