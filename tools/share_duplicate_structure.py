from database.store import connect
D=connect('data/nilephytodock.sqlite')
s=D.execute('SELECT sdf_path,pdbqt_path,properties FROM compound_structures WHERE compound_id=9').fetchone()
D.execute("UPDATE compound_structures SET sdf_path=?,pdbqt_path=?,properties=?,notes='Verified same PubChem CID and InChIKey as Eucalyptol; shared prepared structure; original Cineole name retained' WHERE compound_id=98",tuple(s));D.commit();D.execute('PRAGMA wal_checkpoint(TRUNCATE)');D.close()
