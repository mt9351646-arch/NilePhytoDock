"""Reviewed table and sample mappings for Egyptian botanical literature.

Each observation keeps the exact raw table row. Names are only corrected where
the source context identifies the chemical unambiguously; no structures inferred.
"""
import json,re,sys
from pathlib import Path
from lxml import etree
from tools.research_ncbi import plain,ROOT
sys.stdout.reconfigure(encoding='utf-8')
profiles=[];references={}
def source(pmc):
    d=json.loads((ROOT/(pmc+'.json')).read_text(encoding='utf-8'))
    references[pmc]={k:d[k] for k in ['title','doi','sha256','license']};references[pmc]['url']='https://pmc.ncbi.nlm.nih.gov/articles/'+pmc+'/'
    return d
def table(pmc,tid):
    d=source(pmc);return next(t for t in d['tables'] if t['id']==tid)
def profile(pmc,tid,species,label,part,origin,method='Hydrodistillation; GC-MS',kind='Essential oil',basis='GC peak area %',rankable=True,geo='Egyptian collection documented',notes=''):
    t=table(pmc,tid);p=dict(pmcid=pmc,table_id=tid,table_number=int(re.search(r'(\d+)$',tid)[0]),species=species,label=label,part=part,origin=origin,method=method,type=kind,basis=basis,rankable=rankable,geography_status=geo,notes=notes,observations=[]);profiles.append(p);return p
def add(p,name,cell,row,raw,unit=None,canonical=None,annotation='Published GC-MS library/retention annotation',notes=''):
    original=name;name=canonical or name;cell=cell.strip();unit=unit or p['basis']
    if cell.lower() in ['', '-', '–', '—', '_', '__', 'nd', 'n.d.']:return
    if cell.lower() in ['trace','tr','tr.']:v=None;sd=None;status='trace'
    elif cell=='presence':v=None;sd=None;status='presence_only'
    else:
        m=re.match(r'^(\d+(?:\.\d+)?)\s*(?:±\s*(\d+(?:\.\d+)?))?',cell)
        if not m:raise ValueError((p['species'],name,cell))
        v=float(m[1]);sd=float(m[2]) if m[2] else None;status='reported_zero' if v==0 else 'reported'
    p['observations'].append(dict(name=name.strip(),original_name=original,value=v,sd=sd,unit=unit,status=status,source_row=row,raw=raw,annotation=annotation,notes=notes))

# Published major-component table only. Oil yield and retention index are not
# constituents or composition percentages; the incomplete scope is explicit.
pmc='PMC6044011';tid='Tab1';t=table(pmc,tid)
for row,r in enumerate(t['rows'][1:],2):
    species=re.sub(r'\s*\([\d.]+\)$','',r[0]);part='Fruit peels' if species.startswith('Citrus') else 'Leaves'
    p=profile(pmc,tid,species,'Northern Egypt 2016 major constituents',part,'Alexandria, Behera and Matrouh, Egypt',notes='Table 1 reports major constituents only, not a complete chromatogram. Original oil yield is in raw row. No rescaling. Taxon and unusual chemical spellings retained as published.')
    for m in re.finditer(r'(.*?)\s*\((\d+(?:\.\d+)?),\s*(\d+)\)',r[1]):
        name=m[1].lstrip(', ').strip();name=re.sub(r'\s*[–-]\s*','-',name)
        add(p,name,m[2],row,r,notes='Retention index '+m[3]+'; major-constituent subset.')

# Three oils actually chromatographed in Table 4; the other five plants used
# in the bioassay are not invented as composition profiles.
pmc='PMC9605189';tid='life-12-01587-t004';t=table(pmc,tid)
for col,species,label in [(5,'Cymbopogon citratus','Lemongrass'),(6,'Thymus vulgaris','Thyme'),(7,'Mentha spicata','Spearmint (published as Mentha virdis)')]:
    p=profile(pmc,tid,species,label+' Giza 2018','Aerial material','Medicinal and Aromatic Plants Experimental Station, Cairo University, Giza, Egypt',notes='Mean of three GC-MS runs; SD retained. Source spelling Mentha virdis is mapped to spearmint Mentha spicata (Mentha viridis synonym); original label is retained.')
    for row,r in enumerate(t['rows'][2:],3):
        if len(r)>=10 and re.fullmatch(r'\d+',r[0]):add(p,r[2],r[col],row,r)

