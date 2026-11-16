"""Separate structural and site-specific interaction similarity calculations."""
import math
from rdkit import Chem,DataStructs
from rdkit.Chem import rdFingerprintGenerator
from rdkit.ML.Cluster import Butina

def chemical(molecules,threshold=.65):
 generator=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048,includeChirality=True)
 fps=[generator.GetFingerprint(Chem.RemoveHs(m)) for m in molecules];matrix=[list(DataStructs.BulkTanimotoSimilarity(fp,fps)) for fp in fps]
 distances=[1-matrix[i][j] for i in range(len(fps)) for j in range(i)]
 clusters=Butina.ClusterData(distances,len(fps),1-threshold,isDistData=True,reordering=True) if fps else []
 assignments={index:k+1 for k,cluster in enumerate(clusters) for index in cluster}
 pairs=[matrix[i][j] for i in range(len(fps)) for j in range(i)]
 return {'matrix':matrix,'clusters':assignments,'method':'Morgan radius=2, 2048 bits, chirality enabled; Tanimoto; Butina similarity threshold '+str(threshold),'mean_pairwise_similarity':sum(pairs)/len(pairs) if pairs else None,'cluster_count':len(clusters),'singleton_clusters':sum(len(c)==1 for c in clusters)}

def interaction(fingerprints):
 # Caller supplies only one prepared receptor and selected pocket cohort.
 result=[]
 for a in fingerprints:
  row=[]
  for b in fingerprints:
   union=a|b;row.append(len(a&b)/len(union) if union else None)
  result.append(row)
 return {'matrix':result,'method':'Binary residue-chain-insertion/category fingerprints; Jaccard (Tanimoto). Both-empty fingerprints are unavailable, not similarity 1. Same prepared receptor and pocket only.'}

def enrichment(records,minimum=12):
 """Exploratory Fisher tests on deterministic cluster representatives; BH FDR."""
 from scipy.stats import fisher_exact
 representatives={};scaffolds=set()
 for r in sorted(records,key=lambda v:v['identity']):
  scaffold=r.get('scaffold','')
  if r['cluster'] in representatives or scaffold and scaffold in scaffolds:continue
  representatives[r['cluster']]=r
  if scaffold:scaffolds.add(scaffold)
 cohort=sorted(representatives.values(),key=lambda v:v['score']);n=len(cohort)
 if n<minimum:return {'available':False,'reason':f'At least {minimum} structural-cluster/scaffold representatives are required; available {n}.','raw_compounds':len(records),'cluster_representatives':n,'rows':[]}
 k=max(3,n//4);upper=cohort[k-1]['score'];lower=cohort[-k]['score']
 if upper>=lower:return {'available':False,'reason':'Score ties do not permit distinct high/low quartile cohorts.','rows':[]}
 high=[r for r in cohort if r['score']<=upper];low=[r for r in cohort if r['score']>=lower];out=[]
 for group in sorted({g for r in cohort for g in r['groups']}):
  a=sum(group in r['groups'] for r in high);b=len(high)-a;c=sum(group in r['groups'] for r in low);d=len(low)-c
  if a+c<2 or b+d<2:continue
  odds,p=fisher_exact([[a,b],[c,d]],alternative='two-sided')
  out.append({'functional_group':group,'high_present':a,'high_total':len(high),'low_present':c,'low_total':len(low),'fisher_odds_ratio':float(odds) if math.isfinite(odds) else str(odds),'p_value':float(p),'corrected_odds_ratio':(a+.5)*(d+.5)/((b+.5)*(c+.5))})
 ordered=sorted(out,key=lambda r:r['p_value']);prior=1.
 for i in range(len(ordered)-1,-1,-1):prior=min(prior,ordered[i]['p_value']*len(ordered)/(i+1));ordered[i]['bh_q_value']=prior
 return {'available':bool(out),'reason':'Two-sided Fisher exact, BH across tested groups; top/bottom score quartiles including ties; deterministic representatives selected lexicographically by InChIKey independently of score, with no repeated structural cluster or nonempty Murcko scaffold. Acyclic molecules use fingerprint clusters. Exploratory association, not causation.','raw_compounds':len(records),'cluster_representatives':n,'rows':ordered}
