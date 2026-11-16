from rdkit import Chem,RDLogger
from pathlib import Path
RDLogger.DisableLog('rdApp.error')
m=Chem.SDMolSupplier('data/validation/science/3PTB/prepared.sdf',removeHs=False,sanitize=False)[0]
labels=[l for l in Path('data/validation/science/3PTB/prepared.pdb').read_text().splitlines() if l.startswith(('ATOM  ','HETATM'))]
ps=Chem.DetectChemistryProblems(m);print('problems',len(ps))
for problem in ps[:10]:
 i=problem.GetAtomIdx();a=m.GetAtomWithIdx(i);print(problem.Message(),labels[i]);print([(n.GetIdx(),n.GetSymbol(),str(m.GetBondBetweenAtoms(i,n.GetIdx()).GetBondType())) for n in a.GetNeighbors()])
