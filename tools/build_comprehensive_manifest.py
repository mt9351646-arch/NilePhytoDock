"""Reviewed primary chromatography records; never expand counts with guessed peaks."""
import hashlib,json,re
from pathlib import Path

ROOT=Path('data/literature');references={};profiles=[]
def article(pmc):
 d=json.loads((ROOT/(pmc+'.json')).read_text(encoding='utf-8'))
 references[pmc]={k:d[k] for k in ['title','doi','sha256','license']};references[pmc]['url']=f'https://pmc.ncbi.nlm.nih.gov/articles/{pmc}/';return d
def table(pmc,tid):return next(t for t in article(pmc)['tables'] if t['id']==tid)['rows']
def profile(pmc,tid,species,common,label,part,origin,method,analysis,category='Essential Oils',basis='GC peak area %',notes='',rankable=True):
 article(pmc);p=dict(pmcid=pmc,table_id=tid,table_number=int(re.search(r'(\d+)$',tid)[0]),species=species,common_name=common,label=label,part=part,origin=origin,extraction_method=method,analytical_method=analysis,method=method+'; '+analysis,category=category,type={'Essential Oils':'Essential oil','Fixed Oils':'Fixed oil fatty-acid pool','Botanical Extracts':'Botanical extract','Resins and Aromatic Preparations':'Resin/aromatic preparation'}[category],basis=basis,rankable=rankable if category=='Essential Oils' else False,geography_status='Egyptian collection documented' if 'Egypt' in origin and 'unverified' not in origin else 'Egyptian market; growing origin unverified' if 'Egypt' in origin else 'Non-Egyptian reference sample',notes=notes,observations=[]);profiles.append(p);return p
def obs(p,name,value,row,raw,unit=None,eligible=True,note='',annotation='Published analytical annotation'):
 value=str(value).strip();name=name.strip()
 if value.lower() in ['-','–','—','nd','n.d.','n.d','t','tr','trace','overlap','nda'] or not value:return
 match=re.match(r'^(\d+(?:\.\d+)?)(?:\s*±\s*(\d+(?:\.\d+)?))?',value)
 if not match:raise ValueError((name,value))
 v=float(match[1]);sd=float(match[2]) if match[2] else None
 if not v:return
 p['observations'].append(dict(name=name,original_name=name,value=v,sd=sd,unit=unit or p['basis'],status='reported',source_row=row,raw=raw,annotation=annotation,notes=note,docking_eligible=eligible))

for species,common,col in [('Pimpinella anisum','Anise',3),('Coriandrum sativum','Coriander',4)]:
 p=profile('PMC9023561','Tab1',species,common,common+' ARC Cairo August 2019','Dried fruits','Agricultural Research Center, Cairo, Egypt','Clevenger hydrodistillation','GC-MS')
 for i,r in enumerate(table(p['pmcid'],p['table_id']),1):
  if len(r)==7 and re.fullmatch(r'\d+',r[1]):obs(p,r[0],r[col],i,r)
p=profile('PMC13315271','Tab1','Matricaria chamomilla','German Chamomile','Untreated Heliopolis field quality markers','Flowers','Heliopolis University experimental field, Egypt','Hydrodistillation','GC-MS',notes='Source taxon Chamomilla recutita; Matricaria chamomilla synonym. Seven quality markers only, not a complete oil profile.')
for i,r in enumerate(table(p['pmcid'],p['table_id']),1):
 if len(r)==6 and r[0].isdigit():obs(p,r[2].removesuffix(' %'),r[3],i,r)
p=profile('PMC8615010','antioxidants-10-01844-t001','Allium sativum','Garlic','Arequipa Peru hydrodistilled bulb oil','Bulbs','Arequipa, Peru','Clevenger hydrodistillation 2 h','GC-MS',notes='Library-based identities remain tentative. Unknown peak excluded; published formula and mass are retained in the raw row, not used as structural confirmation.')
for i,r in enumerate(table(p['pmcid'],p['table_id']),1):
 if len(r)==6 and r[0].isdigit() and r[1]!='Unknown':obs(p,r[1],r[4],i,r,eligible=not any(x in r[1].lower() for x in ['androst','phthalate','siloxane']))
