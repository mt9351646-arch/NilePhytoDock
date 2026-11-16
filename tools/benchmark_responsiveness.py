"""Bounded, isolated GUI workload; never opens the researcher's working DB."""
import argparse,json,os,sqlite3,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('output');args=parser.parse_args()
    out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
    os.environ['NILEPHYTODOCK_DATA']=str(out/'userdata')
    from app.resource_policy import configure_environment
    configure_environment()
    import psutil
    from PySide6.QtCore import Qt,QTimer
    from PySide6.QtWidgets import QApplication
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app=QApplication([]);app.setQuitOnLastWindowClosed(False)
    source=sqlite3.connect(ROOT/'data/validation/v1_0_1_visual/study.sqlite')
    db=sqlite3.connect(out/'study.sqlite');source.backup(db);db.close();source.close()
    from app.gui import Window
    from app.branding import VERSION
    start=time.monotonic();w=Window(out/'study.sqlite');w.show();w.error=lambda s:print(str(s),flush=True);w.info=lambda *_:None
    w.project_id=w.db.execute('SELECT max(id) FROM analysis_projects').fetchone()[0]
    samples=[];ticks=[];last=time.monotonic();phase='startup';phase_start=start
    def pulse():
        nonlocal last
        now=time.monotonic();ticks.append({'phase':phase,'gap_ms':(now-last)*1000});last=now
    heartbeat=QTimer();heartbeat.timeout.connect(pulse);heartbeat.start(50)
    def sample():
        procs=[psutil.Process()]+psutil.Process().children(recursive=True);rss=cpu=0;names=[]
        for p in procs:
            try:rss+=p.memory_info().rss;cpu+=sum(p.cpu_times()[:2]);names.append(p.name())
            except psutil.Error:pass
        samples.append({'at':time.monotonic()-start,'phase':phase,'rss':rss,'cpu_seconds':cpu,'processes':names})
    monitor=QTimer();monitor.timeout.connect(sample);monitor.start(500)
    def set_phase(name):
        nonlocal phase,phase_start
        phase=name;phase_start=time.monotonic()
    def ready():
        if w.tasks:QTimer.singleShot(100,ready);return
        set_phase('idle');QTimer.singleShot(6000,screening)
    def screening():
        set_phase('live_results');w.busy=True;w.nav.setCurrentRow(4);QTimer.singleShot(10000,viewer)
    def viewer():
        w.busy=False;set_phase('viewer');pose=w.db.execute('SELECT min(id) FROM docking_poses').fetchone()[0]
        w.show_pose_id(pose,True);QTimer.singleShot(6000,hidden)
    def hidden():
        set_phase('hidden_viewer');w.nav.setCurrentRow(0);QTimer.singleShot(6000,finish)
    def finish():
        if w.tasks:QTimer.singleShot(100,finish);return
        summaries={}
        for name in {s['phase'] for s in samples}:
            ss=[s for s in samples if s['phase']==name];gaps=sorted(t['gap_ms'] for t in ticks if t['phase']==name)
            summaries[name]={'peak_tree_rss_mb':max(s['rss'] for s in ss)/1e6,'cpu_core_equivalents':(ss[-1]['cpu_seconds']-ss[0]['cpu_seconds'])/max(.001,ss[-1]['at']-ss[0]['at']),'heartbeat_p95_ms':gaps[min(len(gaps)-1,int(len(gaps)*.95))] if gaps else None,'heartbeat_max_ms':max(gaps,default=0),'process_count':max(len(s['processes']) for s in ss)}
        (out/'benchmark.json').write_text(json.dumps({'version':VERSION,'summaries':summaries,'samples':samples,'ticks':ticks},indent=2),encoding='utf-8')
        print(json.dumps(summaries,indent=2),flush=True);w.close();app.exit(0)
    QTimer.singleShot(100,ready);QTimer.singleShot(90000,lambda:app.exit(2));sys.exit(app.exec())

if __name__=='__main__':main()
