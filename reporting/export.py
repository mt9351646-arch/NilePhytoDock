import csv
import json
import shutil
from pathlib import Path
from xml.sax.saxutils import escape
from database.store import rows
from scientific.ranking import project_rankings,multi_target
from visualization.figures import charts

LIMITATIONS='Docking scores are computational predictions, not measured binding affinities or evidence of biological activity. Oil indices prioritize documented constituent profiles and do not model mixture synergy, antagonism, bioavailability or whole-oil binding. Relative GC–MS peak area is not an absolute mass fraction. Partial coverage, uncertain identities, protonation and receptor structure quality limit interpretation.'
REPORT_COLUMNS={'Functional group associations':['functional_group','interaction_type','protein_residues','distinct_compounds','interaction_events'],'Group presence':['compound','group','directly_participating'],'Structural clusters':['compound','cluster','scaffold'],'Molecular similarities':['compound_a','compound_b','tanimoto'],'Interaction similarities':['protein','pocket_id','compound_a','compound_b','jaccard'],'Analysis methods':['topic','description']}

def datasets(db,pid):
    from scientific.contact_store import ensure_project_contacts
    ensure_project_contacts(db,pid)
    project=rows(db,'SELECT * FROM analysis_projects WHERE id=?',(pid,))[0]
    settings=json.loads(project['settings'])
    results=rows(db,'SELECT t.name AS protein,c.name AS compound,po.rank AS pocket,p.rank AS pose,p.score,r.status,r.error,r.engine_version,r.elapsed,p.sdf_path,p.complex_path FROM docking_runs r JOIN protein_targets t ON t.id=r.protein_id JOIN chemical_compounds c ON c.id=r.compound_id JOIN predicted_pockets po ON po.id=r.pocket_id LEFT JOIN docking_poses p ON p.run_id=r.id WHERE r.project_id=? ORDER BY t.name,p.score',(pid,))
    contacts=rows(db,'SELECT t.name AS protein,c.name AS compound,p.rank AS pose,i.* FROM molecular_interactions i JOIN docking_poses p ON p.id=i.pose_id JOIN docking_runs r ON r.id=p.run_id JOIN protein_targets t ON t.id=r.protein_id JOIN chemical_compounds c ON c.id=r.compound_id WHERE r.project_id=?',(pid,))
    ranks=project_rankings(db,pid);names={r['id']:r['name'] for r in rows(db,'SELECT * FROM oil_profiles')};targets={r['id']:r['name'] for r in rows(db,'SELECT * FROM protein_targets WHERE project_id=?',(pid,))}
    oil=[{'protein':targets[t],'profile':names[r['profile_id']],**r} for t,rs in ranks.items() for r in rs]
    target_weights={t:settings.get('target_weights',{}).get(str(t),1) for t in targets}
    combined=[{'profile':names[r['profile_id']],**r} for r in multi_target(ranks,target_weights)] if ranks else []
    refs=rows(db,"SELECT DISTINCT r.* FROM scientific_references r JOIN oil_profiles p ON p.reference_id=r.id WHERE p.id IN ("+','.join('?' for _ in settings['profiles'])+")",settings['profiles'])
    boxes=rows(db,'SELECT DISTINCT t.name AS protein,p.rank AS pocket,p.center,p.size AS dimensions,p.method,p.score,p.probability FROM predicted_pockets p JOIN protein_targets t ON t.id=p.protein_id JOIN docking_runs r ON r.pocket_id=p.id WHERE r.project_id=? ORDER BY t.name,p.rank',(pid,))
    for box in boxes:
        center=json.loads(box.pop('center'));box.update(center_x=center[0],center_y=center[1],center_z=center[2])
    observations=rows(db,"SELECT op.name AS profile,c.name AS compound,pc.original_name,COALESCE(pc.reported_value,pc.percentage) AS reported_value,COALESCE(pc.reported_unit,'GC peak area %') AS reported_unit,pc.sd,pc.annotation_level,op.profile_type,op.origin,op.geography_status,CASE WHEN pc.docking_eligible=0 THEN 'Source identity review - excluded' WHEN s.status='ready' THEN 'Ready' ELSE 'Structure review - excluded' END AS docking_status,ref.citation,pc.source_table,pc.source_row FROM profile_compounds pc JOIN oil_profiles op ON op.id=pc.profile_id JOIN chemical_compounds c ON c.id=pc.compound_id LEFT JOIN compound_structures s ON s.compound_id=c.id JOIN scientific_references ref ON ref.id=pc.reference_id WHERE op.id IN ("+','.join('?' for _ in settings['profiles'])+")",settings['profiles'])
    from scientific.molecular_analysis import analyze
    analysis=analyze(db,pid);similarity=analysis['chemical_similarity'];labels=similarity['labels']
    extra={'Functional group associations':analysis['functional_group_interactions'],'Group presence':analysis['presence_vs_participation'],'Structural clusters':[{'compound':v['compound'],'identity':k,'cluster':v['cluster'],'scaffold':v['scaffold'],'smiles':v['smiles']} for k,v in analysis['compound_details'].items()],'Molecular similarities':[{'compound_a':labels[i],'compound_b':labels[j],'tanimoto':value} for i,row in enumerate(similarity['matrix']) for j,value in enumerate(row) if j<=i],'Interaction similarities':[{'protein':cohort['protein'],'pocket_id':cohort['pocket_id'],'compound_a':cohort['interaction_similarity']['labels'][i],'compound_b':cohort['interaction_similarity']['labels'][j],'jaccard':value} for cohort in analysis['site_cohorts'] for i,row in enumerate(cohort['interaction_similarity']['matrix']) for j,value in enumerate(row) if j<=i],'Analysis methods':[{'topic':'Functional Group Contributions and Molecular Similarity Analysis','description':f"{len(analysis['compound_details'])} distinct structures; {similarity['cluster_count']} structural clusters. "+analysis['interpretation']+' '+similarity['method']}]+[{'topic':s['protein']+' pocket '+str(s['pocket_id'])+' enrichment','description':s['enrichment']['reason']} for s in analysis['site_cohorts']]}
    return project,settings,{'Source observations':observations,'Pocket boxes':boxes,'Docking results':results,'Interactions':contacts,'Oil ranking':oil,'Multi target':combined,**extra},refs

