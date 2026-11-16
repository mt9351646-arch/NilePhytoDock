import numpy as np
from scipy.stats import rankdata
from database.store import rows

def percentile_scores(scores):
    """Best energy -> 1, worst -> 0; ties average; singleton -> 0.5."""
    if not scores:return {}
    ids=list(scores);values=[scores[k] for k in ids]
    if not np.isfinite(values).all():raise ValueError("Non-finite docking scores cannot be ranked")
    q=(len(ids)-rankdata(values,method="average"))/(len(ids)-1) if len(ids)>1 else [.5]
    return dict(zip(ids,map(float,q)))

def oil_indices(composition,scores):
    identities={r['compound_id']:r.get('chemical_identity',r['compound_id']) for records in composition.values() for r in records}
    eligible={r['compound_id'] for records in composition.values() for r in records if r.get('docking_eligible',1)}
    unique_scores={}
    for cid,score in scores.items():
        if cid not in eligible:continue
        identity=identities.get(cid,cid);unique_scores[identity]=min(score,unique_scores.get(identity,score))
    unique_q=percentile_scores(unique_scores);q={cid:unique_q[identities.get(cid,cid)] for cid in scores if cid in eligible};out=[]
    for profile,records in composition.items():
        if records and not all(r.get('ranking_eligible',1) for r in records):
            out.append({'profile_id':profile,'best_constituent_score':min((scores[r['compound_id']] for r in records if r['compound_id'] in scores),default=None),'index':None,'screened_peak_area_percent':None,'reported_peak_area_percent':None,'fraction_of_reported':None,'sensitivity_min':None,'sensitivity_max':None,'warning':'No oil index: this profile uses headspace, extract concentration, qualitative annotation, or a fatty-acid pool rather than essential-oil GC peak-area composition.'})
            continue
        # Duplicate compound/profile entries are not silently double-weighted.
        seen=set();duplicates=set()
        for r in records:
            identity=r.get('chemical_identity',r['compound_id'])
            if identity in seen:duplicates.add(identity)
            seen.add(identity)
        if duplicates:
            out.append({'profile_id':profile,'best_constituent_score':min((scores[r['compound_id']] for r in records if r['compound_id'] in scores and r.get('docking_eligible',1)),default=None),'index':None,'screened_peak_area_percent':None,'reported_peak_area_percent':None,'fraction_of_reported':None,'sensitivity_min':None,'sensitivity_max':None,'warning':'Source review required: duplicate compound entries in this profile; no oil index calculated. Chemical identities: '+', '.join(map(str,sorted(duplicates,key=str)))})
            continue
        weights=[(r["compound_id"],r["percentage"]) for r in records if r["percentage"] is not None and r["percentage"]>0]
        successful=[(r['compound_id'],r['percentage']) for r in records if r['percentage'] is not None and r['percentage']>0 and r['compound_id'] in q and r.get('docking_eligible',1)]
        covered=sum(w for _,w in successful);reported=sum(w for _,w in weights)
        best=min((scores[r["compound_id"]] for r in records if r["compound_id"] in scores and r.get('docking_eligible',1)),default=None)
        index=sum(w*q[c] for c,w in successful)/covered if covered else None
        # Deterministic one-at-a-time ±10% relative abundance sensitivity.
        sens=[]
        if covered:
            for j in range(len(successful)):
                for factor in [.9,1.1]:
                    w2=[(c,w*(factor if i==j else 1)) for i,(c,w) in enumerate(successful)]
                    sens.append(sum(w*q[c] for c,w in w2)/sum(w for _,w in w2))
        out.append({"profile_id":profile,"best_constituent_score":best,"index":index,"screened_peak_area_percent":covered,"reported_peak_area_percent":reported,"fraction_of_reported":covered/reported if reported else None,"sensitivity_min":min(sens,default=index),"sensitivity_max":max(sens,default=index),"warning":"Insufficient coverage (<70% of original peak area)" if covered<70 else ""})
    out=sorted(out,key=lambda r:r["index"] if r["index"] is not None else -1,reverse=True)
    for r in out:
        others=[o['index'] for o in out if o is not r and o['index'] is not None]
        r['sensitivity_rank_best']=1+sum(v>r['sensitivity_max'] for v in others) if r['index'] is not None else None
        r['sensitivity_rank_worst']=1+sum(v>r['sensitivity_min'] for v in others) if r['index'] is not None else None
    return out

def project_rankings(db,project):
    settings=__import__('json').loads(db.execute("SELECT settings FROM analysis_projects WHERE id=?",(project,)).fetchone()[0])
    selected=settings.get("profiles",[])
    composition={p:[r for r in rows(db,"SELECT pc.compound_id,pc.percentage,p.ranking_eligible,CASE WHEN pc.docking_eligible=1 AND s.status='ready' THEN 1 ELSE 0 END AS docking_eligible,COALESCE(NULLIF(s.inchikey,''),'compound:'||pc.compound_id) AS chemical_identity FROM profile_compounds pc JOIN oil_profiles p ON p.id=pc.profile_id LEFT JOIN compound_structures s ON s.compound_id=pc.compound_id WHERE pc.profile_id=?",(p,))] for p in selected}
    out={}
    for protein in rows(db,"SELECT * FROM protein_targets WHERE project_id=?",(project,)):
        scores={r["compound_id"]:r["score"] for r in rows(db,"SELECT r.compound_id,min(p.score) AS score FROM docking_runs r JOIN docking_poses p ON p.run_id=r.id WHERE r.project_id=? AND r.protein_id=? AND r.status IN ('complete','interaction_review','figure_review') GROUP BY r.compound_id",(project,protein["id"]))}
        out[protein["id"]]=oil_indices(composition,scores)
    return out

def multi_target(target_results,weights):
    if not weights or any(v<0 or not np.isfinite(v) for v in weights.values()) or sum(weights.values())<=0:raise ValueError("Target weights must be finite, nonnegative and sum to >0")
    profiles={r['profile_id'] for rs in target_results.values() for r in rs};out=[]
    for profile in profiles:
        values={t:next((r['index'] for r in rs if r['profile_id']==profile),None) for t,rs in target_results.items()}
        missing=[t for t,w in weights.items() if w>0 and values.get(t) is None]
        out.append({'profile_id':profile,'combined_index':None if missing else sum(weights[t]*values[t] for t in weights if weights[t]>0)/sum(weights.values()),'missing_targets':missing})
    return sorted(out,key=lambda r:r['combined_index'] if r['combined_index'] is not None else -1,reverse=True)

