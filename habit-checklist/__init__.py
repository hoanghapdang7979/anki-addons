import logging

# Import order matters here: several anki submodules (anki.notes, anki.hooks,
# anki.cards...) hit a circular import in anki 26.8.1 if anki.collection
# hasn't been fully imported yet. Anki's own bootstrap always imports
# anki.collection early (it builds mw.col before any add-on loads), so this
# never surfaces in a real Anki session - only when these modules are
# imported in isolation (e.g. under pytest, or a bare `python -c`).
# Importing it first here sidesteps the cycle without patching the anki
# package. Same fix as auto-date-field/__init__.py and
# inline-field-editor/__init__.py.
import anki.collection  # noqa: F401
from anki.notes import Note
from aqt import gui_hooks, mw

from .checklist import apply_checklist_if_empty, build_habit_checklist

logger = logging.getLogger(__name__)

DEFAULT_FIELD_NAME = "Habits"
DEFAULT_HABITS: list[str] = []


def _config() -> tuple[str, list[str]]:
    config = mw.addonManager.getConfig(__name__) or {}
    field_name = config.get("field_name", DEFAULT_FIELD_NAME)
    habits = config.get("habits", DEFAULT_HABITS)
    return field_name, habits


def _on_note_added(note: Note) -> None:
    field_name, habits = _config()
    checklist_text = build_habit_checklist(habits)
    if apply_checklist_if_empty(note, field_name, checklist_text):
        mw.col.update_note(note)


gui_hooks.add_cards_did_add_note.append(_on_note_added)

logger.info("Habit Checklist loaded")