p=profile('PMC6435767','Tab1','Origanum vulgare','Oregano','Mepaco Egypt medicinal farm','Dried aerial parts','Mepaco medicinal farm, Egypt','Clevenger hydrodistillation 4 h','GC-MS')
for i,r in enumerate(table(p['pmcid'],p['table_id']),1):
 if len(r)==7 and r[0].isdigit():obs(p,r[2],r[5],i,r)
p=profile('PMC10537268','plants-12-03296-t001','Rosa × damascena','Damask Rose','Doalinn commercial rose oil','Flowers (commercial oil)','Doalinn, Türkiye; cultivation origin unverified','Commercial essential oil','GC-FID/MS',notes='Rosa × damascena retained separately from other Rosa species.')
for i,r in enumerate(table(p['pmcid'],p['table_id']),1):
 if len(r)==5 and r[0].isdigit():obs(p,r[1],r[2],i,r)
for sp,common,values in [('Cinnamomum camphora','Camphor / Ravintsara',[('1,8-Cineole','56.8'),('Sabinene','13.4'),('α-Terpineol','7.33')]),('Elettaria cardamomum','Cardamom',[('α-Terphenyl acetate','35.3'),('1,8-Cineole','32.3'),('Linalyl acetate','5.35'),('Linalool','3.35')])]:
 p=profile('PMC9936101','T1',sp,common,'Pranarom selected commercial constituents','Leaves' if sp.startswith('Cinnamomum') else 'Fruits','Pranarom, Belgium; cultivation origin unverified','Commercial steam-distilled oil','Supplier-selected constituent table',notes='Selected major constituents only. Camphor tree is the cineole-rich Ravintsara chemotype. Supplier table is weaker analytical evidence than an independently measured chromatogram.',rankable=False)
 rs=table(p['pmcid'],p['table_id']);idx=next(i for i,r in enumerate(rs,1) if r[0]==sp);raw=rs[idx-1]
 for name,v in values:obs(p,name,v,idx,raw,eligible='Terphenyl' not in name,note='Published terphenyl assignment is suspect; retained without silently correcting to terpinyl acetate.' if 'Terphenyl' in name else '')
p=profile('PMC4115333','T3','Camellia sinensis','Tea','NIST powdered leaf Soxhlet reference','Powdered leaves','NIST reference material; cultivation origin unverified','Exhaustive Soxhlet extraction','Validated HPLC-UV','Botanical Extracts','mg/g dry leaf',notes='Reference Soxhlet column only. Sonication header units differ from narrative and are not used. Not tea-seed oil or Melaleuca tea-tree oil.')
rs=article('PMC4115333')['tables'];t=next(t for t in rs if 'powdered leaf material recovery' in t['caption'].lower());p['table_id']=t['id'];p['table_number']=3
names={'GC':'(+)-Gallocatechin','EGC':'(-)-Epigallocatechin','C':'(+)-Catechin','EC':'(-)-Epicatechin','EGCG':'(-)-Epigallocatechin gallate','GCG':'(-)-Gallocatechin gallate','ECG':'(-)-Epicatechin gallate','Caffeine':'Caffeine'}
for i,r in enumerate(t['rows'],1):
 if r[0] in names:obs(p,names[r[0]],r[1],i,r)
rs=table('PMC7792775','molecules-26-00010-t001')
for i,r in enumerate(rs,1):
 if len(r)==6 and r[1][0].isdigit():
  p=profile('PMC7792775','molecules-26-00010-t001','Coffea arabica','Coffee',r[0]+' aqueous extract','Roasted beans','Royal Project Foundation, Chiang Mai, Thailand; commercial instant samples separately identified','Aqueous '+r[0].lower()+' preparation','HPLC','Botanical Extracts','µg/mg extract',notes='Two quantified markers only. Instant coffee commercial brand/origin differs from experimental beans; see source Methods 4.2.')
  if 'instant' in r[0].lower():p['origin']='Commercial instant coffee, Thailand study; cultivation origin unverified'
  for name,col in [('Chlorogenic acid',1),('Caffeine',2)]:obs(p,name,r[col],i,r)
p=profile('PMC7700282','plants-09-01627-t002','Prunus dulcis','Sweet Almond','Raw Casanova kernel fatty-acid pool','Raw kernels','Torre de Moncorvo, Portugal, 2019','Oil extraction and fatty-acid analysis','GC-FID','Fixed Oils','Fatty-acid %',notes='Raw Casanova column. Reported unusual long-chain proportions retained; fatty-acid pool after analysis is not evidence for native free acids or individual TAG species.')
for i,r in enumerate(table(p['pmcid'],p['table_id']),1):
 if len(r)==19 and i>2:obs(p,r[0]+' acid',r[1],i,r,eligible=False)
