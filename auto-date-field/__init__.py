import logging

# Import order matters here: several anki submodules (anki.notes, anki.hooks,
# anki.cards...) hit a circular import in anki 26.8.1 if anki.collection
# hasn't been fully imported yet. Anki's own bootstrap always imports
# anki.collection early (it builds mw.col before any add-on loads), so this
# never surfaces in a real Anki session - only when these modules are
# imported in isolation (e.g. under pytest, or a bare `python -c`).
# Importing it first here sidesteps the cycle without patching the anki
# package. See inline-field-editor/__init__.py for the same fix.
import anki.collection  # noqa: F401
from anki.notes import Note
from aqt import gui_hooks, mw

from .date_fill import apply_date_if_empty, today_iso

logger = logging.getLogger(__name__)

DEFAULT_FIELD_NAME = "Date"


def _field_name() -> str:
    config = mw.addonManager.getConfig(__name__) or {}
    return config.get("field_name", DEFAULT_FIELD_NAME)


def _on_note_added(note: Note) -> None:
    field_name = _field_name()
    if apply_date_if_empty(note, field_name, today_iso()):
        mw.col.update_note(note)


gui_hooks.add_cards_did_add_note.append(_on_note_added)

logger.info("Auto Date Field loaded")
