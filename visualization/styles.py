"""Shared semantic encodings; residue colors are independent of edge colors."""
import colorsys
import hashlib
import re

INTERACTIONS = {
    'HBDonor': ('Hydrogen bond (ligand donor)', '#2474d2', '7 4'),
    'HBAcceptor': ('Hydrogen bond (ligand acceptor)', '#2474d2', '7 4'),
    'Hydrophobic': ('Hydrophobic', '#27834c', '2 4'),
    'Cationic': ('Ionic (ligand cation)', '#e47b19', ''),
    'Anionic': ('Ionic (ligand anion)', '#e47b19', ''),
    'FaceToFace': ('π–π face-to-face', '#7946b5', '10 3'),
    'EdgeToFace': ('π–π edge-to-face', '#7946b5', '10 3 2 3'),
    'CationPi': ('π–cation (ligand cation)', '#c12b9a', '8 3 2 3'),
    'PiCation': ('π–cation (ligand ring)', '#c12b9a', '8 3 2 3'),
    'VdWContact': ('Van der Waals', '#858b92', '3 3'),
    'MetalDonor': ('Metal coordination', '#b58b00', ''),
    'MetalAcceptor': ('Metal coordination', '#b58b00', ''),
}
PALETTE = {k: v[1] for k, v in INTERACTIONS.items()}
RESIDUE_MODES = ['Biochemical class', 'Polarity', 'Charge', 'Amino acid identity', 'Interaction participation']
CLASSES = {'Acidic': ('ASP GLU', '#f5aaa1'), 'Basic': ('LYS ARG HIS', '#9dbff2'),
           'Polar uncharged': ('SER THR ASN GLN', '#a4ded6'), 'Nonpolar aliphatic': ('ALA VAL LEU ILE MET', '#d8dfa1'),
           'Aromatic': ('PHE TYR TRP', '#cbb2e8'), 'Special': ('GLY PRO CYS', '#f2d398')}
CONVENTION = 'Residue classes assume pH ≈7.4: Lys/Arg +, Asp/Glu −; His neutral/tautomer-dependent, Cys/Tyr neutral. These colors do not determine interaction typing; prepared molecular charges do.'

def residue_name(label):
    return re.match(r'[A-Za-z]+', label or 'UNK')[0][:3].upper()

def residue_category(name, mode):
    name = residue_name(name)
    if mode == 'Charge':
        return ('Positive', '#9dbff2') if name in {'LYS','ARG'} else ('Negative', '#f5aaa1') if name in {'ASP','GLU'} else ('Neutral / conditional', '#d9e1e6')
    if mode == 'Polarity':
        return ('Polar', '#a4ded6') if name in {'ASP','GLU','LYS','ARG','HIS','SER','THR','ASN','GLN','TYR','CYS'} else ('Nonpolar', '#d8dfa1')
    if mode == 'Amino acid identity':
        return name, stable_color(name, .36, .79)
    for category,(members,color) in CLASSES.items():
        if name in members.split():return category,color
    return 'Other / cofactor', '#d9e1e6'

def stable_color(identity, saturation=.65, lightness=.43):
    hue=int(hashlib.sha256(str(identity).encode('utf-8')).hexdigest()[:12],16)/(16**12)
    rgb=colorsys.hls_to_rgb(hue,lightness,saturation)
    return '#'+''.join(f'{round(c*255):02x}' for c in rgb)
