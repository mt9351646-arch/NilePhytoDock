"""English case report and software summary from executed evidence only."""
import json,csv,sqlite3,textwrap
from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
ROOT=Path('.');OUT=ROOT/'docs';CASE=ROOT/'data/validation/case_study_final'
def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
r=load(CASE/'validation.json');a=load(CASE/'analysis/molecular_analysis.json');fig=CASE/'publication_figures';fig.mkdir(exist_ok=True)
def book(title,intro):
 d=Document();s=d.sections[0];s.page_width=Inches(8.5);s.page_height=Inches(11);s.left_margin=s.right_margin=Inches(.8);s.top_margin=Inches(.65);s.bottom_margin=Inches(.65)
 for name,size in [('Normal',10.5),('Title',23),('Heading 1',15),('Heading 2',12)]:d.styles[name].font.name='Arial';d.styles[name].font.size=Pt(size);d.styles[name].font.color.rgb=RGBColor(0,0,0)
 d.styles['Normal'].paragraph_format.space_after=Pt(7);d.styles['Normal'].paragraph_format.line_spacing=1.08
 d.core_properties.author='Ahmed G Soliman and Malak Taha';d.core_properties.title=title;d.core_properties.last_modified_by='NilePhytoDock 0.6.0'
 s.header.paragraphs[0].text='NilePhytoDock 0.6.0 | Ahmed G Soliman and Malak Taha'
 f=s.footer.paragraphs[0];f.alignment=WD_ALIGN_PARAGRAPH.CENTER;f.add_run('NilePhytoDock | ');field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');f._p.append(field)
 d.add_paragraph(title,'Title');d.add_paragraph(intro);return d
def p(d,text):return d.add_paragraph(text)
def h(d,text):d.add_heading(text,1)
def page(d):d.add_page_break()
def table(d,headers,records,widths=None):
 t=d.add_table(rows=1,cols=len(headers));t.style='Light Shading Accent 1'
 for cell,text in zip(t.rows[0].cells,headers):cell.text=text
 repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
 for row in records:
  for cell,value in zip(t.add_row().cells,row):cell.text=str(value)
 if widths:
  t.autofit=False
  for row in t.rows:
   for cell,w in zip(row.cells,widths):cell.width=Inches(w)
 borders=OxmlElement('w:tblBorders')
 for side in ['top','left','bottom','right','insideH','insideV']:
  b=OxmlElement('w:'+side);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
 t._tbl.tblPr.append(borders)
 for row in t.rows:
  for cell in row.cells:
   cb=OxmlElement('w:tcBorders')
   for side in ['top','left','bottom','right']:
    edge=OxmlElement('w:'+side);edge.set(qn('w:val'),'single');edge.set(qn('w:sz'),'4');edge.set(qn('w:color'),'D9D9D9');cb.append(edge)
   cell._tc.get_or_add_tcPr().append(cb)
   for paragraph in cell.paragraphs:
    paragraph.paragraph_format.space_after=Pt(4);paragraph.paragraph_format.space_before=Pt(4)
    for run in paragraph.runs:run.font.size=Pt(9)
 return t
def picture(d,path,caption,width=6.65):
 par=d.add_paragraph();par.add_run().add_picture(str(path),width=Inches(width));par.paragraph_format.keep_with_next=True
 cap=p(d,caption)
 for run in cap.runs:run.font.size=Pt(9)
def save(d,path):
 for e in list(d._element.iter(qn('w:pBdr'))):e.getparent().remove(e)
 for style in d.styles:
  for e in list(style._element.iter(qn('w:pBdr'))):e.getparent().remove(e)
 d.save(path)