p=profile('PMC11740597','Tab2','Pistacia vera','Pistachio','Abbasiali Qom fatty-acid markers','Kernels','Jafariyeh, Qom, Iran, 2022–2023','Seed-oil extraction and FAME derivatization','GC-FID','Fixed Oils','Fatty-acid %',notes='Three individual fatty-acid markers only, not a complete profile or Pistacia lentiscus mastic resin.')
rs=table(p['pmcid'],p['table_id']);i=next(i for i,r in enumerate(rs,1) if r[0]=='Abbasiali' and len(r)==12);r=rs[i-1]
for name,col in [('Palmitic acid',5),('Oleic acid',6),('Linoleic acid',7)]:obs(p,name,r[col],i,r,eligible=False)
for code,sp,common in [('SESO','Sesamum indicum','Sesame'),('SAFO','Carthamus tinctorius','Safflower'),('FLAO','Linum usitatissimum','Flax')]:
 rs=table('PMC4110403','Tab1');origin=next(r[4] for r in rs if len(r)>4 and r[1]==code)
 p=profile('PMC4110403','Tab3',sp,common,code+' cold-pressed oil mean','Seeds',origin+'; commercial country of origin, not necessarily growing locality','Cold pressing; transesterification for analysis','GC-FID','Fixed Oils','Fatty-acid %',notes='Mean across commercial oils; n and country retained in Table 1. Not native free acids. Unspecified C17/C20 and class/other totals excluded. Linseed FLAO retained separately from low-linolenate Linola LINO.')
 rs=table(p['pmcid'],p['table_id']);i=next(i for i,r in enumerate(rs,1) if r[0]==code);r=rs[i-1]
 for col,name in {1:'Myristic acid',2:'Palmitic acid',3:'Palmitoleic acid',5:'Stearic acid',6:'Oleic acid',7:'Linoleic acid',8:'α-Linolenic acid',9:'γ-Linolenic acid',11:'Gondoic acid'}.items():obs(p,name,r[col],i,r,eligible=False)
p=profile('PMC10220419','tbl2','Ricinus communis','Castor','Hydraulic-pressed castor seed oil fatty-acid pool','Seeds','Nigeria study; exact growing locality not verified','Hydraulic pressing','Reported fatty-acid composition','Fixed Oils','Fatty-acid wt. %',notes='Table 2 source labels FFA; retained as analytical fatty-acid pool. Not the biodiesel/FAME product tables. Dihydroxylstearic name/formula notation is inconsistent and remains blocked.')
for i,r in enumerate(table(p['pmcid'],p['table_id']),1):
 if i>1:obs(p,r[0].split(' (')[0]+' acid',r[1],i,r,eligible=False)
p=profile('PMC4058451','Section_3_1','Punica granatum','Pomegranate','Rind bio-guided HPLC fraction marker','Dried fruit rind','Ibn-AlNafess herbalist, Beirut, Lebanon; cultivation origin unverified','Ethanolic extraction and bio-guided fractionation','HPLC','Botanical Extracts','Reported HPLC % (basis unspecified)',notes='Section 3.1 single gallic-acid marker; fraction, not pomegranate seed oil. The percentage denominator is not established, so no mixture weighting.')
raw=next(s['text'] for s in article(p['pmcid'])['sections'] if s['title'].startswith('3.1.'));assert '11.4' in raw;obs(p,'Gallic acid','11.4',1,[raw])
# Preserve questionable myrrh assignments without promoting them to prepared identities.
p=profile('PMC3796379','tI-ol-06-04-1140','Commiphora myrrha','Myrrh','Hydrodistilled commercial resin oil','Oleogum resin','Commercial drug material in China study; cultivation origin unverified','Hydrodistillation 3 h','GC-MS',notes='Published table contains questionable steroid and synthetic-looking library annotations. All assignments in this profile require source identity review; none are automatically docked.',rankable=False)
for i,r in enumerate(table(p['pmcid'],p['table_id']),1):
 if len(r)==4 and r[0].isdigit():obs(p,r[1],r[3],i,r,eligible=False,annotation='Published GC library assignment; source identity review')
