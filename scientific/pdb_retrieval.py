"""Validated coordinate downloads; never substitute an error page for a structure."""
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def normalize_id(value):
    value = value.strip()
    if value.lower().startswith(('https://', 'http://')):
        parsed = urlparse(value)
        if parsed.hostname not in {'www.rcsb.org', 'rcsb.org', 'files.rcsb.org', 'doi.org', 'www.ebi.ac.uk'}:
            raise ValueError('Paste a PDB ID or an RCSB / PDBe structure link.')
        parts = parsed.path.rstrip('/').split('/')
        if parsed.hostname == 'doi.org' and len(parts) >= 3:
            value = parts[-2].removeprefix('pdb').removeprefix('PDB')
        else:
            value = parts[-1].split('.')[0]
    value = re.sub(r'^(?:PDB\s*:\s*)', '', value, flags=re.I).upper()
    if re.fullmatch(r'[A-Z0-9]{4}', value):
        return value
    if re.fullmatch(r'PDB_[A-Z0-9]{8}', value):
        return value[8:] if value.startswith('PDB_0000') else value.lower()
    raise ValueError('Enter a four-character PDB ID (for example 3PTB), an extended pdb_ ID, or a structure link.')


def retrieve(value, folder, emit=None, session=None):
    ident = normalize_id(value)
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    own_session = session is None
    session = session or requests.Session()
    if own_session:
        session.mount('https://', HTTPAdapter(max_retries=Retry(total=2, backoff_factor=.4, status_forcelist=[429, 500, 502, 503, 504])))
    candidates = []
    if len(ident) == 4:
        candidates.append((f'https://files.rcsb.org/download/{ident}.pdb', '.pdb'))
    candidates.append((f'https://files.rcsb.org/download/{ident}.cif', '.cif'))
    if len(ident) == 4:
        candidates.append((f'https://www.ebi.ac.uk/pdbe/entry-files/download/{ident.lower()}.cif', '.cif'))
    failures = []; missing = 0; last_error = None
    try:
        for url, suffix in candidates:
            temporary = None
            try:
                if emit: emit('Retrieving '+ident+' coordinates…', 0, 1)
                response = session.get(url, timeout=(10, 45))
                if response.status_code == 404:
                    missing += 1; continue
                response.raise_for_status()
                text = response.text
                if not (text.lstrip().startswith('data_') if suffix == '.cif' else any(line.startswith(('ATOM  ', 'HETATM')) for line in text.splitlines())):
                    raise ValueError('The server response contains no coordinate records')
                with tempfile.NamedTemporaryFile(dir=folder, suffix=suffix, delete=False) as file:
                    temporary = Path(file.name); file.write(text.encode('utf-8'))
                from scientific.proteins import inspect
                try: metadata = inspect(temporary)
                except Exception as error:
                    raise ValueError('Downloaded coordinates could not be parsed: '+str(error)) from error
                if not metadata['atoms']: raise ValueError('No structural atoms found')
                destination = folder / (ident+suffix)
                os.replace(temporary, destination); temporary = None
                if emit: emit('Retrieved '+ident, 1, 1)
                return str(destination)
            except (requests.RequestException, ValueError, OSError) as error:
                failures.append(str(error)); last_error = error
            finally:
                if temporary is not None: temporary.unlink(missing_ok=True)
    finally:
        if own_session: session.close()
    if missing == len(candidates):
        raise ValueError(f'PDB entry {ident} was not found. Check the identifier and whether the entry is released.')
    raise ValueError('Could not retrieve '+ident+'. Check the internet connection or import a downloaded PDB/mmCIF file. '+ '; '.join(failures)[-600:]) from last_error
