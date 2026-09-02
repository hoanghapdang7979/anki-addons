"""Pure logic for auto-filling today's date into a note field.

No aqt/anki imports here - keep this module testable without a running
Anki instance (see CLAUDE.md code style: data-only modules stay Qt-free).
`note` only needs dict-like __contains__/__getitem__/__setitem__, so a
plain dict works in tests and anki.notes.Note works at runtime.
"""

from datetime import date
from typing import MutableMapping


def today_iso(today: date | None = None) -> str:
    """Return today's date as YYYY-MM-DD. Pass `today` explicitly in tests."""
    return (today or date.today()).isoformat()


def apply_date_if_empty(
    note: MutableMapping[str, str], field_name: str, date_str: str
) -> bool:
    """Set note[field_name] = date_str if the field exists and is empty.

    A field containing only whitespace counts as empty. Returns True if
    the note was changed (caller must persist it), False otherwise.
    """
    if field_name not in note:
        return False
    if note[field_name].strip():
        return False
    note[field_name] = date_str
    return True
