from pathlib import Path
for folder in ['docs','reporting']:
    for p in Path(folder).rglob('*'):
        if p.suffix not in ['.md','.py']:continue
        s=p.read_text(encoding='utf-8')
        s=s.replace('%LOCALAPPDATA%/I-Mole Lab/NilePhytoDock','%LOCALAPPDATA%/NilePhytoDock')
        s=s.replace('I-Mole Lab','Ahmed G soliman and malak Taha')
        p.write_text(s,encoding='utf-8')
for filename in ['README.md','tools/build_user_guide.py']:
    p=Path(filename);s=p.read_text(encoding='utf-8');s=s.replace('I-Mole Lab','Ahmed G soliman and malak Taha');p.write_text(s,encoding='utf-8')