def figures():
 import matplotlib
 matplotlib.use('Agg')
 from matplotlib import pyplot as plt
 import numpy as np
 ligands=sorted(a['site_cohorts'][0]['ligands'],key=lambda x:x['score'])[:10]
 f,ax=plt.subplots(figsize=(8.3,4.3));ax.barh([v['compound'] for v in ligands][::-1],[v['score'] for v in ligands][::-1],color='#147d86');ax.set_xlabel('Smina Vina score (kcal/mol)');ax.set_title('Best saved poses for ten unique structures');f.tight_layout();f.savefig(fig/'case_top_scores.png',dpi=300);plt.close(f)
 values={}
 for v in a['presence_vs_participation']:
  counts=values.setdefault(v['group'],[0,0]);counts[0]+=1;counts[1]+=int(v['directly_participating'])
 labels=list(values);y=np.arange(len(labels));f,ax=plt.subplots(figsize=(8.3,4.3));ax.barh(y+.18,[values[v][0] for v in labels],height=.35,color='#b7c5d4',label='Present');ax.barh(y-.18,[values[v][1] for v in labels],height=.35,color='#147d86',label='Directly participating');ax.set_yticks(y,labels);ax.set_xlabel('Distinct chemical identities at the selected site');ax.legend(loc='lower right');f.tight_layout();f.savefig(fig/'case_groups.png',dpi=300);plt.close(f)
 for name,m in [('case_structural_similarity',a['chemical_similarity']),('case_interaction_similarity',a['site_cohorts'][0]['interaction_similarity'])]:
  f,ax=plt.subplots(figsize=(7,6));im=ax.imshow(np.array(m['matrix'],float),vmin=0,vmax=1,cmap='viridis');n=len(m['labels']);ax.set_xticks(range(n),range(1,n+1),fontsize=7);ax.set_yticks(range(n),range(1,n+1),fontsize=7);ax.set_xlabel('Chemical identity number');ax.set_ylabel('Chemical identity number');f.colorbar(im,ax=ax,label='Tanimoto' if 'structural' in name else 'Jaccard');f.tight_layout();f.savefig(fig/(name+'.png'),dpi=300);plt.close(f)
 with (fig/'matrix_identity_legend.csv').open('w',encoding='utf-8-sig',newline='') as stream:
  w=csv.writer(stream);w.writerow(['Number','Compound','InChIKey']);w.writerows([[i+1,label,identity] for i,(label,identity) in enumerate(zip(a['chemical_similarity']['labels'],a['chemical_similarity']['identities']))])