p=profile('PMC12030047','pharmaceutics-17-00426-t002','Boswellia carterii','Frankincense','Harraz Cairo commercial frankincense oil','Commercial resin-derived essential oil','Harraz Co., Cairo, Egypt; growing origin unverified','Commercial essential oil','GC-MS',notes='Published GC assignments; isomers and unusual source names retained for review.')
for i,r in enumerate(table(p['pmcid'],p['table_id']),1):
 if len(r)==7 and r[0].isdigit():
  eligible=not any(x in r[2].lower() for x in ['isomer','phthal','androst','silox','fluoro','chloro'])
  obs(p,r[2],r[6],i,r,eligible=eligible)
p=profile('PMC7248992','molecules-25-02136-t001','Pistacia lentiscus','Mastic','MGEO-1 wild Cesme Uzunkoy','Air-dried gum resin','Cesme–Uzunkoy village, Izmir, Turkey, September 2016','Clevenger hydrodistillation 3 h','GC-FID/MS',notes='P. lentiscus var. chia; essential oil distilled from gum, not fixed pistachio oil. Single MGEO-1 sample; no inferred pure alpha-pinene enantiomer.')
for i,r in enumerate(table(p['pmcid'],p['table_id']),1):
 if len(r)==7 and r[0].isdigit():obs(p,r[2],r[3],i,r)
for part,col in [('Leaves',3),('Berries',4)]:
 p=profile('PMC10673065','molecules-28-07547-t001','Juniperus phoenicea','Juniper',part+' Boukornine Tunisia 2022',part,'Boukornine mountain, Ben Arous, Tunisia, May 2022','Clevenger hydrodistillation 3 h','GC-MS','Essential Oils','Reported relative % (w/w)',notes='Paper captions w/w; not relabelled as mass-calibrated GC peak area. No GC-weighted oil index without established quantitation basis.',rankable=False)
 for i,r in enumerate(table(p['pmcid'],p['table_id']),1):
  if len(r)==5 and r[1].isdigit():obs(p,r[0],r[col],i,r)
p=profile('PMC13144440','Tab1','Cedrus atlantica','Cedar','Modern Azrou cedar tar reference','Dry-distilled wood tar','Les Arômes de Ben Sim, Azrou, Morocco, October 2009','Traditional per ascensum dry distillation; DCM dissolution','GC-MS','Resins and Aromatic Preparations','Qualitative presence',notes='Modern reference material; not ancient species proof or steam-distilled essential oil. Putative annotation only; no invented abundance, all identities require review.')
for i,r in enumerate(table(p['pmcid'],p['table_id']),1):
 if len(r)==5 and r[0].startswith('#'):obs(p,r[2],1,i,r,eligible=False,annotation='Putative GC-MS annotation; qualitative presence')

# Supplement first-page subset: PDF retained and manually checked against page 12.
mp=[('16:0-Campesterol',.02),('22:1-Stigmasterol',.04),('22:2-Sitosterol',.04),('22:0-Campesterol',.04),('20:1-Stigmasterol',.05),('20:2-Sitosterol',.05),('MG 20:4',.05),('20:0-Sitosterol',.06),('18:3-Stigmasterol',.06),('MG 18:1',.06),('22:0-Stigmasterol',.06),('22:1-Sitosterol',.06),('1,3DG 38:4',.07),('16:3-Stigmasterol',.07),('18:0-Stigmasterol',.08),('18:1-Sitosterol',.08),('20:0-Stigmasterol',.08),('20:1-Sitosterol',.08),('TG 60:3',.47),('TG 60:2',.48),('TG 52:5',.48),('TG 60:6',.48),('1,3DG 35:5',.49),('1,3DG 36:0',.49),('20:2-Campesterol',.49),('PE 36:2',.49),('PE 34:2',.5),('TG 60:5',.5),('PC 36:3',.51),('PC 33:2',.52),('PE 36:1',.52),('18:2-Sitosterol',.54),('18:1-Stigmasterol',.54),('20:3-Stigmasterol',.55),('1,2DG 32:3',.56),('1,2DG 35:4',.56)]
pdf=ROOT/'PMC6571088_216_2019_1850_MOESM1_ESM.pdf';sha=hashlib.sha256(pdf.read_bytes()).hexdigest()
(ROOT/'PMC6571088_s3_transcription.json').write_text(json.dumps({'source':pdf.name,'sha256':sha,'page':12,'table':'S3','scope':'First 18 rows of each column block; partial lipid annotation subset','rows':[{'name':n,'MP':1,'MO':v} for n,v in mp],'uncertainty':'Published SDs remain in source PDF; not transcribed into this mean-only subset.'},indent=2),encoding='utf-8')
for sp,common,origin,col in [('Moringa peregrina','Moringa peregrina','Al Dhakhlia, Oman, June 2017',0),('Moringa oleifera','Moringa oleifera','Limpopo, South Africa, September 2017',1)]:
 p=profile('PMC6571088','Supplement_S3',sp,common,'Seed lipid annotations relative to M. peregrina','Seeds',origin,'80 MPa carbon dioxide with ethanol extraction','UHPSFC/QTOF-MS','Fixed Oils','Analyte area ratio to M. peregrina',notes='Partial first-page S3 subset (36 annotations); each analyte separately normalized to MP=1. Not percent composition. Sum lipid labels do not define acyl positions/unique molecular structures. All excluded from docking. PDF SHA256 '+sha)
 for i,(name,v) in enumerate(mp,1):obs(p,name,1 if col==0 else v,i,[name,1,v,'Supplement S3 page 12'],eligible=False,annotation='Sum-composition lipid annotation, unresolved molecular species')
