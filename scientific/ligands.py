"""Offline ligand preparation and opt-in PubChem maintenance."""
import datetime
import json
import re
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote
import requests
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, Crippen, Lipinski
from database.import_documents import standardized
from database.store import rows
from scientific.molecules import write_sdf

def name_key(name):
    return re.sub(r"[^a-z0-9+\-]", "", standardized(unicodedata.normalize("NFKC",name)).lower())

def validate_geometric_identity(mol,name):
    """Do not silently pick an E/Z isomer for a generic analytical name."""
    potential=[s for s in Chem.FindPotentialStereo(mol) if s.type==Chem.StereoType.Bond_Double]
    if not potential:return
    if any(s.specified==Chem.StereoSpecified.Unspecified for s in potential):raise ValueError('Potential geometric stereochemistry is unspecified in the candidate; manual identity review required')
    explicit=bool(re.search(r'\btrans\b|\bcis\b|\([\dEZ, -]*[EZ][\dEZ, -]*\)',name,re.I))
    # These conventional names encode alkene geometry. Their source analytical
    # assignments remain tentative independently of the structure definition.
    defined={'alpha-humulene','humulene','nerol','geraniol','cis-geraniol','alpha-citral','beta-citral','geranial','isoneral','geranic acid','geranyl acetate','geranyl isovalerate','neryl acetate','oleyl acetate','methyl elaidate','linoleic acid','oleic acid','germacrene b','curcumin','demethoxycurcumin','bisdemethoxycurcumin'}
    if not explicit and standardized(name).strip().lower() not in defined:raise ValueError('Source name does not establish the candidate E/Z geometry; manual identity review required')

def validate_small_molecule(mol):
    if Descriptors.MolWt(mol)>900 or mol.GetNumHeavyAtoms()>80 or Lipinski.NumRotatableBonds(mol)>25:
        raise ValueError('Outside the standard small-molecule preparation scope (900 Da, 80 heavy atoms, 25 rotatable bonds); specialist protocol review required')

def prepare(smiles, folder, compound_id):
    mol=Chem.MolFromSmiles(smiles)
    if mol is None: raise ValueError("RDKit rejected the molecular structure")
    if len(Chem.GetMolFrags(mol))!=1: raise ValueError("Multicomponent structures require manual review")
    validate_small_molecule(mol)
    mol=Chem.AddHs(mol)
    params=AllChem.ETKDGv3();params.randomSeed=20261029
    if AllChem.EmbedMolecule(mol,params)!=0: raise ValueError("ETKDGv3 conformer generation failed")
    if AllChem.MMFFHasAllMoleculeParams(mol):
        ff="MMFF94s";code=AllChem.MMFFOptimizeMolecule(mol,mmffVariant=ff,maxIters=2000)
    elif AllChem.UFFHasAllMoleculeParams(mol):
        ff="UFF";code=AllChem.UFFOptimizeMolecule(mol,maxIters=2000)
    else: raise ValueError("No complete MMFF or UFF parameterization")
    if code!=0: raise ValueError("Conformer minimization did not converge")
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    sdf=folder/f"compound_{compound_id}.sdf";pdbqt=sdf.with_suffix(".pdbqt")
    mol.SetProp("_Name",f"Compound {compound_id}");mol.SetProp("Preparation",ff+" ETKDGv3 seed=20261029")
    write_sdf(sdf,mol)
    from meeko import MoleculePreparation, PDBQTWriterLegacy
    setups=MoleculePreparation().prepare(mol)
    text,ok,error=PDBQTWriterLegacy.write_string(setups[0])
    if not ok: raise ValueError(error)
    pdbqt.write_text(text,encoding="utf-8")
    props={"MW":Descriptors.MolWt(mol),"cLogP":Crippen.MolLogP(mol),"HBD":Lipinski.NumHDonors(mol),"HBA":Lipinski.NumHAcceptors(mol),"TPSA":Descriptors.TPSA(mol),"force_field":ff,"seed":20261029}
    return sdf,pdbqt,props

