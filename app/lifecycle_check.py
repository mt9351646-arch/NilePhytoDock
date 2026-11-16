"""Explicit QA flag: close once during an owned native process and exit."""
import json,sys,time
from pathlib import Path
import psutil
from PySide6.QtCore import QTimer
from app.branding import VERSION

def start(window,app,output,protein):
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=True)
    record={'version':VERSION,'frozen':bool(getattr(sys,'frozen',False))};began=time.monotonic();owned=[];closed_at=[]
    def finish():
        alive=[p.pid for p in owned if p.is_running()]
        record.update(success=bool(closed_at) and not alive and not window.tasks and not (out/'queued-work-ran.txt').exists(),owned_engines=[p.pid for p in owned],remaining_engines=alive,remaining_tasks=len(window.tasks),queued_work_ran=(out/'queued-work-ran.txt').exists(),close_seconds=time.monotonic()-closed_at[0] if closed_at else None)
        (out/'verification.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    app.aboutToQuit.connect(finish)
    def watch():
        if time.monotonic()-began>45:
            record['error']='Native lifecycle verification timed out';window.close();return
        engines=[p for p in psutil.Process().children(recursive=True) if p.name().lower()=='java.exe']
        if not engines:QTimer.singleShot(30,watch);return
        owned.extend(engines);record['native_priority']=[int(p.nice()) for p in owned];record['native_affinity']=[p.cpu_affinity() for p in owned]
        window.run_task(lambda emit:(out/'queued-work-ran.txt').write_text('Unexpected queued execution',encoding='utf-8'))
        closed_at.append(time.monotonic());window.close();record['hidden_after_one_close']=not window.isVisible()
    def begin():
        if window.tasks:QTimer.singleShot(50,begin);return
        def work(emit):
            from scientific.pockets import predict
            from scientific.runtime import Runner
            predict(protein,out/'pockets',Runner())
        window.run_task(work);QTimer.singleShot(30,watch)
    QTimer.singleShot(50,begin)
