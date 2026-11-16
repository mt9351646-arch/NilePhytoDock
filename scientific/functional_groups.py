"""Versioned atom-centred SMARTS ontology, independent of compound names.

Specific carbonyl classes take precedence over generic carbonyls. Phenolic OH
is not also alcohol; amide N is not amine. Aromatic/alkene/hydrophobic features
are a separate domain and may overlap a conventional group, explicitly.
"""
from rdkit import Chem
VERSION='nile-functional-groups-1'
# name, SMARTS, atom positions defining the functional centre, domain
PATTERNS=[
 ('Carboxylic acid/carboxylate','[CX3](=[OX1])[OX2H1,OX1-]',(0,1,2),'Functional group'),
 ('Ester','[CX3](=[OX1])[OX2H0][#6]',(0,1,2),'Functional group'),
 ('Amide','[CX3](=[OX1])[NX3]',(0,1,2),'Functional group'),
 ('Aldehyde','[CX3H1](=[OX1])[#6]',(0,1),'Functional group'),
 ('Ketone','[#6][CX3](=[OX1])[#6]',(1,2),'Functional group'),
 ('Phenolic hydroxyl','[OX2H1][c]',(0,),'Functional group'),
 ('Alcohol hydroxyl','[OX2H1][CX4]',(0,),'Functional group'),
 ('Ether','[OD2]([#6])[#6]',(0,),'Functional group'),
 ('Amine','[N;X3,X4+;!$(N-C=O);!$(N-S(=O)=O);!$(N=*)]',(0,),'Functional group'),
 ('Sulfonyl','[SX4](=[OX1])(=[OX1])',(0,1,2),'Functional group'),
 ('Sulfoxide','[SX3](=[OX1])',(0,1),'Functional group'),
 ('Thiol','[SX2H1]',(0,),'Functional group'),
 ('Disulfide/polysulfide','[SX2][SX2]',(0,1),'Functional group'),
 ('Thioether','[#6][SX2H0][#6]',(1,),'Functional group'),
 ('Alkene feature','[CX3;!$(C=O)]=[CX3;!$(C=O)]',(0,1),'Molecular feature'),
]
COMPILED=[(name,Chem.MolFromSmarts(smarts),indices,domain) for name,smarts,indices,domain in PATTERNS]

def identify(mol):
 if mol is None:raise ValueError('A validated molecular graph is required')
 result=[];claimed=set()
 for name,pattern,indices,domain in COMPILED:
  if pattern is None:raise ValueError('Invalid ontology SMARTS: '+name)
  for match in mol.GetSubstructMatches(pattern,uniquify=True):
   atoms=frozenset(match[i] for i in indices)
   if name=='Disulfide/polysulfide':
    connected=set(atoms);pending=list(atoms)
    while pending:
     for neighbour in mol.GetAtomWithIdx(pending.pop()).GetNeighbors():
      if neighbour.GetAtomicNum()==16 and neighbour.GetIdx() not in connected:connected.add(neighbour.GetIdx());pending.append(neighbour.GetIdx())
    atoms=frozenset(connected)
   if domain=='Functional group' and atoms & claimed:continue
   if domain=='Functional group':claimed.update(atoms)
   if not any(r['name']==name and set(r['atoms'])==atoms for r in result):result.append({'name':name,'atoms':sorted(atoms),'domain':domain})
 for ring in Chem.GetSymmSSSR(mol):
  atoms=list(ring)
  if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in atoms):result.append({'name':'Aromatic ring feature','atoms':sorted(atoms),'domain':'Molecular feature'})
 # Hydrophobic atom features are chemically typed by the same ProLIF SMARTS.
 from prolif.interactions import Hydrophobic
 hydrophobic=Hydrophobic()
 for match in mol.GetSubstructMatches(hydrophobic.lig_pattern):
  result.append({'name':'Hydrophobic atom feature','atoms':list(match),'domain':'Molecular feature'})
 return result

def participating(mol,groups,indices,interaction_type):
 atoms=set()
 for i in indices:
  atom=mol.GetAtomWithIdx(int(i))
  if atom.GetAtomicNum()==1:atoms.update(a.GetIdx() for a in atom.GetNeighbors() if a.GetAtomicNum()!=1)
  else:atoms.add(int(i))
 matches=[]
 for group in groups:
  hit=bool(atoms & set(group['atoms']))
  if group['name']=='Aromatic ring feature':hit=interaction_type in ['FaceToFace','EdgeToFace','PiCation','CationPi'] and len(atoms & set(group['atoms']))>=3
  if group['name']=='Hydrophobic atom feature':hit=interaction_type in ['Hydrophobic','VdWContact'] and hit
  if hit:matches.append(group)
 return matches or [{'name':'Unassigned atom/feature','atoms':sorted(atoms),'domain':'Unassigned'}]

def ontology():
 return {'version':VERSION,'patterns':[{'name':name,'smarts':smarts,'centre_positions':indices,'domain':domain} for name,smarts,indices,domain in PATTERNS],
 'policy':'Specific functional centres claim atoms in listed priority order. Aromatic, alkene and chemically typed hydrophobic features are orthogonal; their frequencies must not be summed as independent conventional functional groups. Explicit-H contacts map to their bonded heavy atom. Aromatic feature assignment requires ring geometry indices and an aromatic interaction category.'}
