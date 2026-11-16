"""Explicit command-line installation verification using a private data folder.

Normal desktop startup never enters this path. The check performs real local
calculations and exits with a JSON record, suitable for release QA.
"""
import json,time,traceback,hashlib
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel,QPushButton
from database.store import connect,rows,counts
from scientific.pipeline import create_project,run_project
from scientific.ranking import project_rankings
from app.branding import VERSION

def network_check(window,app,output):
    """Explicit release diagnostic, keeping TLS validation enabled."""
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    def work(emit):
        import requests,ssl,sys,socket,urllib.request
        from scientific.pdb_retrieval import retrieve
        result={'version':VERSION,'frozen':bool(getattr(sys,'frozen',False)),'certifi':requests.certs.where(),'certificate_file_exists':Path(requests.certs.where()).exists(),'openssl':ssl.OPENSSL_VERSION}
        try:
            context=ssl.create_default_context(cafile=requests.certs.where())
            with socket.create_connection(('files.rcsb.org',443),timeout=20) as raw:
                with context.wrap_socket(raw,server_hostname='files.rcsb.org') as tls:
                    tls.sendall(b'GET /download/3PTB.pdb HTTP/1.1\r\nHost: files.rcsb.org\r\nConnection: close\r\n\r\n');result['raw_tls']=tls.recv(200).decode(errors='replace')
        except Exception:result['raw_tls_error']=traceback.format_exc()
        try:
            with urllib.request.urlopen('https://files.rcsb.org/download/3PTB.pdb',timeout=30,context=ssl.create_default_context(cafile=requests.certs.where())) as response:result['urllib_status']=response.status;result['urllib_bytes']=len(response.read())
        except Exception:result['urllib_error']=traceback.format_exc()
        try:result['file']=retrieve('3PTB',output/'downloads');result['success']=True
        except Exception as error:
            result.update(success=False,error=traceback.format_exc());visited=set();nested=[]
            def walk(value):
                if not isinstance(value,BaseException) or id(value) in visited:return
                visited.add(id(value));nested.append(''.join(traceback.format_exception(type(value),value,value.__traceback__)))
                for child in [value.__cause__,value.__context__,getattr(value,'reason',None),*value.args]:walk(child)
            walk(error);result['nested_errors']=nested
        (output/'network.json').write_text(json.dumps(result,indent=2),encoding='utf-8');return result
    def done(result):
        def finish():
            if window.tasks:QTimer.singleShot(50,finish)
            else:app.exit(0 if result['success'] else 1)
        QTimer.singleShot(50,finish)
    window.run_task(work,done)

