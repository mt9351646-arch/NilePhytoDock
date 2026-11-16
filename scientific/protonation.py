"""Explicit standard-residue protonation approximation, not a site pKa solver."""
from rdkit import Chem

def assign(mol,ph):
    mol=Chem.RWMol(mol)
    residues={}
    for a in mol.GetAtoms():
        p=a.GetPDBResidueInfo()
        if p:residues.setdefault((p.GetChainId(),p.GetResidueNumber(),p.GetInsertionCode(),p.GetResidueName().strip()),{})[p.GetName().strip()]=a.GetIdx()
    def charge(atoms,name,value):
        if name in atoms:mol.GetAtomWithIdx(atoms[name]).SetFormalCharge(value)
    for (_,_,_,res),atoms in residues.items():
        if res in {'ASP','GLU'}:
            oxy=['OD1','OD2'] if res=='ASP' else ['OE1','OE2'];carbon='CG' if res=='ASP' else 'CD';pka=3.9 if res=='ASP' else 4.2
            if all(x in atoms for x in oxy+[carbon]):
                # The single-bond oxygen carries the negative charge.
                for name in oxy:
                    bond=mol.GetBondBetweenAtoms(atoms[carbon],atoms[name]);charge(atoms,name,-1 if ph>pka and bond.GetBondType()==Chem.BondType.SINGLE else 0)
        elif res=='LYS':charge(atoms,'NZ',1 if ph<10.5 else 0)
        elif res=='ARG' and 'CZ' in atoms:
            for name in ['NE','NH1','NH2']:
                if name in atoms:
                    bond=mol.GetBondBetweenAtoms(atoms['CZ'],atoms[name]);charge(atoms,name,1 if ph<12.5 and bond.GetBondType()==Chem.BondType.DOUBLE else 0)
        elif res=='HIS' and ph<6.0:
            for name in ['ND1','NE2']:
                if name in atoms:
                    a=mol.GetAtomWithIdx(atoms[name])
                    if a.GetIsAromatic() and a.GetTotalNumHs()==0:a.SetFormalCharge(1);a.SetNumExplicitHs(1)
        elif res=='CYS' and 'SG' in atoms:
            atom=mol.GetAtomWithIdx(atoms['SG'])
            if atom.GetDegree()==1:atom.SetFormalCharge(-1 if ph>8.3 else 0)
        elif res=='TYR':charge(atoms,'OH',-1 if ph>10.1 else 0)
        # Recognize free termini from the covalent graph, not residue numbering.
        if res in {'ALA','ARG','ASN','ASP','CYS','GLN','GLU','GLY','HIS','ILE','LEU','LYS','MET','PHE','PRO','SER','THR','TRP','TYR','VAL'} and 'N' in atoms:
            n=mol.GetAtomWithIdx(atoms['N'])
            previous=[a for a in n.GetNeighbors() if a.GetPDBResidueInfo() and a.GetPDBResidueInfo().GetName().strip()=='C']
            if not previous:n.SetFormalCharge(1 if ph<8.0 else 0)
        if 'OXT' in atoms:charge(atoms,'OXT',-1 if ph>3.1 else 0)
    result=mol.GetMol();Chem.SanitizeMol(result)
    return Chem.AddHs(result,addCoords=True)
