"""Five missing oils; existing Egyptian thyme is evaluated without duplication."""
import json,re,hashlib
from pathlib import Path
from docx import Document
ROOT=Path('data/literature');refs={};profiles=[]
def ref(pmc):
 d=json.loads((ROOT/(pmc+'.json')).read_text(encoding='utf-8'));refs[pmc]={k:d[k] for k in ['title','doi','sha256','license']};refs[pmc]['url']='https://pmc.ncbi.nlm.nih.gov/articles/'+pmc+'/';return d
def profile(pmc,tid,sp,common,label,part,origin,extraction,analysis,geo,notes=''):
 ref(pmc);p={'pmcid':pmc,'table_id':tid,'table_number':1 if tid.startswith('Supplement') else int(re.search(r'(\d+)$',tid)[0]),'species':sp,'common_name':common,'label':label,'part':part,'origin':origin,'extraction_method':extraction,'analytical_method':analysis,'method':extraction+'; '+analysis,'type':'Essential oil','basis':'GC peak area %','rankable':True,'geography_status':geo,'notes':notes,'observations':[]};profiles.append(p);return p
def observation(p,name,value,row,raw):
 if value.lower() in ['-','–','—','nd','n.d','n.d.',''] or set(value.strip())<=set('-–—'):return
 match=re.fullmatch(r'(\d+(?:\.\d+)?)(?:\s*\((\d+(?:\.\d+)?)\))?',value.strip())
 if not match:raise ValueError((name,value))
 p['observations'].append({'name':name.strip(),'original_name':name.strip(),'value':float(match[1]),'sd':float(match[2]) if match[2] else None,'unit':'GC peak area %','status':'reported','source_row':row,'raw':raw,'annotation':'Published GC-MS/GC-FID assignment','notes':''})

