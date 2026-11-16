"""Offline 3Dmol workspace with verified atom/feature anchors."""
import json,uuid,base64,time
from pathlib import Path
from PySide6.QtCore import QUrl,Qt,QTimer
from PySide6.QtGui import QImage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from app.paths import resource,user_data
from visualization.semantics import INTERACTIONS,residue_color,MODES,stable_color,CHARGE_NOTE

class MolecularViewer(QWebEngineView):
    def __init__(self,parent=None):
        super().__init__(parent);self.setMinimumSize(360,320);self.viewer_id=uuid.uuid4().hex;self.last_data=None
        self._pending_url=None;self._loaded=False
        # An unused hidden viewer must not start a Chromium renderer.
    def showEvent(self,event):
        super().showEvent(event)
        if self._pending_url:
            self.load(self._pending_url);self._pending_url=None;self._loaded=True
        elif self._loaded:self.page().setLifecycleState(QWebEnginePage.LifecycleState.Active)
        else:self.setHtml('<html lang="en"><body style="font:15px Segoe UI;padding:30px">Select a protein, pocket or calculated pose.</body></html>');self._loaded=True
    def hideEvent(self,event):
        super().hideEvent(event)
        if self._loaded and not getattr(self,'_exporting',False):
            self.page().runJavaScript('window.pauseViewer && window.pauseViewer()')
            QTimer.singleShot(0,self._freeze_hidden)
    def _freeze_hidden(self):
        if self._loaded and not self.isVisible() and not getattr(self,'_exporting',False):self.page().setLifecycleState(QWebEnginePage.LifecycleState.Frozen)
    @staticmethod
    def prepare_data(protein,ligand=None,pockets=(),contacts=(),context=None):
        from scientific.geometry import viewer_contacts
        from scientific.molecules import read_sdf
        from rdkit import Chem
        protein=Path(protein);normalized=viewer_contacts(protein,ligand,contacts) if ligand and contacts else []
        for index,c in enumerate(normalized):c.setdefault('id','view_'+str(index))
        residue_colors={};charges={}
        for c in normalized:
            meta=json.loads(c.get('metadata') or '{}');key=c['chain']+':'+c['residue_number']+':'+c.get('insertion_code','');charges[key]=meta.get('residue_formal_charge')
        atoms=[]
        if protein.suffix.lower() not in ['.cif','.mmcif']:
            for line in protein.read_text(encoding='utf-8',errors='replace').splitlines():
                if line.startswith(('ATOM  ','HETATM')):
                    name=line[17:20].strip();key=line[21:22].strip()+':'+str(int(line[22:26]))+':'+line[26:27].strip();atoms.append({'serial':int(line[6:11]),'name':line[12:16].strip(),'residue':key,'xyz':[float(line[k:k+8]) for k in [30,38,46]],'element':line[76:78].strip()})
                    residue_colors[key]={mode:residue_color(name,mode,charges.get(key)) for mode in MODES}
        protein_bonds=None
        if protein.with_suffix('.sdf').exists():
            from scientific.geometry import load_receptor
            graph=load_receptor(protein);protein_bonds=[[b.GetBeginAtomIdx(),b.GetEndAtomIdx(),b.GetBondTypeAsDouble()] for b in graph.GetBonds()]
        ligand_atoms=[];ligand_bonds=[]
        if ligand:
            mol=read_sdf(ligand,removeHs=False)[0];ligand_atoms=[{'index':a.GetIdx(),'element':a.GetSymbol(),'xyz':list(mol.GetConformer().GetAtomPosition(a.GetIdx()))} for a in mol.GetAtoms()];ligand_bonds=[[b.GetBeginAtomIdx(),b.GetEndAtomIdx(),b.GetBondTypeAsDouble()] for b in mol.GetBonds()]
        data={'pdb':protein.read_text(encoding='utf-8',errors='replace'),'format':'cif' if protein.suffix.lower() in ['.cif','.mmcif'] else 'pdb','sdf':Path(ligand).read_text(encoding='utf-8') if ligand else '', 'pockets':list(pockets),'contacts':normalized,'protein_atoms':atoms,'verify_atoms':bool(normalized) or protein.with_suffix('.sdf').exists(),'ligand_atoms':ligand_atoms,'residue_colors':residue_colors,'interactions':INTERACTIONS,'context':context or {'protein':protein.stem,'ligand':Path(ligand).stem if ligand else ''},'charge_note':CHARGE_NOTE}
        data.update(protein_bonds=protein_bonds,ligand_bonds=ligand_bonds);return data
    def display(self,protein,ligand=None,pockets=(),contacts=(),context=None):
        self.display_data(self.prepare_data(protein,ligand,pockets,contacts,context))
    def display_data(self,data):
        self.last_data=data
        template=resource('app','resources','molecular_viewer.html').read_text(encoding='utf-8');html=template.replace('__3DMOL__',resource('app','resources','3Dmol-min.js').as_uri()).replace('__VIEWER_JS__',resource('app','resources','molecular_viewer.js').as_uri()).replace('__DATA__',json.dumps(data,ensure_ascii=True).replace('<','\\u003c'))
        folder=user_data()/'viewer';folder.mkdir(exist_ok=True);path=folder/('molecule_'+self.viewer_id+'.html');path.write_text(html,encoding='utf-8');url=QUrl.fromLocalFile(str(path))
        if self.isVisible():self.page().setLifecycleState(QWebEnginePage.LifecycleState.Active);self.load(url);self._loaded=True
        else:self._pending_url=url
    def focus_contact(self,contact_id):self.page().runJavaScript('window.focusContact && window.focusContact('+json.dumps(str(contact_id))+')')
    def export_png(self,path,dpi=300,width=2400,height=1800,callback=None):
        if getattr(self,'_exporting',False):
            if callback:callback(False)
            return
        self._exporting=True;deadline=time.monotonic()+90
        self.page().setLifecycleState(QWebEnginePage.LifecycleState.Active)
        if self._pending_url:self.load(self._pending_url);self._pending_url=None;self._loaded=True
        def finish(ok):
            self._exporting=False
            self._freeze_hidden()
            if callback:callback(ok)
        def save(data):
            if isinstance(data,dict) and data.get('pending'):
                if time.monotonic()<deadline:QTimer.singleShot(100,request)
                else:self.page().runJavaScript('window.cancelPNG && window.cancelPNG()');finish(False)
                return
            ok=False
            try:
                if isinstance(data,str) and data.startswith('data:image/'):
                    image=QImage.fromData(base64.b64decode(data.split(',',1)[1]));image=image.scaled(width,height,Qt.AspectRatioMode.IgnoreAspectRatio,Qt.TransformationMode.SmoothTransformation);image.setDotsPerMeterX(round(dpi/.0254));image.setDotsPerMeterY(round(dpi/.0254));ok=image.save(str(path))
            finally:finish(ok)
        def request():self.page().runJavaScript(f'window.exportPNG ? window.exportPNG({int(width)},{int(height)}) : null',save)
        request()
