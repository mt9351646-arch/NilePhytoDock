from pathlib import Path

p=Path('app/gui.py');s=p.read_text(encoding='utf-8')
s=s.replace("self.button('Open user guide',lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(resource('docs','USER_GUIDE_AR.pdf')))),l);",'')
s=s.replace("See the methodology and validation report for the tested scope.","Refer to the separate English documentation for the tested scope.")
s=s.replace("Original GC–MS peak-area percentages retained. Docking results are predictions.","Published analytical values retain their original units. Docking results are predictions.")
s=s.replace("Published peak-area percentages are never rescaled in the source database. Unresolved identities remain visible and are excluded from docking.","Published values retain their original units. Headspace, extracts and fatty-acid pools have no oil index. Unresolved structures are excluded from docking.")
s=s.replace("'original_name','percentage','sd','value_status','structure_status','identity_notes','source_document'","'original_name','reported_value','reported_unit','sd','value_status','profile_type','origin','geography_status','annotation_level','structure_status','identity_notes','source_document'")
s=s.replace('pc.original_name,pc.percentage,pc.sd,pc.value_status,COALESCE',"pc.original_name,pc.percentage,COALESCE(pc.reported_value,pc.percentage) AS reported_value,COALESCE(pc.reported_unit,CASE WHEN pc.percentage IS NOT NULL THEN 'GC peak area %' ELSE '' END) AS reported_unit,pc.sd,pc.value_status,p.profile_type,p.origin,p.geography_status,pc.annotation_level,COALESCE")
p.write_text(s,encoding='utf-8')
for name in ['app/branding.py','pyproject.toml','build/windows_version.txt']:
 p=Path(name);s=p.read_text(encoding='utf-8').replace('0.3.0','0.4.0').replace('(0,3,0,0)','(0,4,0,0)');p.write_text(s,encoding='utf-8')
p=Path('build/NilePhytoDock.spec');s=p.read_text(encoding='utf-8').replace(",(str(root/'docs'),'docs')",'')
s=s.replace("(str(root/'data'/'compound_library'),'data/compound_library')","(str(root/'data'/'compound_library'),'data/compound_library'),(str(root/'data'/'literature'),'data/literature')")
p.write_text(s,encoding='utf-8')
