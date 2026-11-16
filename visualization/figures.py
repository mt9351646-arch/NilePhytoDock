import json
from pathlib import Path
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, Draw
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from database.store import rows
from scientific.molecules import read_sdf

from visualization.semantics import PALETTE as COLORS

def export_pose(db,pose_id,folder,dpi=300):
    row=rows(db,'SELECT p.*,c.name,t.name AS protein_name FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id JOIN chemical_compounds c ON c.id=r.compound_id JOIN protein_targets t ON t.id=r.protein_id WHERE p.id=?',(pose_id,))[0]
    contacts=rows(db,'SELECT * FROM molecular_interactions WHERE pose_id=?',(pose_id,))
    from visualization.interaction_diagram import diagram,save_diagram
    title=f"{row['name']} · {row['protein_name']} · pose {row['rank']} · {row['score']:.3f} kcal/mol"
    svg,layout=diagram(row['sdf_path'],contacts,title)
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);out=folder/f'interactions_pose_{row["rank"]}'
    save_diagram(svg,out,dpi)
    out.with_suffix('.layout.json').write_text(json.dumps(layout,indent=2),encoding='utf-8')
    complex_path=Path(row['complex_path']).resolve();sdf=Path(row['sdf_path']).resolve()
    pml=f'''load "{complex_path.as_posix()}", complex
hide everything
show cartoon, polymer
show sticks, resn LIG
color cyan, resn LIG
zoom resn LIG, 8
bg_color white
'''
    (folder/'view.pml').write_text(pml,encoding='utf-8')
    return out.with_suffix('.png')

def charts(db,project,folder,dpi=300):
    from visualization.release_charts import CHARTS,chart_spec,export_chart
    from scientific.contact_store import ensure_project_contacts
    ensure_project_contacts(db,project)
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);out=[]
    from scientific.runtime import checkpoint
    for kind in CHARTS:
        checkpoint()
        spec=chart_spec(db,project,kind)
        if spec['available']:out.append(export_chart(spec,folder/kind.lower().replace(' ','_'),dpi))
    return out

