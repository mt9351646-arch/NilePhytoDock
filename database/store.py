import json
import shutil
import sqlite3
from pathlib import Path
from app.paths import resource, user_data

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS plant_species(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS essential_oils(id INTEGER PRIMARY KEY, species_id INTEGER REFERENCES plant_species, name TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS scientific_references(id INTEGER PRIMARY KEY, source_document TEXT UNIQUE, citation TEXT, notes TEXT, sha256 TEXT);
CREATE TABLE IF NOT EXISTS oil_profiles(id INTEGER PRIMARY KEY, oil_id INTEGER REFERENCES essential_oils, name TEXT UNIQUE NOT NULL, plant_part TEXT, method TEXT, origin TEXT, profile_type TEXT, reference_id INTEGER REFERENCES scientific_references, notes TEXT);
CREATE TABLE IF NOT EXISTS chemical_compounds(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, identity_status TEXT DEFAULT 'unresolved', identity_notes TEXT);
CREATE TABLE IF NOT EXISTS compound_aliases(id INTEGER PRIMARY KEY, compound_id INTEGER REFERENCES chemical_compounds, original_name TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS compound_structures(id INTEGER PRIMARY KEY, compound_id INTEGER UNIQUE REFERENCES chemical_compounds, smiles TEXT, inchikey TEXT, pubchem_cid TEXT, source_url TEXT, retrieved_at TEXT, sdf_path TEXT, pdbqt_path TEXT, properties TEXT, status TEXT, notes TEXT);
CREATE TABLE IF NOT EXISTS profile_compounds(id INTEGER PRIMARY KEY, profile_id INTEGER REFERENCES oil_profiles, compound_id INTEGER REFERENCES chemical_compounds, original_name TEXT, percentage REAL, sd REAL, value_status TEXT, chemical_class TEXT, reference_id INTEGER REFERENCES scientific_references, source_table INTEGER, source_row INTEGER, original_row TEXT, notes TEXT, confidence TEXT, validation_status TEXT);
CREATE TABLE IF NOT EXISTS extraction_audit(id INTEGER PRIMARY KEY, reference_id INTEGER REFERENCES scientific_references, source_table INTEGER, source_row INTEGER, original_row TEXT, interpretation TEXT, profile_id INTEGER REFERENCES oil_profiles, compound_id INTEGER REFERENCES chemical_compounds);
CREATE TABLE IF NOT EXISTS analysis_projects(id INTEGER PRIMARY KEY, name TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, status TEXT, settings TEXT, folder TEXT);
CREATE TABLE IF NOT EXISTS protein_targets(id INTEGER PRIMARY KEY, project_id INTEGER REFERENCES analysis_projects, name TEXT, original_path TEXT, prepared_path TEXT, pdbqt_path TEXT, sha256 TEXT, metadata TEXT, status TEXT, error TEXT);
CREATE TABLE IF NOT EXISTS predicted_pockets(id INTEGER PRIMARY KEY, protein_id INTEGER REFERENCES protein_targets, rank INTEGER, score REAL, center TEXT, size TEXT, residues TEXT, method TEXT, provenance TEXT);
CREATE TABLE IF NOT EXISTS docking_runs(id INTEGER PRIMARY KEY, project_id INTEGER REFERENCES analysis_projects, protein_id INTEGER REFERENCES protein_targets, pocket_id INTEGER REFERENCES predicted_pockets, compound_id INTEGER REFERENCES chemical_compounds, cache_key TEXT UNIQUE, settings TEXT, status TEXT, error TEXT, elapsed REAL, log_path TEXT, engine_version TEXT, folder TEXT);
CREATE TABLE IF NOT EXISTS docking_poses(id INTEGER PRIMARY KEY, run_id INTEGER REFERENCES docking_runs, rank INTEGER, score REAL, sdf_path TEXT, complex_path TEXT, UNIQUE(run_id,rank));
CREATE TABLE IF NOT EXISTS molecular_interactions(id INTEGER PRIMARY KEY, pose_id INTEGER REFERENCES docking_poses, residue TEXT, chain TEXT, residue_number TEXT, interaction_type TEXT, protein_atom TEXT, ligand_atom TEXT, distance REAL, angle REAL, method TEXT, metadata TEXT);
CREATE TABLE IF NOT EXISTS ranking_results(id INTEGER PRIMARY KEY, project_id INTEGER REFERENCES analysis_projects, protein_id INTEGER REFERENCES protein_targets, profile_id INTEGER REFERENCES oil_profiles, result TEXT);
CREATE TABLE IF NOT EXISTS execution_logs(id INTEGER PRIMARY KEY, project_id INTEGER REFERENCES analysis_projects, time TEXT DEFAULT CURRENT_TIMESTAMP, level TEXT, message TEXT);
CREATE TABLE IF NOT EXISTS calculation_cache(signature TEXT PRIMARY KEY, folder TEXT NOT NULL, poses TEXT NOT NULL, manifest TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS csv_imports(sha256 TEXT PRIMARY KEY, source_name TEXT, summary TEXT, imported_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS csv_composition_records(id INTEGER PRIMARY KEY,source_sha256 TEXT,source_row INTEGER,profile_id INTEGER REFERENCES oil_profiles,compound_id INTEGER REFERENCES chemical_compounds,profile_compound_id INTEGER REFERENCES profile_compounds,percentage REAL,original_row TEXT,status TEXT,UNIQUE(source_sha256,source_row));
INSERT OR IGNORE INTO schema_migrations(version) VALUES(1);
INSERT OR IGNORE INTO schema_migrations(version) VALUES(2);
INSERT OR IGNORE INTO schema_migrations(version) VALUES(3);
"""

def connect(path=None):
    if path is None:
        path = user_data() / "nilephytodock.sqlite"
        if not path.exists() and resource("data", "nilephytodock.sqlite").exists():
            shutil.copy2(resource("data", "nilephytodock.sqlite"), path)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(SCHEMA)
    existing={r[1] for r in db.execute('PRAGMA table_info(predicted_pockets)')}
    for field,kind in [('name','TEXT'),('probability','REAL')]:
        if field not in existing:db.execute(f'ALTER TABLE predicted_pockets ADD COLUMN {field} {kind}')
    db.execute('INSERT OR IGNORE INTO schema_migrations(version) VALUES(4)');db.commit()
    # Preserve chromatography units and keep non-oil measurements out of the
    # GC peak-area weighting model. Existing source records remain unchanged.
    for table,fields in {
        'oil_profiles':[('quantitation_basis','TEXT'),('ranking_eligible','INTEGER DEFAULT 1'),('geography_status','TEXT'),('extraction_method','TEXT'),('analytical_method','TEXT')],
        'essential_oils':[('common_name','TEXT')],
        'profile_compounds':[('reported_value','REAL'),('reported_unit','TEXT'),('annotation_level','TEXT'),('reported_formula','TEXT'),('docking_eligible','INTEGER DEFAULT 1')]
    }.items():
        existing={r[1] for r in db.execute('PRAGMA table_info('+table+')')}
        for field,kind in fields:
            if field not in existing:db.execute(f'ALTER TABLE {table} ADD COLUMN {field} {kind}')
    db.execute('CREATE TABLE IF NOT EXISTS literature_imports (sha256 TEXT PRIMARY KEY, manifest_name TEXT, summary TEXT, imported_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    db.execute("UPDATE oil_profiles SET ranking_eligible=0 WHERE lower(profile_type) LIKE '%headspace%' AND ranking_eligible=1")
    db.execute('INSERT OR IGNORE INTO schema_migrations(version) VALUES(5)');db.commit()
    db.execute('CREATE TABLE IF NOT EXISTS interaction_reanalyses (id INTEGER PRIMARY KEY, pose_id INTEGER REFERENCES docking_poses, performed_at TEXT DEFAULT CURRENT_TIMESTAMP, previous_records TEXT, reason TEXT, geometry_version TEXT)')
    db.execute('INSERT OR IGNORE INTO schema_migrations(version) VALUES(6)');db.commit()
    if 'preparation_category' not in {r[1] for r in db.execute('PRAGMA table_info(oil_profiles)')}:db.execute('ALTER TABLE oil_profiles ADD COLUMN preparation_category TEXT')
    db.execute("UPDATE oil_profiles SET preparation_category=CASE WHEN lower(profile_type) LIKE '%fatty%' OR lower(profile_type) LIKE '%fixed%' THEN 'Fixed Oils' WHEN lower(profile_type) LIKE '%resin%' OR lower(profile_type) LIKE '%absolute%' THEN 'Resins and Aromatic Preparations' WHEN profile_type IN ('Essential oil','Extracted oil profile') THEN 'Essential Oils' WHEN lower(profile_type) LIKE '%individual%' THEN 'Individual Natural Compounds' ELSE 'Botanical Extracts' END WHERE preparation_category IS NULL")
    db.execute('CREATE TABLE IF NOT EXISTS botanical_history (id INTEGER PRIMARY KEY, scientific_name TEXT, common_name TEXT, association TEXT, evidence_type TEXT, period TEXT, source_url TEXT, citation TEXT, confidence TEXT, description TEXT, taxonomic_scope TEXT, UNIQUE(scientific_name,association,source_url))')
    db.execute('CREATE TABLE IF NOT EXISTS molecular_analysis_runs (id INTEGER PRIMARY KEY,project_id INTEGER REFERENCES analysis_projects,created_at TEXT DEFAULT CURRENT_TIMESTAMP,method_version TEXT,scope TEXT,signature TEXT,result TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS ligand_functional_annotations (pose_id INTEGER PRIMARY KEY REFERENCES docking_poses,ontology_version TEXT,sdf_sha256 TEXT,groups_json TEXT)')
    db.execute('INSERT OR IGNORE INTO schema_migrations(version) VALUES(7)');db.commit()
    return db

def rows(db, query, args=()):
    return [dict(r) for r in db.execute(query, args)]

def insert(db, table, **values):
    # Table and column identifiers come only from internal application code.
    return db.execute(f"INSERT INTO {table} ({','.join(values)}) VALUES ({','.join('?' for _ in values)})", tuple(values.values())).lastrowid

def log(db, project, message, level="INFO"):
    insert(db,"execution_logs",project_id=project,level=level,message=message)
    db.commit()

def counts(db):
    return {"botanical_oils":db.execute("SELECT count(DISTINCT oil_id) FROM oil_profiles WHERE preparation_category IN ('Essential Oils','Fixed Oils')").fetchone()[0],
            "essential_oils":db.execute("SELECT count(DISTINCT o.id) FROM essential_oils o JOIN oil_profiles p ON p.oil_id=o.id WHERE p.preparation_category='Essential Oils'").fetchone()[0],
            "fixed_oils":db.execute("SELECT count(DISTINCT oil_id) FROM oil_profiles WHERE preparation_category='Fixed Oils'").fetchone()[0],
            "species": db.execute("SELECT count(*) FROM plant_species").fetchone()[0],
            "profiles": db.execute("SELECT count(*) FROM oil_profiles").fetchone()[0],
            "compounds": db.execute("SELECT count(*) FROM chemical_compounds").fetchone()[0],
            "ready": db.execute("SELECT count(*) FROM compound_structures WHERE status='ready'").fetchone()[0],
            "unique_ready": db.execute("SELECT count(DISTINCT inchikey) FROM compound_structures WHERE status='ready'").fetchone()[0],
            "records": db.execute("SELECT count(*) FROM profile_compounds").fetchone()[0]}

