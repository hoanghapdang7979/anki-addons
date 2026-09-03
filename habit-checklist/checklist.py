"""Pure logic for auto-filling a habit checklist into a note field.

No aqt/anki imports here - keep this module testable without a running
Anki instance (see CLAUDE.md code style: data-only modules stay Qt-free).
`note` only needs dict-like __contains__/__getitem__/__setitem__, so a
plain dict works in tests and anki.notes.Note works at runtime.
"""

from typing import MutableMapping


def build_habit_checklist(habits: list[str]) -> str:
    """Render habits as one "[ ] Name" line per habit, joined by <br>.

    Anki fields are HTML, so <br> (not "\\n") is what actually produces
    separate lines in the Editor/Reviewer.
    """
    return "<br>".join(f"[ ] {habit}" for habit in habits)


def apply_checklist_if_empty(
    note: MutableMapping[str, str], field_name: str, checklist_text: str
) -> bool:
    """Set note[field_name] = checklist_text if the field exists and is empty.

    A field containing only whitespace counts as empty. Never re-renders
    over existing content, even content that looks like an old checklist -
    that would wipe out ticks and per-habit notes the user already wrote.
    Returns True if the note was changed (caller must persist it).
    """
    if field_name not in note:
        return False
    if note[field_name].strip():
        return False
    note[field_name] = checklist_text
    return True
