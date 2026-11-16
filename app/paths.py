"""Read-only bundled resources and writable per-user data are distinct."""
import os
import sys
from pathlib import Path

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
DATA = Path(os.environ.get("NILEPHYTODOCK_DATA", Path(os.environ.get("LOCALAPPDATA", Path.home())) / "NilePhytoDock"))

def resource(*parts):
    return ROOT.joinpath(*parts)

def user_data():
    DATA.mkdir(parents=True, exist_ok=True)
    # Preserve existing installations after the corrected developer attribution.
    # This legacy folder is migration input only, never a branding field.
    legacy=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'I-Mole Lab'/'NilePhytoDock'/'nilephytodock.sqlite'
    destination=DATA/'nilephytodock.sqlite'
    if 'NILEPHYTODOCK_DATA' not in os.environ and not destination.exists() and legacy.exists():
        import sqlite3
        old=sqlite3.connect(legacy);new=sqlite3.connect(destination);old.backup(new);new.close();old.close()
    return DATA