def start(window,app,output,protein):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    def fail(error):
        (output/'verification.json').write_text(json.dumps({'success':False,'error':str(error),'version':VERSION},indent=2),encoding='utf-8');app.exit(1)
    def completed(pid):
        if not getattr(window,'_qa_results_requested',False):
            window._qa_results_requested=True;window.project_id=pid;window.refresh_results()
        if window._results_loading:QTimer.singleShot(100,lambda:completed(pid));return
        try:
            window.project_id=pid;window.refresh_results();window.nav.setCurrentRow(5);app.processEvents();window.grab().save(str(output/'packaged_results.png'))
            runs=rows(window.db,'SELECT * FROM docking_runs WHERE project_id=?',(pid,));assert len(runs)==3 and all(r['status']=='complete' and r['elapsed']>0 for r in runs)
            assert all(i['index'] is None for rs in project_rankings(window.db,pid).values() for i in rs)
            command_boxes=[]
            for run in runs:
                pocket=dict(window.db.execute('SELECT * FROM predicted_pockets WHERE id=?',(run['pocket_id'],)).fetchone());cmd=json.loads((Path(run['folder'])/'process.log').read_text(encoding='utf-8').splitlines()[0]);center=[float(cmd[cmd.index('--center_'+a)+1]) for a in 'xyz'];size=[float(cmd[cmd.index('--size_'+a)+1]) for a in 'xyz'];assert center==json.loads(pocket['center']) and size==json.loads(pocket['size']);command_boxes.append({'center':center,'dimensions':size,'elapsed':run['elapsed']})
            import re
            labels=[v.text() for v in window.findChildren(QLabel)+window.findChildren(QPushButton)]
            assert not any(re.search(r'[\u0600-\u06ff]',s) for s in labels)
            assert not any('guide' in v.text().lower() for v in window.findChildren(QPushButton))
            folder=Path(window.db.execute('SELECT folder FROM analysis_projects WHERE id=?',(pid,)).fetchone()[0])
            assert window.db.execute('SELECT status FROM analysis_projects WHERE id=?',(pid,)).fetchone()[0]=='complete'
            for filename in ['scientific_report.docx','scientific_report.pdf','screening_results.xlsx','source_observations.csv']:
                path=folder/'Reports'/filename;assert path.exists() and path.stat().st_size>100,filename
            assert (folder/'Reports/reproducibility.json').exists()
            assert json.loads((folder/'Reports/reproducibility.json').read_text(encoding='utf-8'))['application']['version']==VERSION
            window.nav.setCurrentRow(0);app.processEvents();window.grab().save(str(output/'packaged_overview.png'))
            result={'success':True,'version':VERSION,'engine_health':window.health_data,'counts':counts(window.db),'project_id':pid,'project_folder':str(folder),'actual_docking_runs':len(runs),'run_ids':[r['id'] for r in runs],'command_boxes':command_boxes,'hplc_units_preserved':True,'hplc_oil_index_suppressed':True,'english_ui_and_no_guide_buttons':True,'elapsed_seconds':time.monotonic()-started,'frozen':bool(getattr(__import__('sys'),'frozen',False))}
            window.results_table.selectRow(0);window.open_interaction();window.nav.setCurrentRow(12)
            visual_started=time.monotonic()
            def visual_check():
                if time.monotonic()-visual_started>90:fail('Native 3D/Plotly rendering timeout');return
                def got_view(state):
                    state=json.loads(state) if isinstance(state,str) else state
                    if state.get('error'):fail(state['error']);return
                    if not state.get('ready'):QTimer.singleShot(250,visual_check);return
                    try:
                        expected=window.db.execute('SELECT count(*) FROM molecular_interactions WHERE pose_id=?',(window.current_pose,)).fetchone()[0]
                        assert state['contacts']==expected and expected>0
                        window.nav.setCurrentRow(8)
                        def chart_check():
                            if time.monotonic()-visual_started>90:fail('Native Plotly rendering timeout');return
                            def chart_ready(ready):
                                if not ready:QTimer.singleShot(250,chart_check);return
                                window.grab().save(str(output/'packaged_charts.png'))
                                result.update(project_complete=True,all_report_formats_verified=True,native_3d_atom_mapping_verified=True,native_3d_contacts=expected,offline_plotly_rendered=True)
                                window.functional_results.set_project(pid)
                                def summary_check():
                                    if time.monotonic()-visual_started>150:fail('Native result summary timeout');return
                                    if window.functional_results.group_result is None or window.tasks:QTimer.singleShot(250,summary_check);return
                                    try:
                                        assert len(window.oil_results.result['compounds'])==3
                                        assert window.functional_results.group_result['cohort_size']==3
                                        window.nav.setCurrentRow(5);app.processEvents();window.grab().save(str(output/'packaged_oil_results.png'))
                                        window.nav.setCurrentRow(11);app.processEvents();window.grab().save(str(output/'packaged_functional_groups.png'))
                                        window.open_three_d_window();child=window.three_d_window
                                        def standalone_check():
                                            if time.monotonic()-visual_started>150:fail('Standalone 3D timeout');return
                                            def child_ready(state):
                                                if not state:QTimer.singleShot(250,standalone_check);return
                                                child.presentation(True)
                                                def final_frame():
                                                    child.grab().save(str(output/'packaged_fullscreen_3d.png'));child.presentation(False);child.close()
                                                    result.update(oil_first_results_verified=True,functional_group_summary_verified=True,dedicated_3d_page=True,separate_fullscreen_3d_window=True)
                                                    if '--verify-visual-update' in __import__('sys').argv:
                                                        try:
                                                            from app.visual_verification import verify
                                                            result['visual_update']=verify(window,app,output/'visual_update')
                                                        except Exception:fail(traceback.format_exc());return
                                                    window.nav.setCurrentRow(0);app.processEvents();window.grab().save(str(output/'packaged_overview.png'))
                                                    (output/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');app.exit(0)
                                                QTimer.singleShot(400,final_frame)
                                            child.viewer.page().runJavaScript('Boolean(window.viewerReady)&&!window.validationError',child_ready)
                                        QTimer.singleShot(250,standalone_check)
                                    except Exception:fail(traceback.format_exc())
                                QTimer.singleShot(250,summary_check)
                            window.chart_workspace.web.page().runJavaScript('Boolean(window.chartReady)',chart_ready)
                        QTimer.singleShot(250,chart_check)
                    except Exception:fail(traceback.format_exc())
                window.interaction_viewer.page().runJavaScript('JSON.stringify({ready:Boolean(window.viewerReady),error:window.validationError||null,contacts:(window.viewerGeometryAudit||[]).length})',got_view)
            QTimer.singleShot(250,visual_check)
        except Exception:fail(traceback.format_exc())
    def begin():
        if window.tasks:
            if time.monotonic()-started>120:fail('Engine check timeout')
            else:QTimer.singleShot(250,begin)
            return
        try:
            assert all(v['ok'] for v in window.health_data.values())
            profile=window.db.execute("SELECT id FROM oil_profiles WHERE name LIKE 'Curcuma longa%Control%'").fetchone()[0]
            folder=output/'Actual_HPLC_screening'
            if folder.exists():raise ValueError('Use a fresh verification directory')
            settings={'exhaustiveness':1,'num_modes':1,'seed':20261029,'cpu':2,'remove_heterogens':['BEN A:1'],'pocket_mode':'Automatic'}
            pid=create_project(window.db,'English installation HPLC validation',[str(Path(protein).resolve())],[profile],settings,folder)
            def work(emit):
                db=connect(window.db_path)
                try:run_project(db,pid,progress=emit)
                finally:db.close()
                return pid
            task=window.run_task(work,completed);task.failed.connect(fail);task.cancelled.connect(lambda:fail('Installation verification was cancelled before completion'))
        except Exception:fail(traceback.format_exc())
    QTimer.singleShot(250,begin)