def export_all(db,pid,folder,dpi=300):
    from scientific.runtime import checkpoint
    checkpoint();folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    project,settings,tables,refs=datasets(db,pid)
    from openpyxl import Workbook
    from openpyxl.styles import Font,PatternFill
    book=Workbook();book.remove(book.active)
    def clean(v):return json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v
    for title,data in tables.items():
        checkpoint()
        ws=book.create_sheet(title)
        if not data:ws.append(['No calculated records']);continue
        keys=list(data[0]);ws.append(keys)
        with (folder/(title.lower().replace(' ','_')+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.writer(f);writer.writerow(keys)
            for row in data:
                vals=[clean(row.get(k)) for k in keys];writer.writerow(vals)
                # Avoid interpreting source names as Excel formulas.
                ws.append([("'"+v) if isinstance(v,str) and v.startswith(('=','+','-','@')) else v for v in vals])
        for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='174B58')
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
        for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=min(55,max(15,len(str(col[0].value))+3))
    book.save(folder/'screening_results.xlsx')
    figures=charts(db,pid,folder/'figures',dpi)
    from app.branding import VERSION,DEVELOPERS
    provenance={'application':{'name':'NilePhytoDock','version':VERSION,'developers':DEVELOPERS},'project':project,'settings':settings,'references':refs,'limitations':LIMITATIONS,'tables':tables}
    analysis=db.execute('SELECT result FROM molecular_analysis_runs WHERE project_id=? ORDER BY id DESC LIMIT 1',(pid,)).fetchone()
    if analysis:(folder/'molecular_analysis.json').write_text(analysis[0],encoding='utf-8')
    (folder/'reproducibility.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
    checkpoint();write_docx(project,settings,tables,refs,figures,folder/'scientific_report.docx')
    checkpoint();write_pdf(project,settings,tables,refs,figures,folder/'scientific_report.pdf')
    return folder

def narrative(project,settings):
    settings={k:v for k,v in settings.items() if k not in ['pocket_selections','center','box_size']}
    settings['box_details']='Per-protein geometry is listed in Pocket boxes.'
    return [('Study',project['name']+' — NilePhytoDock by Ahmed G Soliman and Malak Taha. Project status: '+project['status']),('Methods','Composition records were extracted from the supplied Word documents, supplementary CSV and primary PMC literature with original names, sample distinctions, analytical units, uncertainties and references retained. Extract concentrations, headspace and fatty-acid pools do not receive an oil index. Source-specific identity-review observations are excluded from docking and covered peak area. Ligands were validated with RDKit, embedded using ETKDGv3 (seed 20261029) and minimized with MMFF94s or UFF. Only approved local structures were screened. Receptors use the first model, highest occupancy alternate locations and configurable water/heterogen selection. RDKit establishes the receptor graph and applies explicit standard-residue protonation approximations before H addition; OpenBabel assigns Gasteiger charges. This is not a site-specific pKa calculation. Missing backbone atoms cause a visible preparation failure; missing residues and side chains are not rebuilt. P2Rank 2.5.1 predicts pockets unless a custom/reference box is selected. Smina 2020.12.10 performs rigid receptor docking. ProLIF classifies interactions using chemical identities and geometry; interaction failures are recorded. Metal candidates are reported only when the complete Zn tetrahedral or Mg octahedral shell passes the documented chemical, distance and angular checks.'),('Parameters','; '.join(f'{k}={v}' for k,v in settings.items())),('Ranking','For each protein, use the best score per compound over the selected pockets and poses. q = (N − average ascending energy rank)/(N − 1); a single compound receives q=0.5. Oil index = sum(w*q)/sum(w) over successfully screened constituents with positive published peak areas. Original percentages are retained. Duplicate compound entries suppress the affected profile index. Headspace, HPLC concentrations, qualitative extracts and fatty-acid pools have no oil index. Coverage is the sum of screened published peak areas; <70% is flagged. Sensitivity varies each included abundance by ±10%, one at a time. Multi-target index averages these normalized indices with explicit target weights; a missing selected target makes the combined index unavailable.'),('Interpretation and limitations',LIMITATIONS)]

def write_docx(project,settings,tables,refs,figures,path):
    from docx import Document
    from docx.shared import Inches,Pt,RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from app.branding import VERSION
    d=Document();d.core_properties.author='Ahmed G Soliman and Malak Taha';d.core_properties.last_modified_by='NilePhytoDock '+VERSION;d.core_properties.title='NilePhytoDock scientific screening report';sec=d.sections[0];sec.header.paragraphs[0].text='Ahmed G Soliman and Malak Taha | NilePhytoDock'
    for name in ['Title','Heading 1','Heading 2']:
        d.styles[name].font.color.rgb=RGBColor(0,0,0)
    d.styles['Normal'].font.name='Calibri';d.styles['Normal'].font.size=Pt(10)
    d.add_heading('Botanical constituent screening report',0)
    for title,text in narrative(project,settings):d.add_heading(title,1);d.add_paragraph(text)
    for name,items in tables.items():
        d.add_heading('Functional Group Contributions and Molecular Similarity Analysis' if name=='Analysis methods' else name,1)
        if not items:d.add_paragraph('No calculated records available.');continue
        keys={**REPORT_COLUMNS,'Source observations':['compound','reported_value','reported_unit','docking_status'],'Pocket boxes':['protein','pocket','center_x','center_y','center_z','dimensions'],'Docking results':['protein','compound','pose','score','status'],'Interactions':['protein','compound','residue','interaction_type','distance'],'Oil ranking':['protein','profile','index','screened_peak_area_percent'],'Multi target':['profile','combined_index']}[name]
        caption=d.add_paragraph(f'{len(items)} records. Full machine-readable data are included in the companion CSV/XLSX files. Report tables show up to 100 records per category.');caption.paragraph_format.keep_with_next=True
        table=d.add_table(rows=1,cols=len(keys));table.style='Light Shading Accent 1'
        borders=OxmlElement('w:tblBorders')
        for side in ['top','left','bottom','right','insideH','insideV']:
            border=OxmlElement('w:'+side);border.set(qn('w:val'),'single');border.set(qn('w:sz'),'4');border.set(qn('w:color'),'D9D9D9');borders.append(border)
        table._tbl.tblPr.append(borders)
        for cell,k in zip(table.rows[0].cells,keys):cell.text=k.replace('_',' ')
        repeat=OxmlElement('w:tblHeader');table.rows[0]._tr.get_or_add_trPr().append(repeat)
        for row in items[:100]:
            for cell,k in zip(table.add_row().cells,keys):
                v=row.get(k);cell.text=f'{v:.3f}' if isinstance(v,float) else str(v if v is not None else 'Unavailable')
    for f in figures:d.add_heading(f.stem.replace('_',' ').capitalize(),1);d.add_picture(str(f),width=Inches(6));d.add_paragraph('Calculated project results. Missing values represent unavailable calculations.')
    d.add_heading('Source references',1)
    for r in refs:d.add_paragraph(r['citation'] or r['source_document'])
    for style in d.styles:
        for border in list(style.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
    for paragraph in d.paragraphs:
        for border in list(paragraph._p.iter(qn('w:pBdr'))):border.getparent().remove(border)
    d.save(path)

def write_pdf(project,settings,tables,refs,figures,path):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from app.paths import resource
    font=resource('app','resources','fonts','DejaVuSans.ttf')
    if not font.exists():
        import matplotlib
        font=Path(matplotlib.get_data_path())/'fonts/ttf/DejaVuSans.ttf'
    if 'NileUnicode' not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont('NileUnicode',str(font)))
    styles=getSampleStyleSheet();flow=[Paragraph('Botanical constituent screening report',styles['Title']),Paragraph('NilePhytoDock | Ahmed G Soliman and Malak Taha',styles['Normal']),Spacer(1,18)]
    for style in styles.byName.values():style.fontName='NileUnicode'
    def para(text,style='BodyText'):return Paragraph(escape(str(text)).replace('\n','<br/>'),styles[style])
    for title,text in narrative(project,settings):flow.extend([para(title,'Heading1'),para(text),Spacer(1,8)])
    for name,data in tables.items():
        flow.append(para('Functional Group Contributions and Molecular Similarity Analysis' if name=='Analysis methods' else name,'Heading1'))
        if not data:flow.append(para('No calculated records available.'));continue
        keys={**REPORT_COLUMNS,'Source observations':['compound','reported_value','reported_unit','docking_status'],'Pocket boxes':['protein','pocket','center_x','center_y','center_z','dimensions'],'Docking results':['protein','compound','pose','score','status'],'Interactions':['protein','compound','residue','interaction_type','distance'],'Oil ranking':['protein','profile','index','screened_peak_area_percent'],'Multi target':['profile','combined_index']}[name]
        flow.append(para(f'{len(data)} records. First 100 shown; complete tables accompany this report as CSV/XLSX.'))
        widths=[480/len(keys)]*len(keys)
        cells=[[para(k.replace('_',' ')) for k in keys]]
        for r in data[:100]:cells.append([para(f'{r[k]:.3f}' if isinstance(r.get(k),float) else r.get(k) if r.get(k) is not None else 'Unavailable') for k in keys])
        t=Table(cells,colWidths=widths,repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e0ecee')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#d9d9d9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));flow.extend([t,Spacer(1,12)])
    from PIL import Image as PILImage
    for f in figures:
        w,h=PILImage.open(f).size;scale=min(480/w,590/h);flow.extend([PageBreak(),para(f.stem.replace('_',' ').capitalize(),'Heading1'),Image(str(f),width=w*scale,height=h*scale)])
    flow.append(para('Source references','Heading1'))
    for r in refs:flow.extend([para(r['citation'] or r['source_document']),Spacer(1,8)])
    SimpleDocTemplate(str(path),title='NilePhytoDock screening report',author='Ahmed G Soliman and Malak Taha',leftMargin=54,rightMargin=54).build(flow)
