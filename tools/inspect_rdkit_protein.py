from rdkit import Chem
p='data/validation/science/3PTB/selected.pdb'
for prox in [True,False]:
 m=Chem.MolFromPDBFile(p,removeHs=False,sanitize=True,proximityBonding=prox);print('RDKit',prox, bool(m),m.GetNumBonds() if m else None)
 if m:
  print('problems',len(Chem.DetectChemistryProblems(m)));print(Chem.MolToSmiles(m)[:70]);Chem.MolToMolFile(m,'data/validation/test_rdkit.mol',forceV3000=True)