def resolve_library(db, folder, progress=lambda text:None, cancelled=None, compound_ids=None):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    session=requests.Session()
    for c in rows(db,"SELECT * FROM chemical_compounds ORDER BY id"):
        if compound_ids is not None and c['id'] not in compound_ids:continue
        if cancelled and cancelled.is_set(): break
        cid=c["id"];name=c["name"]
        existing=db.execute("SELECT status FROM compound_structures WHERE compound_id=?",(cid,)).fetchone()
        if existing and existing[0]=="ready": continue
        progress(f"Resolving {name}")
        cache=folder/f"pubchem_{cid}.json"
        state="unresolved";note="";sdf="";pdbqt="";smiles="";key="";pcid="";url="";props={}
        try:
            if cache.exists(): payload=json.loads(cache.read_text(encoding="utf-8"))
            else:
                base="https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"+quote(name,safe="")
                r=session.get(base+"/property/IsomericSMILES,InChIKey/JSON",timeout=25);r.raise_for_status()
                payload=r.json();prop=payload["PropertyTable"]["Properties"][0]
                syn=session.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{prop['CID']}/synonyms/JSON",timeout=25);syn.raise_for_status()
                payload["synonyms"]=syn.json()["InformationList"]["Information"][0]["Synonym"]
                cache.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
                time.sleep(.25)
            prop=payload["PropertyTable"]["Properties"][0]
            pcid=str(prop["CID"]);url=f"https://pubchem.ncbi.nlm.nih.gov/compound/{pcid}"
            smiles=prop.get("SMILES",prop.get("IsomericSMILES",""));key=prop["InChIKey"]
            if name_key(name) not in {name_key(s) for s in payload["synonyms"]}: raise ValueError("PubChem returned a candidate without an exact normalized synonym match")
            mol=Chem.MolFromSmiles(smiles)
            if mol is None: raise ValueError("Invalid PubChem SMILES")
            stereo=Chem.FindMolChiralCenters(mol,includeUnassigned=True)
            explicit=bool(re.search(r"\(\+\)|\(-\)|\b[RS]\b|[0-9][RS]|\btrans\b|\bcis\b|\(E\)|\(Z\)",name))
            if stereo and not explicit: raise ValueError("Connectivity candidate found; source does not specify absolute stereochemistry. Manual review required")
            if any(label=="?" for _,label in stereo): raise ValueError("Unassigned stereocentres in candidate require manual review")
            if explicit and stereo: raise ValueError("Specified stereoisomer candidate requires manual identity confirmation against source and PubChem before preparation")
            validate_geometric_identity(mol,name)
            if any(k in name.lower() for k in ["hexenal","pseudo phytol","ambrial","pentanediol"]): raise ValueError("Ambiguous or unusual source identity requires manual review")
            identical=db.execute("SELECT * FROM compound_structures WHERE inchikey=? AND status='ready' AND compound_id!=?",(key,cid)).fetchone()
            if identical:
                sdf=Path(identical['sdf_path']);pdbqt=Path(identical['pdbqt_path']);props=json.loads(identical['properties'])
                note='Verified identical InChIKey; shared prepared structure; original name/profile association retained'
            else:
                sdf,pdbqt,props=prepare(smiles,folder,cid);note="Exact normalized PubChem synonym; RDKit validation; achiral or unambiguous geometric identity"
            state="ready"
        except Exception as e: note=str(e)
        db.execute("INSERT INTO compound_structures(compound_id,smiles,inchikey,pubchem_cid,source_url,retrieved_at,sdf_path,pdbqt_path,properties,status,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(compound_id) DO UPDATE SET smiles=excluded.smiles,inchikey=excluded.inchikey,pubchem_cid=excluded.pubchem_cid,source_url=excluded.source_url,retrieved_at=excluded.retrieved_at,sdf_path=excluded.sdf_path,pdbqt_path=excluded.pdbqt_path,properties=excluded.properties,status=excluded.status,notes=excluded.notes",(cid,smiles,key,pcid,url,datetime.datetime.now(datetime.timezone.utc).isoformat(),str(sdf),str(pdbqt),json.dumps(props),state,note))
        db.execute("UPDATE chemical_compounds SET identity_status=?,identity_notes=? WHERE id=?",(state,note,cid));db.commit()
    return rows(db,"SELECT status,count(*) AS count FROM compound_structures GROUP BY status")

