from pathlib import Path
p=Path('visualization/figures.py');s=p.read_text(encoding='utf-8');a=s.index('    mol=read_sdf',s.index('def export_pose'));b=s.index('    complex_path=',a)
s=s[:a]+'''    from visualization.interaction_diagram import diagram,save_diagram
    title=f"{row['name']} · {row['protein_name']} · pose {row['rank']} · {row['score']:.3f} kcal/mol"
    svg,layout=diagram(row['sdf_path'],contacts,title)
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);out=folder/f'interactions_pose_{row["rank"]}'
    save_diagram(svg,out,dpi)
    out.with_suffix('.layout.json').write_text(json.dumps(layout,indent=2),encoding='utf-8')
'''+s[b:];p.write_text(s,encoding='utf-8')