def legacy_charts(db,project,folder,dpi=300):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    data=rows(db,'SELECT c.name,t.name AS protein,min(p.score) AS score FROM docking_poses p JOIN docking_runs r ON r.id=p.run_id JOIN chemical_compounds c ON c.id=r.compound_id JOIN protein_targets t ON t.id=r.protein_id WHERE r.project_id=? GROUP BY c.id,t.id',(project,))
    if not data:return []
    names=list(dict.fromkeys(r['name'] for r in data));targets=list(dict.fromkeys(r['protein'] for r in data));matrix=np.full((len(names),len(targets)),np.nan)
    for r in data:matrix[names.index(r['name']),targets.index(r['protein'])]=r['score']
    fig,ax=plt.subplots(figsize=(max(7,len(targets)*1.6),max(4,min(36,len(names)*.25))))
    im=ax.imshow(matrix,aspect='auto',cmap='viridis_r');ax.set_xticks(range(len(targets)),targets,rotation=30,ha='right');ax.set_yticks(range(len(names)),names,fontsize=8);fig.colorbar(im,ax=ax,label='Smina score (kcal/mol)');ax.set_title('Compound–protein docking scores')
    out=[]
    def save(fig,name):
        png=folder/(name+'.png');fig.savefig(png,dpi=dpi,bbox_inches='tight');fig.savefig(folder/(name+'.svg'),bbox_inches='tight');plt.close(fig);out.append(png)
    save(fig,'docking_heatmap')
    from scientific.ranking import project_rankings
    ranks=project_rankings(db,project);pnames={r['id']:r['name'] for r in rows(db,'SELECT * FROM oil_profiles')}
    if ranks:
        pids=list(dict.fromkeys(r['profile_id'] for rs in ranks.values() for r in rs));tids=list(ranks);matrix=np.full((len(pids),len(tids)),np.nan)
        for j,t in enumerate(tids):
            for r in ranks[t]:
                if r['index'] is not None:matrix[pids.index(r['profile_id']),j]=r['index']
        if np.isfinite(matrix).any():
            fig,ax=plt.subplots(figsize=(9,max(4,len(pids)*.3)));im=ax.imshow(matrix,vmin=0,vmax=1,cmap='YlGnBu',aspect='auto');tn={r['id']:r['name'] for r in rows(db,'SELECT * FROM protein_targets WHERE project_id=?',(project,))};ax.set_xticks(range(len(tids)),[tn[t] for t in tids]);ax.set_yticks(range(len(pids)),[pnames[p] for p in pids],fontsize=8);fig.colorbar(im,ax=ax,label='Composition-informed index');ax.set_title('Oil profile priorities');save(fig,'oil_heatmap')
    for target in targets:
        best=sorted([r for r in data if r['protein']==target],key=lambda r:r['score'])[:15]
        fig,ax=plt.subplots(figsize=(9,6));ax.barh([r['name'] for r in best][::-1],[r['score'] for r in best][::-1],color='#17867e');ax.set_xlabel('Smina score (kcal/mol)');ax.set_title(target+' — best compounds');save(fig,'best_'+str(targets.index(target)))
    contact=rows(db,'SELECT i.interaction_type,count(*) AS n FROM molecular_interactions i JOIN docking_poses p ON p.id=i.pose_id JOIN docking_runs r ON r.id=p.run_id WHERE r.project_id=? GROUP BY i.interaction_type',(project,))
    if contact:
        fig,ax=plt.subplots(figsize=(9,5));ax.barh([r['interaction_type'] for r in contact],[r['n'] for r in contact],color='#467d9d');ax.set_xlabel('Detected contacts across all saved poses');ax.set_title('Interaction frequency (counts do not measure affinity)');save(fig,'interaction_frequency')
    tn={r['id']:r['name'] for r in rows(db,'SELECT * FROM protein_targets WHERE project_id=?',(project,))}
    for tid,rs in ranks.items():
        valid=[r for r in rs if r['index'] is not None]
        if valid:
            fig,ax=plt.subplots(figsize=(11,max(4,len(valid)*.35)));labels=[pnames[r['profile_id']] for r in valid][::-1];ax.barh(labels,[r['index'] for r in valid][::-1],color='#208479');ax.set_xlim(0,1);ax.set_xlabel('Composition-informed index');ax.set_title(tn[tid]+' — oil profile priority');save(fig,'oil_ranking_'+str(tid))
    import networkx as nx
    graph=nx.Graph()
    edges=rows(db,'SELECT DISTINCT t.name AS protein,c.name AS compound,i.residue,i.interaction_type FROM molecular_interactions i JOIN docking_poses p ON p.id=i.pose_id JOIN docking_runs r ON r.id=p.run_id JOIN protein_targets t ON t.id=r.protein_id JOIN chemical_compounds c ON c.id=r.compound_id WHERE r.project_id=? ORDER BY i.id LIMIT 100',(project,))
    for r in edges:
        a='Ligand: '+r['compound'];b=r['protein']+': '+r['residue'];graph.add_edge(a,b,kind=r['interaction_type'])
    def network(g,title,name):
        if not g:return
        fig,ax=plt.subplots(figsize=(13,9));pos=nx.spring_layout(g,seed=20261029);nx.draw_networkx(g,pos,ax=ax,node_size=550,font_size=7,node_color=['#a5d6c8' if str(n).startswith('Ligand:') else '#d7e4ec' for n in g],edge_color='#9baeb7');ax.set_title(title);ax.axis('off');save(fig,name)
    network(graph,'Molecular interaction network — up to 100 observed edges','interaction_network')
    graph=nx.Graph()
    associations=rows(db,'SELECT DISTINCT op.name AS oil,c.name AS compound,t.name AS protein FROM docking_runs r JOIN docking_poses dp ON dp.run_id=r.id JOIN chemical_compounds c ON c.id=r.compound_id JOIN protein_targets t ON t.id=r.protein_id JOIN profile_compounds pc ON pc.compound_id=c.id JOIN oil_profiles op ON op.id=pc.profile_id WHERE r.project_id=? ORDER BY op.id LIMIT 80',(project,))
    selected=__import__('json').loads(db.execute('SELECT settings FROM analysis_projects WHERE id=?',(project,)).fetchone()[0])['profiles'];selected_names={pnames[p] for p in selected}
    for r in associations:
        if r['oil'] in selected_names:graph.add_edge('Oil: '+r['oil'],'Ligand: '+r['compound']);graph.add_edge('Ligand: '+r['compound'],'Protein: '+r['protein'])
    network(graph,'Oil–compound–protein relationships — screened constituents only','oil_compound_protein_network')
    return out