pmc='PMC8398089';tid='plants-10-01721-t001';t=table(pmc,tid)
for col,species,label,origin in [(4,'Rosa banksiae','Banksian rose aerial parts','Merryland Botanical Garden, Cairo, Egypt'),(5,'Rosa multiflora','Orange fairy rose aerial parts','Kirdassa, Giza, Egypt'),(6,'Rosa multiflora','White fairy rose aerial parts','Kirdassa, Giza, Egypt'),(7,'Rosa banksiae','Banksian rose flowers','Merryland Botanical Garden, Cairo, Egypt'),(8,'Rosa multiflora','Orange fairy rose flowers','Kirdassa, Giza, Egypt'),(9,'Rosa multiflora','White fairy rose flowers','Kirdassa, Giza, Egypt')]:
    p=profile(pmc,tid,species,label+' 2016','Flowers' if col>=7 else 'Aerial parts',origin,notes='Source calls R. multiflora R. polyantha (synonym). Table includes constituents reaching >=2% in at least one sample; not a full chromatogram. These are Egyptian garden rose taxa, not Damask rose.')
    for row,r in enumerate(t['rows'][2:],3):
        if len(r)>=10 and re.fullmatch(r'\d+\.',r[0]):
            name=re.sub(r'\s*\*?,?\s*[abceh]$','',r[1]).replace(' *','');add(p,name,r[col],row,r)

pmc='PMC12988214';tid='Tab2';t=table(pmc,tid)
origins={'Js':'Ain Shams University medicinal plants station, Cairo, Egypt','Ja':'Banha, Al Qalyubia, Egypt','Jg':'Shubra Belola, Gharbia, Egypt','Jm':'Bagour, Menofia, Egypt'}
names={'Js':'Jasminum sambac','Ja':'Jasminum azoricum','Jg':'Jasminum grandiflorum','Jm':'Jasminum multiflorum'}
for col,code in enumerate(t['rows'][0][5:],5):
    prefix,month=code.split();p=profile(pmc,tid,names[prefix],code+' flower headspace 2022','Flowers',origins[prefix],method='HS-GC-MS',kind='Headspace volatile profile',rankable=False,notes='Flower headspace, not an extracted essential oil. Collection month retained. Concrete and absolute composition was not inferred from the headspace table.')
    for row,r in enumerate(t['rows'][1:],2):
        if len(r)==15 and r[0].isdigit():add(p,r[2],r[col],row,r)

pmc='PMC13338266'
for tid,offset,species,labels in [('Tab2',3,'Citrus sinensis',['Washington Navel','Balady Seeded Orange','Blood Orange','Sweet Orange Sukkari']),('Tab3',3,'Citrus reticulata',['Yousfy Balady','Ponkan Chinese Honey','Murcott','Clementine','Dancy Tangerine']),('Tab4',3,None,['Key Lime','Sweet Lime']),('Tab5',3,'Citrus paradisi',['Tangelo Seminole'])]:
    t=table(pmc,tid)
    for j,label in enumerate(labels):
        sp=species or ['Citrus aurantifolia','Citrus limettioides'][j]
        p=profile(pmc,tid,sp,label+' peel oil 2022-2023','Fruit peels','Private garden, Atia Street, Beni-Suef, Egypt',notes='Separate cultivar and oil profile. Source table values preserved; no rescaling. Published taxon labels retained, including Tangelo Seminole as C. paradisi.')
        for row,r in enumerate(t['rows'],1):
            if len(r)>offset+j and r[0].isdigit():add(p,r[1],r[offset+j],row,r)

pmc='PMC9767472';tid='tbl1';t=table(pmc,tid)
for col,sp,label in [(2,'Salvia officinalis','Common sage'),(3,'Lavandula angustifolia','Lavender')]:
    p=profile(pmc,tid,sp,label+' El-Orman 2020','Flowering aerial parts','El-Orman Garden, Giza, Egypt',method='Hydrodistillation; GC-FID and GC-MS',notes='Unknown peak and Total row excluded as non-compounds. Trace retained without an invented percentage. Source total is internally inconsistent; individual values retained for review.')
    for row,r in enumerate(t['rows'][1:],2):
        if len(r)==4 and r[1].lower() not in ['unknown','total']:add(p,r[1],r[col],row,r,canonical={'Myrecene':'Myrcene','1.8-Cineole':'1,8-Cineole'}.get(r[1]))

# White Egyptian water lily. The newer blue-lily paper has contradictory plant
# identification in its Methods and is excluded pending taxonomic clarification.
pmc='PMC5240310'
p=profile(pmc,'Tab1','Nymphaea alba','White water lily leaf ethanol extract 2013','Leaves','El-Orman Gardens, Giza, Egypt',method='70% aqueous ethanol extraction; LC-HRESI-MS/MS',kind='Solvent extract',basis='Qualitative presence',rankable=False,notes='Tentative LC-MS annotations; no abundance values reported. Derivatives and unspecified glycosides remain unresolved.')
for row,r in enumerate(table(pmc,'Tab1')['rows'][1:],2):
    if r[0].isdigit():add(p,r[1],'presence',row,r,annotation='Tentative LC-HRESI-MS/MS identification')
