from openbabel import openbabel as ob
c=ob.OBConversion();c.SetInFormat('pdb');m=ob.OBMol();c.ReadFile(m,'data/validation/science/3PTB/selected.pdb');m.SetChainsPerceived(True)
labels={a.GetIdx():(a.GetResidue().GetName(),a.GetResidue().GetNumString(),a.GetResidue().GetAtomID(a)) for a in ob.OBMolAtomIter(m)}
for a in ob.OBMolAtomIter(m):
 if a.IsMetal(): a.SetFormalCharge(2);a.SetImplicitHCount(0)
m.AddHydrogens(False,True,7.4);m.SetChainsPerceived(True)
for a in ob.OBMolAtomIter(m):
 if a.IsMetal(): print('after',a.GetAtomicNum(),a.GetType(),a.GetResidue().GetName(),a.GetResidue().GetNumAtoms(),a.GetExplicitDegree())
for a in list(ob.OBMolAtomIter(m))[:8]:print(a.GetIdx(),a.GetResidue().GetName(),a.GetResidue().GetNumString(),labels.get(a.GetIdx()))
