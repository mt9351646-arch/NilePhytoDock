from rdkit import Chem
from openbabel import openbabel as ob
m=Chem.MolFromPDBFile('data/validation/science/3PTB/selected.pdb',removeHs=True)
c=ob.OBConversion();c.SetInAndOutFormats('mol','sdf');mol=ob.OBMol();c.ReadString(mol,Chem.MolToMolBlock(m,forceV3000=True))
def show(when):
 a=mol.GetAtom(362); print(when,a.GetFormalCharge(),a.GetImplicitHCount(),[(n.GetIdx(),n.GetAtomicNum(),mol.GetBond(a,n).GetBondOrder()) for n in ob.OBAtomAtomIter(a)])
show('READ');mol.AddHydrogens(False,True,7.4);show('HYDROGENS')
excess=[]
for a in ob.OBMolAtomIter(mol):
 if a.GetAtomicNum()==6 and a.GetFormalCharge()==0:
  val=sum(b.GetBondOrder() for b in ob.OBAtomBondIter(a));hs=[n.GetIdx() for n in ob.OBAtomAtomIter(a) if n.GetAtomicNum()==1]
  if val>4:excess+=hs[:val-4]
print('EXCESS',excess)
for i in sorted(excess,reverse=True):mol.DeleteAtom(mol.GetAtom(i))
for a in ob.OBMolAtomIter(mol):a.SetImplicitHCount(0)
show('CORRECTED')
organic=ob.OBMol(mol)
for i in reversed([a.GetIdx() for a in ob.OBMolAtomIter(organic) if a.IsMetal()]):organic.DeleteAtom(organic.GetAtom(i))
print(ob.OBChargeModel.FindType('gasteiger').ComputeCharges(organic));show('CHARGED');print(c.WriteString(mol).splitlines()[369])