for tid,label,kind in [('Tab2','Unsaponifiable leaf fraction','Unsaponifiable fraction'),('Tab3','Leaf fatty-acid fraction','Fatty-acid pool')]:
    p=profile(pmc,tid,'Nymphaea alba',label+' 2013','Leaves','El-Orman Gardens, Giza, Egypt',method='GLC; separate lipid fractions',kind=kind,basis='Fraction composition %',rankable=False,notes='Percentage of a separated lipid fraction, not intact essential-oil composition. Fatty acid names do not imply free acids in the original plant.')
    for row,r in enumerate(table(pmc,tid)['rows'][1:],2):
        if len(r)==2 and not r[0].lower().startswith(('total','identified','saturated','unsaturated')):add(p,r[0],r[1],row,r)

pmc='PMC12957211';tid='tab1';t=table(pmc,tid)
for row,r in enumerate(t['rows'][1:],2):
    p=profile(pmc,tid,'Curcuma longa','Turmeric rhizome extract '+r[0],'Rhizomes','SEKEM, Heliopolis, Cairo, Egypt',method='Ethanolic extraction; HPLC-PDA',kind='Solvent extract',basis='ug/mL extract solution',rankable=False,notes='Control and laser-treated samples kept separate. Solution concentrations are not oil percentages.')
    for col,name in enumerate(t['rows'][0][1:],1):add(p,name,r[col],row,r,annotation='HPLC with curcuminoid standards')

pmc='PMC11325491';tid='tbl2';t=table(pmc,tid)
p=profile(pmc,tid,'Vitis vinifera','Roumy Ahmer grape seed ethanol extract','Seeds','Gharbia local market, Egypt; cultivation origin not established',method='95% ethanol extraction; HPLC',kind='Solvent extract',basis='ug/g extract',rankable=False,geo='Egyptian market sample; growing origin unverified',notes='Source abbreviates phenolic acid names. Expanded acid names follow Table 2 phenolic context; raw text retained. Source qurecetin spelling corrected to quercetin.')
acid_names=['gallic','protocatechuic','p-hydroxybenzoic','gentisic','chlorogenic','caffeic','syringic','vanillic','ferulic','sinapic','p-coumaric','rosmarinic','cinnamic']
for row,r in enumerate(t['rows'][1:],2):add(p,r[0],r[1],row,r,canonical=r[0]+' acid' if r[0] in acid_names else 'Quercetin' if r[0]=='qurecetin' else r[0],annotation='Published targeted HPLC annotation')

pmc='PMC10788201';tid='tbl1';t=table(pmc,tid)
p=profile(pmc,tid,'Hibiscus sabdariffa','Roselle calyx water extract','Calyces','Market sample in Egyptian study; geographical origin not reported',method='Water extraction; HPLC-DAD',kind='Water extract',basis='ug/g extract as reported',rankable=False,geo='Study in Egypt; sample growing origin unverified',notes='Do not interpret as hibiscus essential oil. Published source does not establish cultivation location. No data from mixed herbal syrup imported.')
for row,r in enumerate(t['rows'][2:],3):add(p,r[0],r[4],row,r,canonical='Caffeic acid' if r[0]=='Coffeic acid' else r[0],annotation='Published targeted HPLC annotation')

pmc='PMC11607071';tid='Tab2';t=table(pmc,tid)
p=profile(pmc,tid,'Olea europaea','Pure olive oil fatty-acid pool before maceration','Fruit oil','Egyptian NRC study; olive oil cultivation origin not reported',method='GC analysis of fatty acid composition',kind='Fixed oil fatty-acid pool',basis='Fatty acid GC area %',rankable=False,geo='Study in Egypt; sample growing origin unverified',notes='Pure olive column only, not rosemary-macerated olive. Fatty-acid pool cannot be treated as the abundance of free acids or intact triglycerides. No oil index.')
for row,r in enumerate(t['rows'][2:6],3):add(p,r[0],r[4],row,r,canonical=re.sub(r'\s*\(C[\d:]+\)','',r[0]),annotation='Published GC fatty acid assignment')

manifest={'format':1,'retrieved_at':'2026-10-29','policy':'Primary NCBI PMC papers only. Open-access JATS cached via Europe PMC. Raw rows, methods, sample geography and measurement units retained. A named compound is not a verified chemical structure. No invented peaks, source locations or normalized percentages.','exclusions':['PMC12717157: Methods names N. nucifera while title/table name Nymphaea nouchali var. caerulea; unresolved taxonomic conflict.','PMC8924206: commercial oils with unverified growing origin and unusual tentative library assignments; not used.','PMC12869296: Egyptian cultivated olive confirmed, but LC-MS annotation table available only on request; no LC-MS composition invented.'],'references':references,'profiles':profiles}
path=ROOT/'reviewed_manifest.json';path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
confirmed={p['species'] for p in profiles if p['geography_status']=='Egyptian collection documented'}
print(len(profiles),'profiles;',len({p['species'] for p in profiles}),'taxa;',len(confirmed),'taxa with documented Egyptian collection;',sum(len(p['observations']) for p in profiles),'observations')
print('\n'.join(sorted(confirmed)))
assert len(confirmed)>=25
