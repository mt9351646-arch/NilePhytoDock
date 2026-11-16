"""Shared scientific color conventions for 2D, 3D and charts."""
import colorsys,hashlib,re,json

INTERACTIONS={
 'HBDonor':('Hydrogen bond','#289b45','7 4','HB donor'),
 'HBAcceptor':('Hydrogen bond','#289b45','7 4','HB acceptor'),
 'Hydrophobic':('Hydrophobic','#b95f9b','5 4','Hydrophobic'),
 'Cationic':('Ionic / salt bridge','#ea580c','','Cationic'),
 'Anionic':('Ionic / salt bridge','#ea580c','','Anionic'),
 'FaceToFace':('Pi-pi stacking','#7c3aed','9 3 2 3','Face-to-face'),
 'EdgeToFace':('Pi-pi stacking','#7c3aed','9 3 2 3','Edge-to-face'),
 'PiCation':('Pi-cation','#d946ef','9 3','Pi-cation'),
 'CationPi':('Pi-cation','#d946ef','9 3','Cation-pi'),
 'VdWContact':('Van der Waals','#83a85a','2 3','Van der Waals'),
 'MetalDonor':('Metal coordination','#b88a00','','Metal donor'),
 'MetalAcceptor':('Metal coordination','#b88a00','','Metal acceptor')}
PALETTE={k:v[1] for k,v in INTERACTIONS.items()}
MODES=['Polarity','Charge','Biochemical class','Amino acid identity','Hydrophobicity','Aromaticity','Interaction participation']
HYDROPHOBICITY={'ILE':4.5,'VAL':4.2,'LEU':3.8,'PHE':2.8,'CYS':2.5,'MET':1.9,'ALA':1.8,'GLY':-.4,'THR':-.7,'SER':-.8,'TRP':-.9,'TYR':-1.3,'PRO':-1.6,'HIS':-3.2,'GLU':-3.5,'GLN':-3.5,'ASP':-3.5,'ASN':-3.5,'LYS':-3.9,'ARG':-4.5}
CLASSES={**dict.fromkeys(['ASP','GLU'],'Acidic'),**dict.fromkeys(['LYS','ARG','HIS'],'Basic'),**dict.fromkeys(['SER','THR','ASN','GLN'],'Polar uncharged'),**dict.fromkeys(['ALA','VAL','ILE','LEU','MET'],'Nonpolar aliphatic'),**dict.fromkeys(['PHE','TYR','TRP'],'Aromatic'),**dict.fromkeys(['GLY','PRO','CYS'],'Special')}
CLASS_COLORS={'Acidic':'#f9b7b7','Basic':'#b9cdfa','Polar uncharged':'#b5e6da','Nonpolar aliphatic':'#f1ddb1','Aromatic':'#ddc5ed','Special':'#d5dce5','Other':'#e2e8f0'}
POLAR=set(['SER','THR','CYS','ASN','GLN','TYR','HIS','LYS','ARG','ASP','GLU'])
IDENTITIES=['ALA','ARG','ASN','ASP','CYS','GLN','GLU','GLY','HIS','ILE','LEU','LYS','MET','PHE','PRO','SER','THR','TRP','TYR','VAL']
CHARGE_NOTE='At general pH 7.4: Asp/Glu negative, Lys/Arg positive, His neutral unless explicitly protonated. Prepared formal residue charge takes precedence when available; this is not a site-specific pKa calculation.'
def stable_color(key):
 digest=hashlib.sha256(str(key).encode('utf-8')).digest();h=int.from_bytes(digest[:2],'big')/65536;s=.58+(digest[2]/255)*.14;l=.40+(digest[3]/255)*.12
 r,g,b=colorsys.hls_to_rgb(h,l,s);return '#'+''.join(f'{round(255*v):02x}' for v in (r,g,b))
def residue_name(contact):
 data=json.loads(contact.get('metadata') or '{}');return data.get('residue_name') or re.sub('[^A-Z]','',contact['residue'])[:3]
def residue_category(name,mode,charge=None):
 if mode=='Aromaticity':return 'Aromatic' if name in ['PHE','TYR','TRP','HIS'] else 'Nonaromatic' if name in IDENTITIES else 'Other'
 if mode=='Hydrophobicity':
  value=HYDROPHOBICITY.get(name)
  return 'Other' if value is None else 'Hydrophobic (>1)' if value>1 else 'Hydrophilic (<-1)' if value< -1 else 'Intermediate'
 if mode=='Polarity':return 'Polar' if name in POLAR else 'Nonpolar' if name in IDENTITIES else 'Other'
 if mode=='Charge':
  value=charge if charge is not None else -1 if name in ['ASP','GLU','CYM','TYM'] else 1 if name in ['LYS','ARG','HIP'] else 0
  return 'Positive' if value>0 else 'Negative' if value<0 else 'Neutral'
 if mode=='Biochemical class':return CLASSES.get(name,'Other')
 if mode=='Amino acid identity':return name if name in IDENTITIES else 'Other'
 return 'Interaction participation'
def residue_color(name,mode='Biochemical class',charge=None):
 category=residue_category(name,mode,charge)
 if mode=='Aromaticity':return {'Aromatic':'#ddc5ed','Nonaromatic':'#b5e6da','Other':'#e2e8f0'}[category]
 if mode=='Hydrophobicity':return {'Hydrophobic (>1)':'#e4bc70','Hydrophilic (<-1)':'#83c5df','Intermediate':'#cbd5e1','Other':'#e2e8f0'}[category]
 if mode=='Polarity':return {'Polar':'#b7e5de','Nonpolar':'#f1ddb1','Other':'#e2e8f0'}[category]
 if mode=='Charge':return {'Positive':'#b9cdfa','Negative':'#f9b7b7','Neutral':'#e2e8f0'}[category]
 if mode=='Amino acid identity':return stable_color(name)
 return CLASS_COLORS.get(category,'#f8fafc')
def residue_legend(mode):
 cats={'Polarity':['Polar','Nonpolar','Other'],'Charge':['Positive','Negative','Neutral'],'Hydrophobicity':['Hydrophobic (>1)','Hydrophilic (<-1)','Intermediate','Other'],'Aromaticity':['Aromatic','Nonaromatic','Other'],'Biochemical class':list(CLASS_COLORS),'Amino acid identity':IDENTITIES+['Other'],'Interaction participation':['Segmented ring shows every interaction category']}[mode]
 result=[]
 for cat in cats:
  sample=next((a for a in IDENTITIES if residue_category(a,mode)==cat),'UNK')
  result.append((cat,residue_color(sample,mode)))
 return result
