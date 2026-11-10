"""Builds the Store for the currently open profile (collection + that
profile's own shadow file). Touches aqt."""

from pathlib import Path

import aqt

from .shadow import ShadowFile, shadow_filename
from .store import Store

# user_files/ is preserved by Anki across add-on updates, but is shared by all
# profiles on this machine - hence one shadow file per profile name.
_USER_FILES = Path(__file__).resolve().parent / "user_files"


def make_store() -> Store:
    path = _USER_FILES / shadow_filename(aqt.mw.pm.name)
    return Store(aqt.mw.col, shadow=ShadowFile(path))
