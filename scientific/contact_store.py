"""Versioned reanalysis of old poses, preserving the original contact records."""
import json
from database.store import rows,insert
from scientific.geometry import viewer_contacts,GEOMETRY_VERSION

def ensure_pose_contacts(db,pose_id,force=False):
    pose=rows(db,'SELECT p.*,t.prepared_path,t.id AS protein_id,t.name AS protein_name,r.status AS run_status FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id JOIN protein_targets t ON t.id=r.protein_id WHERE p.id=?',(pose_id,))[0]
    old=rows(db,'SELECT * FROM molecular_interactions WHERE pose_id=?',(pose_id,));reason='Explicit reanalysis requested' if force else ''
    if not force:
        try:
            if not old and pose['run_status']=='interaction_review':raise ValueError('Prior interaction analysis failed')
            if any(json.loads(c['metadata'] or '{}').get('geometry_version')!=GEOMETRY_VERSION for c in old):raise ValueError('Legacy interaction geometry metadata')
            viewer_contacts(pose['prepared_path'],pose['sdf_path'],old);return old
        except Exception as error:reason=str(error)
    from scientific.interactions import analyze
    actual=analyze(pose['prepared_path'],pose['sdf_path'],protein_identifier=f"{pose['protein_id']}:{pose['protein_name']}")
    # Analyze successfully before touching saved rows; retain a recoverable audit.
    with db:
        insert(db,'interaction_reanalyses',pose_id=pose_id,previous_records=json.dumps(old),reason=reason,geometry_version=GEOMETRY_VERSION)
        db.execute('DELETE FROM molecular_interactions WHERE pose_id=?',(pose_id,))
        for contact in actual:insert(db,'molecular_interactions',pose_id=pose_id,**contact)
    return rows(db,'SELECT * FROM molecular_interactions WHERE pose_id=?',(pose_id,))

def ensure_project_contacts(db,project):
    from scientific.runtime import checkpoint
    for pose in rows(db,'SELECT p.id FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id WHERE r.project_id=?',(project,)):
        checkpoint();ensure_pose_contacts(db,pose['id'])