pmc='PMC9563047';path=ROOT/(pmc+'_mmc1.docx');table_rows=[[c.text for c in row.cells] for row in Document(path).tables[0].rows]
(ROOT/(pmc+'_supplement_table1.json')).write_text(json.dumps({'source_file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'table':1,'rows':table_rows},ensure_ascii=False,indent=2),encoding='utf-8')
p=profile(pmc,'Supplementary_Table_1','Origanum majorana','Sweet Marjoram','Sweet marjoram Giza May 2020','Fresh aerial parts','Cairo University Experimental Station of Medicinal Plants, Giza, Egypt','Hydrodistillation, Clevenger, 5 h','GC-MS, Rtx-5MS','Egyptian collection documented','Complete supplementary component table; class totals and unknown peak excluded. Supplement file '+path.name+' SHA256 '+hashlib.sha256(path.read_bytes()).hexdigest())
for row,r in enumerate(table_rows,1):
 if not r[0] and r[1]!='Unknown' and re.match(r'^\d',r[4]):observation(p,r[1],r[4],row,r)

pmc='PMC9578474';tid='t0001';d=ref(pmc);t=next(t for t in d['tables'] if t['id']==tid)
p=profile(pmc,tid,'Ocimum basilicum','Sweet Basil','Sweet basil Tanta December 2018','Dried aerial parts','Medicinal plant farm, Faculty of Pharmacy, Tanta University, Egypt','Hydrodistillation, Clevenger','GC-MS','Egyptian collection documented')
for row,r in enumerate(t['rows'],1):
 if r[0].isdigit():observation(p,r[3],r[4],row,r)

pmc='PMC11666597';tid='Tab3';d=ref(pmc);t=next(t for t in d['tables'] if t['id']==tid)
p=profile(pmc,tid,'Foeniculum vulgare','Fennel','Sweet fennel untreated control cultivation plot','Fresh fruits','Egyptian cultivation study; Mepaco seed source; exact field coordinates not reported','Hydrodistillation, Clevenger, 3 h','GC-MS','Egyptian study with documented experimental cultivation','Control soil plot only: no treatment; irrigation every 15 days. Table 3 has separate treatment columns, not replicated oil identities.')
for row,r in enumerate(t['rows'],1):
 if len(r)==8 and re.fullmatch(r'\d+\.\d+',r[0]):observation(p,r[2],r[3],row,r)

pmc='PMC9570728';tid='plants-11-02617-t001';d=ref(pmc);t=next(t for t in d['tables'] if t['id']==tid)
p=profile(pmc,tid,'Cuminum cyminum','Cumin','Cumin Egyptian market January 2022','Dried fruits','Egyptian local market; cultivation origin not reported','Hydrodistillation, Clevenger, 5 h','GC-MS','Egyptian market sample; growing origin unverified','Do not assign a specific Egyptian growing site to this market sample. Only the C. cyminum column was imported, not anise or caraway.')
for row,r in enumerate(t['rows'],1):
 if len(r)==7 and re.fullmatch(r'\d+(?:\.\d+)?',r[3]) and re.fullmatch(r'\d+',r[1]):observation(p,r[0],r[3],row,r)

# Table 1 is a raster in the original PMC JATS. Transcribed from the cached
# original 488 by 722 image, not generated from an expected peppermint profile.
pmc='PMC5527698';image=ROOT/(pmc+'_Table1.jpg');raw_rows=[['RI','Constituents','Picsaera (%)'],['931','alpha-thujene','0.31'],['939','alpha-pinene','0.32'],['967','Verbenene','0.02'],['975','Sabinene','1.38'],['979','beta-pinene','0.53'],['1005','alpha-phellandrene','0.01'],['1026','P-cymene','0.03'],['1031','Limonene','3.01'],['1033','1,8-cineole','6.06'],['1070','Cis-sabinene hydrate','0.24'],['1098','Linalool','0.05'],['1123','Chrysanthenone','0.42'],['1152','Menthone','7.42'],['1164','Menthofuran','13.18'],['1165','Neomenthol','4.79'],['1171','Menthol','46.32'],['1177','terpinen-4-ol','0.04'],['1189','alpha-terpineol','0.03'],['1243','Carvone','1.02'],['1273','Neomenthylacetate','0.43'],['1295','Methyl acetate','12.10'],['1305','Isomenthylacetate','0.82'],['1352','alpha-terpinyl acetate','0.03'],['1388','beta-bourbonene','0.37'],['1409','alpha-gurjunene','0.03'],['1418','beta-caryophyllene','0.55'],['1460','alpha-humulene','0.01']]
(ROOT/(pmc+'_table1_transcription.json')).write_text(json.dumps({'source_image':image.name,'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'rows':raw_rows,'printed_total':99.51,'sum_of_individual_rows':99.52,'rounding_note':'Published individual rows sum to 99.52%; printed total is 99.51%. Neither is silently corrected.','note':'Greek alpha/beta printed in source are spelled out in the transcription. Original table image retained.'},ensure_ascii=False,indent=2),encoding='utf-8')
p=profile(pmc,'Table1','Mentha × piperita','Peppermint','Peppermint Taounate Morocco reference profile','Fresh aerial parts','National Institute of Medicinal and Aromatic Plants garden, Taounate, Morocco','Hydrodistillation, Clevenger, 3 h','GC-MS','Non-Egyptian reference sample','Documented Moroccan sample, not an Egyptian oil. Source table image SHA256 '+hashlib.sha256(image.read_bytes()).hexdigest()+'. The methyl acetate row at RI1295 is flagged for identity review rather than silently changed to menthyl acetate.')
for row,r in enumerate(raw_rows[1:],2):
 observation(p,r[1],r[2],row,r)
 if r[1]=='Methyl acetate':p['observations'][-1].update(docking_eligible=False,annotation='Source identity review required',notes='Published name methyl acetate at RI1295 is suspect; original value and name retained, observation excluded from docking and oil-index coverage until curated.')

manifest={'format':1,'retrieved_at':'2026-10-29','references':refs,'profiles':profiles,'evaluation':{'Origanum majorana':'New Egyptian oil; full supplementary composition','Thymus vulgaris':'Already documented in PMC9605189; no duplicate imported','Mentha × piperita':'New Moroccan reference; no unsupported Egyptian attribution','Ocimum basilicum':'New Egyptian farm sample','Foeniculum vulgare':'New experimental cultivation control; exact field coordinates not reported','Cuminum cyminum':'New Egyptian market sample; growing origin unverified'},'exclusions':['PMC6253825 lacks a clear peppermint collection location; not used for geographic attribution.','No pharmacological results or published docking scores were imported as application calculations.']}
Path('data/literature/six_oils_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(len(profiles),'new oils,',sum(len(p['observations']) for p in profiles),'observations; existing thyme retained')
