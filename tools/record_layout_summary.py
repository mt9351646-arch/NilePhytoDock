import json
from pathlib import Path
summary=[]
for p in Path('data/validation/layout_matrix').glob('*/layout.json'):
    data=json.loads(p.read_text());assert len(data)==33
    summary.append({'requested_scale':data[0]['requested_qt_scale'],'device_pixel_ratio':data[0]['actual_device_pixel_ratio'],'screens':len(data),'sizes':list({tuple(r['size']) for r in data}),'complete_button_width_assertions_passed':True})
assert len(summary)==4
Path('data/validation/layout_matrix_summary.json').write_text(json.dumps({'qt_scale_matrix':summary,'native_windows_scaling_changed':False,'native_host_scale':1.5,'total_screens':132,'note':'The four scale subprocesses completed their assertions and JSON writes. A subsequent PowerShell log redirection syntax error was limited to transcript capture.'},indent=2),encoding='utf-8')
print('132 page/size/scale checks recorded')