p=profile('PMC11011647','Supplement_S2','Balanites aegyptiaca','Desert Date','Mo1 Tata kernel oil 2020 fatty-acid pool','Kernels','Tata, Morocco, 2020','Cold pressing; fatty-acid derivatization','GC-FID','Fixed Oils','Fatty-acid %',notes='Mo1 sample only, not the roasted Mauritanian oil or Egyptian collection. PDF supplementary Table S2. No native free-acid inference.')
vals=[('Myristic acid',.1,0),('Palmitic acid',14.5,.5),('Palmitoleic acid',.1,0),('Heptadecanoic acid',.1,0),('Stearic acid',11.1,.2),('Oleic acid',23.4,.1),('Vaccenic acid',.8,0),('Linoleic acid',48.5,.3),('α-Linolenic acid',.7,0),('Arachidic acid',.4,0),('Gondoic acid',.2,0),('Behenic acid',.1,0),('Lignoceric acid',.1,0)]
pdf=ROOT/'PMC11011647_foods-2945624-supplementary.pdf';sha=hashlib.sha256(pdf.read_bytes()).hexdigest();p['notes']+=' PDF SHA256 '+sha
for i,(n,v,sd) in enumerate(vals,1):obs(p,n,f'{v} ± {sd}',i,[n,v,sd,'Mo1; Supplement S2'],eligible=False)
(ROOT/'PMC11011647_s2_transcription.json').write_text(json.dumps({'source':pdf.name,'sha256':sha,'table':'S2','sample':'Mo1','rows':vals},indent=2),encoding='utf-8')
p=profile('PMC10359763','tab2','Balanites aegyptiaca','Desert Date','Wadi El Gemal Egyptian seed NMR extract','Seeds','Wadi El Gemal National Park, Marsa Alam, Egypt, January 2022','Methanolic seed extraction','Quantitative 1H-NMR','Botanical Extracts','µg/mg dry powder',notes='BS column only. NMR class pools such as omega-3/omega-6 fatty acids and aggregate sugars are not individual compounds and are excluded.')
for i,r in enumerate(table(p['pmcid'],p['table_id']),1):
 if len(r)==7 and r[0] not in ['Metabolite','ω-3 fatty acid','ω-6 fatty acid','Sucrose + glucose','Glucose + fructose'] and not any(x in r[0].lower() for x in ['total','fatty acid']):obs(p,r[0],r[5],i,r)

manifest={'format':1,'retrieved_at':'2026-10-29','references':references,'profiles':profiles,'exclusions':['PMC8909160 uses Csp inconsistently for C. sinensis var. pubilimba and C. ptilophylla; excluded from the Camellia sinensis library.','PMC11649686 contains questionable exotic library assignments in Egyptian Moringa seed extracts; not promoted to validated compounds.','No percentages generated for qualitative markers. No totals, pooled classes, unknown peaks or biodiesel products counted as botanical molecules.']}
(ROOT/'comprehensive_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(len(profiles),'profiles;',sum(len(p['observations']) for p in profiles),'observations;',len(references),'references')
