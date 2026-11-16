"""Opt-in release QA; exercises the actual Qt controls and offline renderers."""
import hashlib,json,time
from pathlib import Path

def verify(window,app,output):
 from PySide6.QtWidgets import QPushButton,QFileDialog,QInputDialog,QTabWidget
 from PySide6.QtGui import QImage
 from visualization.release_charts import CHARTS,export_chart
 output=Path(output);output.mkdir(parents=True,exist_ok=True);checks={};errors=[]
 old_error,old_info=window.error,window.info;window.error=lambda text:errors.append(str(text));window.info=lambda text:None
 def wait(test,seconds=120):
  end=time.monotonic()+seconds
  while not test():
   app.processEvents();time.sleep(.01)
   if errors:raise AssertionError(errors[-1])
   if time.monotonic()>end:raise TimeoutError('Visual release check timed out')
  app.processEvents()
 def js(web,code):
  result=[];web.page().runJavaScript(code,lambda value:result.append(value));wait(lambda:bool(result),30);return result[0]
 def settle():
  end=time.monotonic()+.5
  while time.monotonic()<end:app.processEvents();time.sleep(.01)
 try:
  wait(lambda:not window.tasks)
  # Test the same dialog callback as the visible Retrieve PDB ID button.
  original=QInputDialog.getText
  try:
   QInputDialog.getText=lambda *a,**k:(' https://www.rcsb.org/structure/3ptb ',True)
   window.retrieve_pdb()
  finally:QInputDialog.getText=original
  wait(lambda:not window.tasks)
  assert any(Path(p).stem=='3PTB' for p in window.protein_files)
  checks['real_pdb_retrieval_from_pasted_url']=True
  pose=window.db.execute('SELECT p.id FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id WHERE r.project_id=? ORDER BY p.score LIMIT 1',(window.project_id,)).fetchone()[0]
  window.show_pose_id(pose,False);wait(lambda:not window.tasks);settle()
  path=output/'2D figure Ω.png';original=QFileDialog.getSaveFileName
  try:
   QFileDialog.getSaveFileName=lambda *a,**k:(str(path),'PNG image (*.png)')
   matches=[b for b in window.findChildren(QPushButton) if b.text()=='Save 2D figure'];assert len(matches)==1;assert matches[0].isVisible();matches[0].click()
  finally:QFileDialog.getSaveFileName=original
  assert path.exists() and path.with_suffix('.svg').exists();svg,layout=window.current_diagram();assert layout['anchors'];window.grab().save(str(output/'2d-workspace.png'))
  checks.update(direct_2d_save_button=True,vector_2d_and_300dpi_png=True,atom_anchored_2d_contacts=len(layout['anchors']))
  window.nav.setCurrentRow(12);viewer=window.interaction_viewer
  wait(lambda:js(viewer,'Boolean(window.viewerReady)&&!window.validationError'))
  assert js(viewer,"document.getElementById('representation').value")=='Cartoon'
  assert not js(viewer,"document.getElementById('siteOnly').checked")
  settle();window.grab().save(str(output/'3d-overview-workspace.png'));checks['complete_protein_cartoon_and_ligand_default']=True
  js(viewer,'ligandFocus();true');settle()
  assert js(viewer,"document.getElementById('labelMode').value")=='Residue and chain'
  endpoints=json.loads(js(viewer,'JSON.stringify(window.viewerEndpointAudit)'))
  assert endpoints and all(e['proteinAtomsVisible'] and e['ligandAtomsVisible'] and e['proteinCovalentContextVisible'] for e in endpoints),endpoints
  (output/'contact-endpoints.json').write_text(json.dumps(endpoints,indent=2));checks['visible_covalently_connected_contact_endpoints']=len(endpoints)
  js(viewer,"document.getElementById('highlight').click();true");settle()
  assert js(viewer,'window.viewerEndpointAudit.every(e=>e.proteinAtomsVisible&&e.ligandAtomsVisible&&e.proteinCovalentContextVisible)')
  js(viewer,"document.getElementById('highlight').click();true")
  views=[];hashes=[]
  for name in ['Front','Right','Top']:
   js(viewer,'setCameraView('+json.dumps(name)+'); true');settle();view=json.loads(js(viewer,'JSON.stringify(viewer.getView())'));views.append(view)
   path=output/('3d-'+name.lower()+'.png');saved=[];viewer.export_png(path,300,2400,1800,lambda ok:saved.append(ok));wait(lambda:bool(saved));assert saved[0]
   image=QImage(str(path));assert image.width()==2400 and image.height()==1800
   audit=json.loads(js(viewer,'JSON.stringify(window.lastExportAudit)'));assert audit['labelPixels']>=30
   after=json.loads(js(viewer,'JSON.stringify(viewer.getView())'));assert all(abs(a-b)<1e-5 for a,b in zip(after,view))
   hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
  assert len({tuple(v[4:8]) for v in views})==3 and len(set(hashes))==3
  js(viewer,"setCameraView('Right');true");settle();window.grab().save(str(output/'3d-workspace.png'))
  checks.update(three_distinct_camera_views_and_exports=True,current_camera_preserved_after_export=True,high_resolution_labels_scaled=True,viewer_geometry_contacts=js(viewer,'window.viewerGeometryAudit.length'))
  js(viewer,'surfaceView();true');wait(lambda:js(viewer,'window.pendingSurfaces===0'),90);settle();surface=output/'3d-pocket-surface.png';saved=[];viewer.export_png(surface,300,2400,1800,lambda ok:saved.append(ok));wait(lambda:bool(saved));assert saved[0],js(viewer,'JSON.stringify({error:window.validationError,pending:window.pendingSurfaces,audit:window.lastExportAudit,job:!!exportJob})')
  audit=json.loads(js(viewer,'JSON.stringify(window.lastExportAudit)'));assert audit['surfaceCount']>0;checks['computed_pocket_surface_in_export']=True
  wait(lambda:js(viewer,'window.pendingSurfaces===0'),90);settle();window.grab().save(str(output/'3d-surface-workspace.png'))
  window.nav.setCurrentRow(8);c=window.chart_workspace;chart_checks=[]
  for kind in CHARTS:
   start=time.monotonic();c.kind.setCurrentText(kind)
   wait(lambda:c.spec is not None and c.spec['kind']==kind and js(c.web,'Boolean(window.chartReady)&&window.chartSpec.kind=='+json.dumps(kind)))
   assert c.spec['available'];export_chart(c.spec,output/kind,120)
   assert all((output/kind).with_suffix(e).stat().st_size>100 for e in ('.png','.svg','.pdf','.csv','.xlsx','.json'))
   chart_checks.append({'kind':kind,'query_seconds':c.spec['query_seconds'],'including_exports_seconds':time.monotonic()-start})
  settle();window.grab().save(str(output/'network-workspace.png'));checks['four_lazy_charts_and_six_exports']=chart_checks
  window.nav.setCurrentRow(11);m=window.molecular_workspace;m.set_project(window.project_id)
  for tabs in window.findChildren(QTabWidget):
   if tabs.indexOf(m)>=0:tabs.setCurrentWidget(m)
  m.run();wait(lambda:m.result is not None and not window.tasks,180);assert m.shared.currentData()
  m.view.setCurrentIndex(0);settle();window.grab().save(str(output/'shared-groups-workspace.png'))
  from visualization.shared_groups import diagram
  from visualization.interaction_diagram import save_diagram
  svg,meta=diagram(m.result['compound_details'],m.shared.currentData());save_diagram(svg,output/'shared-group',150)
  checks['actual_shared_functional_group']={'name':meta['name'],'unique_structures':meta['count'],'total':meta['total']}
  assert not errors
  (output/'visual-verification.json').write_text(json.dumps(checks,indent=2),encoding='utf-8');return checks
 finally:window.error,window.info=old_error,old_info