def case_report():
 d=book('NilePhytoDock Case Study','Reproducible botanical constituent screening and reference redocking against bovine beta trypsin 3PTB. This report documents actual local calculations, their analytical provenance and their limits. Developers are Ahmed G Soliman and Malak Taha.')
 h(d,'1 Abstract');p(d,f"Five source profiles were selected; four contributed approved native constituents. The resulting 23 compound-name jobs represent 20 unique structures and produced {r['saved_poses']} saved poses. The fifth profile, anise, had no approved native structure after source review. All {r['all_contacts_independently_verified']} saved contact events passed independent coordinate verification. Charged benzamidine redocking gave a top-pose RMSD of 0.390 Å in the experimental box and 0.389 Å in the P2Rank box, without post-alignment. All source-profile coverage values remain below 70%; these results are workflow validation and computational priorities, not evidence of oil efficacy.")
 h(d,'2 Scientific question');p(d,'Can one traceable desktop workflow transfer a predicted binding site into native docking, recover a known ligand pose and produce inspectable constituent contacts, group participation, structural similarity and coverage-qualified profile priorities? The study does not test clinical efficacy, mixture synergy or target selectivity.')
 h(d,'3 Experimental reference and protein selection');p(d,'RCSB entry 3PTB is bovine beta-trypsin from Bos taurus, determined by X-ray diffraction at 1.70 Å, with bound benzamidine BEN A:1. Benzamidine is therefore an appropriate pose-recovery control. A separate experimental study reports bovine trypsin inhibition Ki = 33 µM (PMC17520). That measurement is an external comparator, not a calibration of the Smina score. No matched experimental activities or decoy set were available for the botanical constituents, so no correlation, AUROC or enrichment factor for activity prediction was calculated.')
 p(d,'Sources: https://www.rcsb.org/structure/3PTB and https://pmc.ncbi.nlm.nih.gov/articles/PMC17520/')
 page(d);h(d,'4 Source profiles and inclusion')
 db=sqlite3.connect(CASE/'case_study.sqlite');db.row_factory=sqlite3.Row;names={v['id']:v['name'] for v in r['profiles']};ranking=list(r['ranking'].values())[0]
 cells=[]
 for v in ranking:
  name=names[v['profile_id']];species=name.split(' — ')[0];cells.append([species,f"{v['screened_peak_area_percent']:.2f}",'Unavailable' if v['index'] is None else f"{v['index']:.4f}", 'No approved native structure' if v['index'] is None else 'Coverage below 70%'])
 table(d,['Botanical profile','Screened GC area %','Priority index','Interpretation'],cells,[2.25,1.15,1.0,2.2])
 p(d,'Thyme (Giza 2018), basil (Tanta 2018), anise and coriander (ARC Cairo 2019) have documented Egyptian study samples. Cumin was purchased in an Egyptian market; its growing origin is unverified. Each sample remains distinct. Major stereochemically unresolved constituents are excluded, rather than assigned an invented configuration. An analytical trimethylsilyl derivative and highly flexible long-chain structures were withheld during QC; their original records, candidate files and initial raw calculations remain archived.')
 p(d,'Analytical sources: PMC9605189, PMC9578474, PMC9570728 and PMC9023561. Complete source rows, units and profile memberships accompany the data. The very low coriander coverage and absent anise coverage prevent whole-oil interpretation.')
 h(d,'5 Receptor and ligand preparation');p(d,'The original receptor was copied unchanged. BEN A:1 and waters were removed for this protocol; the calcium cofactor was retained. The receptor chemistry graph, atom labels and general pH 7.4 protonation approximation were recorded. No missing loops or side chains were rebuilt. Approved library ligands used exact normalized PubChem synonym checks, explicit stereochemical gates, ETKDGv3 seed 20261029 and converged MMFF94s or UFF minimization. The software does not enumerate pH-dependent ligand ensembles. Neutral benzamidine and a separately explicit +1 amidinium control were both prepared so the reference valence state is visible.')
 h(d,'6 Pocket localization');p(d,f"P2Rank 2.5.1 on the prepared receptor placed the top pocket center {r['p2rank_pocket_center_to_crystal_ligand_centroid_A']:.3f} Å from the crystal benzamidine heavy-atom centroid. All {r['crystal_heavy_atom_count']} crystal heavy atoms lie inside the predicted box. The center was [−1.5173, 14.4714, 17.4739] Å and dimensions [29.737, 23.963, 29.950] Å. Every actual Smina command was checked against the saved pocket. A correctly localized box alone does not validate the scoring function.")
 page(d);h(d,'7 Docking settings and reference redocking');p(d,'Constituent screening used native Smina 2020.12.10, Vina scoring, exhaustiveness 8, three modes, seed 20261029 and two CPU threads. Reference controls used exhaustiveness 16 and five modes. The final study transparently reused hash-verified raw outputs from the preceding QC executions where the receptor, ligand, engine and protocol matched; elapsed zero identifies reuse. P2Rank and all four reference controls executed locally. No docking value was taken from literature or generated as a demonstration.')
 table(d,['Control','Charge','Top score kcal/mol','Top RMSD Å'],[[b['box'].replace('_',' '),b['formal_charge'],f"{b['poses'][0]['score_kcal_mol']:.5f}",f"{b['poses'][0]['symmetry_corrected_no_alignment_rmsd_A']:.6f}"] for b in r['benchmark']],[3.0,.65,1.4,1.4])
 p(d,f"RMSD uses RDKit graph-symmetry mapping of heavy atoms in the original receptor coordinate frame. No rotation or translation is fitted after docking. Repeating the charged reference protocol produced a maximum coordinate difference of {r['reference_repeat_max_coordinate_difference_A']:.1f} Å over corresponding saved poses. Pose recovery on this one system is not broad validation of ligand ranking.")
 h(d,'8 Botanical constituent screening results');p(d,'The best saved score for each InChIKey is retained for chemical comparisons; aliases do not increase the similarity population. Twenty distinct structures span terpenes, aromatic phenols, ethers, an ester, aldehydes and long-chain hydrocarbons within the accepted scope. Lower energies are favored only within this target and protocol. All profile priorities require strong coverage qualifications; the selected anise profile correctly receives no index.')
 picture(d,fig/'case_top_scores.png','Figure 1  Actual best-pose energies for ten unique structures. These are Smina scores, not measured affinities.')
 page(d);h(d,'9 Molecular interaction analysis');p(d,f"ProLIF 2.2.3 and RDKit chemically classified the saved poses. All {r['interaction_events']} raw events from 69 poses were independently checked against receptor and ligand atoms; the largest distance residual was {r['maximum_contact_distance_residual_A']:.2g} Å. Hydrogen-bond distances use donor/acceptor heavy atoms, with donor-H-acceptor angles. Aromatic contacts use ring features; ionic calls use formal charge. Conservative metal classification requires a complete supported Zn/Mg geometry; merely being near calcium is not labelled a validated coordination bond.")
 picture(d,fig/'Thymol_Circular.png','Figure 2  Circular map of the actual best saved thymol pose. Links are schematic and labels are measured 3D distances; all source contacts remain in the exported table.',6.1)
 page(d);d.add_heading('Binding pose detail',2);picture(d,fig/'3d/Publication_Quality.png','Figure 3  Actual thymol pose in its prepared 3PTB receptor. Protein context uses blue lines and binding-residue sticks; ligand carbon is teal and displayed hydrogen-bond links are blue. Labels identify actual residues; the complete contact table includes all categories.',6.6)
 page(d);h(d,'10 Functional group contributions');p(d,'Versioned atom-centred SMARTS assigns specific conventional groups before generic ones: ester does not also become ether, amide nitrogen does not become amine, and phenolic hydroxyl is distinct from alcohol. Source atom indices link each group to its saved pose. A group must contain an actual contact atom or a qualifying ring feature to be counted as directly participating. Aromatic, alkene and hydrophobic features are overlapping molecular-feature domains and cannot be added as independent conventional groups.')
 picture(d,fig/'case_groups.png','Figure 4  Presence versus direct participation among the 20 best identity/site poses. Group participation is a predicted association, not a causal contribution to affinity.')
 p(d,f"There are {len(a['functional_group_interactions'])} group/category/site summary associations. Complete tables separately count raw events, distinct InChIKeys and ligand-residue pairs, and retain target, pocket, residue, atom indices, distance, angle and method. These definitions prevent repeated contacts or aliases from inflating the apparent evidence.")
 h(d,'11 Molecular and interaction similarity');p(d,f"Morgan radius-2 fingerprints use 2048 bits and chirality; Tanimoto similarity is independent of docking energy. The 20 structures formed {a['chemical_similarity']['cluster_count']} Butina clusters at similarity 0.65, including {a['chemical_similarity']['singleton_clusters']} singleton clusters; mean pairwise similarity was {a['chemical_similarity']['mean_pairwise_similarity']:.4f}. Interaction fingerprints encode chain, residue number, insertion code and category. Jaccard comparisons are confined to this one prepared receptor and pocket; empty-empty fingerprints are unavailable.")
 page(d);picture(d,fig/'case_structural_similarity.png','Figure 5  Complete structural similarity matrix. Axis numbers map to compound names and InChIKeys in matrix_identity_legend.csv. Diagonal values are 1.',6.05)
 picture(d,fig/'case_interaction_similarity.png','Figure 6  Compatible-site interaction fingerprint similarity in the same identity order. A similar contact fingerprint does not establish the same mechanism.',6.05)
 page(d);h(d,'12 Statistics and validation');e=a['site_cohorts'][0]['enrichment'];p(d,e['reason']);p(d,'The analysis prunes repeated structural clusters and nonempty Murcko scaffolds before any exploratory group test. Acyclic molecules use fingerprint clusters. Top and bottom energy quartiles include ties; overlapping cutoffs suppress inference. Two-sided Fisher tests receive Benjamini-Hochberg correction across tested groups. No significant or causal effect is asserted from this small single-target dataset.')
 if e['rows']:table(d,['Feature','High present / total','Low present / total','Fisher p','BH q'],[[v['functional_group'],f"{v['high_present']}/{v['high_total']}",f"{v['low_present']}/{v['low_total']}",f"{v['p_value']:.4f}",f"{v['bh_q_value']:.4f}"] for v in e['rows']],[2.3,1.15,1.15,1.0,1.0])
 p(d,'Software validation also includes 56 passing automated tests; 222 independently checked contacts in six saved poses across two targets; three 2D styles and seven residue color modes; native WebGL model/opacity/background tests for three appearance presets; all sixteen scientific charts with real tooltips and Qt selection events; and six CSV/XLSX/DOCX interaction export modes with full numeric precision. The separate validation report records frozen-EXE checks and display-scale evidence.')
 h(d,'13 Limitations');p(d,r['limitations']);p(d,'Coverage is incomplete for every selected oil profile, often because primary source names do not establish stereochemistry. This is a material limitation, not a missing value to be imputed. Oil indices depend on the screened population and do not model whole-oil binding. A single successful redocking control and exact seeded repeat do not establish prospective screening performance. Windows 10 and a clean virtual machine are untested; the Windows executable is unsigned.')
 h(d,'14 Reproducibility and sources');p(d,'The companion evidence contains case_study.sqlite, validation.json, original and prepared receptors, source profiles, P2Rank outputs, exact process commands, raw Smina logs and poses, complex files, contact records, complete CSV/XLSX tables, analysis JSON, both similarity matrices and source-index legends. Repeat analysis produces the same saved-data signature. Retain the whole directory when relocating the study.')
 p(d,'Reproduction commands: python -m tools.run_final_case_study followed by python -m tools.finalize_case_analysis. Use a fresh destination; the initial-QC cache policy is explicit in the script. Standard standalone reproduction can use tools.run_case_study with current source eligibility. Do not overwrite an existing study folder.')
 for pmc in ['PMC9605189','PMC9578474','PMC9570728','PMC9023561','PMC17520']:p(d,'https://pmc.ncbi.nlm.nih.gov/articles/'+pmc+'/')
 save(d,OUT/'NilePhytoDock_Case_Study.docx');db.close()

