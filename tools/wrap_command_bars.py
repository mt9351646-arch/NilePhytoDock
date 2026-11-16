from pathlib import Path
p=Path('app/gui.py');s=p.read_text(encoding='utf-8');s=s.replace('from app.paths import user_data,resource','from app.flow_layout import FlowLayout\nfrom app.paths import user_data,resource');s=s.replace('bar=QHBoxLayout()','bar=FlowLayout()');p.write_text(s,encoding='utf-8')
p=Path('app/redesign.py');s=p.read_text(encoding='utf-8');s=s.replace('from app.paths import resource,user_data','from app.flow_layout import FlowLayout\nfrom app.paths import resource,user_data');s=s.replace('bar=QHBoxLayout()','bar=FlowLayout()').replace('tools=QHBoxLayout()','tools=FlowLayout()').replace('actions=QHBoxLayout();self.button(\'Import proteins\'','actions=FlowLayout();self.button(\'Import proteins\'').replace('pocket_bar=QHBoxLayout()','pocket_bar=FlowLayout()')
# Output actions also need wrapping independently of the expanding path field.
s=s.replace("row=QHBoxLayout();self.button('Create New Folder'","row=FlowLayout();self.button('Create New Folder'")
p.write_text(s,encoding='utf-8')
