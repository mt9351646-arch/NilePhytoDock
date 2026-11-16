from pathlib import Path
import json
r=json.loads(Path('data/validation/science/validation_results.json').read_text())
print('Top pocket center distance:',r['top_pocket_to_experimental_ligand_centroid_A'])
print('RMSD:',r['redocking'][0]['rmsd_A'])
print('Reference eucalyptol contacts:',len(r['interactions']))