def summary():
 d=book('NilePhytoDock Complete Software Summary','This document describes the implemented Windows desktop application, the verified scientific workflow, the delivered source and documentation, and the limits of the current validation. Developers are Ahmed G Soliman and Malak Taha.')
 h(d,'Application and workflow');p(d,'NilePhytoDock 0.6.0 connects source-qualified botanical chemistry with protein inspection, explicit receptor preparation, P2Rank pockets, native Smina docking, geometry-verified interactions and composition-informed priorities. The application is English with left-to-right layout; its user and development guides are external English documents. The supplied emblem is used by the splash, window, executable and seven-resolution Windows ICO. Existing research databases and prior releases are preserved.')
 table(d,['Area','Implemented behavior'],[['Library','119 separate source profiles; preparation and historical evidence filters'],['Screening','PDB/mmCIF import, per-target pockets and exact box transfer, protocol controls, pause/cancel and saved projects'],['Interactions','ProLIF/RDKit typing, atom/feature geometry checks, archived reanalysis and explicit review states'],['Visualization','Classic, Circular and Functional group 2D; independent residue fills; custom line colors; three real 3D presets'],['Analysis','SMARTS participation, independent chemical and compatible-site fingerprints, clusters and exploratory statistics'],['Export','Six interaction modes; CSV/XLSX/DOCX; sixteen charts with PNG/SVG/PDF/CSV/XLSX; reproducibility reports']],[1.15,5.55])
 page(d);h(d,'Database and source evidence');p(d,'The seed has 57 distinct botanical oils: 46 essential and 11 fixed oils. Across 68 botanical taxa it retains 819 normalized compound-name records and 2109 source observations. There are 186 ready name records representing 164 distinct InChIKeys; 633 names remain outside the ready set. A source peak, an alias and a unique chemical structure are different counts. The seed contains no research projects or demonstration results.')
 p(d,'Three reviewed literature packs contain 90 profiles and 1448 observations from 37 primary PMC papers, in addition to the original 661 source observations. The latest pack adds anise, coriander, chamomile, garlic, oregano, Damask rose, camphor-tree/Ravintsara and cardamom references; sweet almond, pistachio, castor, sesame, safflower, flax, Balanites and both Moringa species; tea and coffee extracts, a pomegranate fraction, myrrh, frankincense, mastic, juniper and cedar tar. Existing thyme and previously requested Egyptian/Mediterranean botanicals are retained. Countries and market-origin uncertainty are explicit; non-Egyptian reference samples are not relabelled as Egyptian.')
 p(d,'The five preparation categories distinguish essential oils, fixed oils, botanical extracts, resins/aromatic preparations and individual natural compounds. Historical metadata evaluates twelve candidates separately, with source, period, evidence type, confidence and taxonomic uncertainty. Safflower dye and flax linen demonstrate botanical uses, not evidence for those seed oils in a sacred recipe. Modern cedar/juniper species are not inferred from genus-level ancient residues.')
 p(d,'Fixed fatty-acid pools, unresolved sum lipids, analytical TMS derivatives and source-suspect annotations are excluded where they do not establish native individual molecules. Molecular scope limits are 900 Da, 80 heavy atoms and 25 rotatable bonds. Original values, units, raw rows, candidate files and previous raw calculations survive these review decisions. All 1613 observations present before this upgrade were checked unchanged in their original scientific fields.')
 page(d);h(d,'Scientific methods');p(d,'RDKit performs structure checks, ETKDGv3 embedding, converged minimization and molecular descriptors. PubChem CID formulas agree with all 186 ready records. Receptor preparation uses an explicit chemistry graph and general protonation approximation, without loop/side-chain rebuilding. P2Rank 2.5.1 and Smina 2020.12.10 run locally through recorded commands and hash-based cache checks. ProLIF 2.2.3 supplies chemical contact typing; PLIP is not used.')
 p(d,'Functional centres use versioned SMARTS with specificity precedence and saved atom indices. Presence and directly participating atoms are separate results. Chemical similarity is chirality-aware Morgan/Tanimoto with Butina clustering; contact similarity uses same-receptor/site residue-category Jaccard. Empty fingerprints, small cohorts and missing results remain explicit. Exploratory Fisher/BH statistics prune repeated clusters and Murcko scaffolds. No activity or causal contribution is inferred from a predicted group contact.')
 p(d,'Within-target best energies are converted to percentiles over unique InChIKeys. An oil index weights these by original successfully screened GC peak area. Duplicate identities can suppress a source index; incomplete coverage is reported. HPLC concentrations, headspace, fixed fatty-acid pools and qualitative annotations receive no GC-weighted oil index. Multi-target results do not silently drop a missing positive-weight target.')
 h(d,'Executed validation');p(d,'The automated suite passes 56 tests. Geometry QA checks 222 contacts in six real poses across two proteins, rejects corrupted coordinates/distances and exercises three 2D styles, seven residue color modes, nine protein representations and three actual appearance presets. Sixteen charts render offline with numeric checks, tooltip execution, Qt selection callbacks and static/tabular exports. Six interaction export modes preserve complete numeric values; unsupported empty exports fail visibly.')
 p(d,'The case study retains 23 real compound-name calculations, 20 unique structures, 69 poses and 1917 verified contact events. P2Rank center error is 0.608 Å and its box contains all nine crystal ligand heavy atoms. Charged reference redocking reaches 0.390 Å RMSD in the crystal box and 0.389 Å in the predicted box without post-alignment; a repeated charged run produces identical saved coordinates. All selected profile coverages remain below 70%, and anise has no approved native constituent. No matched botanical activity dataset was available for AUROC or affinity correlation.')
 page(d);h(d,'Build distribution and documentation');p(d,'The native PySide6 application is packaged with PyInstaller for 64-bit Windows. Java, P2Rank, Smina and the scientific libraries are included in the portable distribution with notices and native asset hashes. Keep _internal beside NilePhytoDock.exe. Documentation is delivered in Documentation beside the executable. A private data-directory installation check performs actual P2Rank/Smina HPLC screening, verifies reports, native atom mapping, offline charts and English UI. The final validation report records the tested executable and its SHA-256.')
 p(d,'Deliverables include the portable Windows ZIP, a source ZIP, README, USER_GUIDE, INSTALLATION, SCIENTIFIC_METHODOLOGY, DATABASE_GUIDE, DEVELOPER_GUIDE, VALIDATION_REPORT, CHANGELOG, NEXT_CODEX_PROMPT, the English user and methods manuals, this summary and the full scientific case study. The release is under X:/nile/release. The private repository is https://github.com/ahmedGSoliman99/NilePhytoDock and versioned release is https://github.com/ahmedGSoliman99/NilePhytoDock/releases/tag/v0.6.0; private access is required.')
 h(d,'Limits and future validation');p(d,'Scores are predictions, not measured affinity, efficacy or safety. Relative GC peak area is not an absolute mass fraction. Coverage and stereochemical uncertainties materially limit source interpretation; mixture synergy, exposure and pharmacology are not modelled. The current preparation does not calculate site-specific pKa, enumerate ligand protonation ensembles or rebuild missing receptor atoms. Optional PyMOL sessions require an installed legitimate PyMOL. The executable is unsigned. Windows 10, a clean VM and every GPU/display configuration are untested. Broader prospective benchmarks and curated identity resolution remain future scientific work; they are not claimed as completed features.')
 save(d,OUT/'NilePhytoDock_Complete_Software_Summary.docx')
 # A prose Markdown companion, including all document paragraphs and table rows.
 lines=[]
 for paragraph in d.paragraphs:
  if paragraph.text:lines.append(('# ' if paragraph.style.name=='Title' else '## ' if paragraph.style.name.startswith('Heading') else '')+paragraph.text)
 for t in d.tables:
  for row in t.rows:lines.append(' | '.join(c.text for c in row.cells))
 (OUT/'NilePhytoDock_Complete_Software_Summary.md').write_text('\n\n'.join(lines)+'\n',encoding='utf-8')
if __name__=='__main__':figures();case_report();summary();print('Case study and complete software summary authored from executed evidence')
