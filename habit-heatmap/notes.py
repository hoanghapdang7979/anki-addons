"""Per-day notes: cleaning, size limits, date rules and the three-way merge used
by sync. No aqt/anki imports.

A habit's notes are a dict {"<date ordinal>": "text"} (string keys because the
config is JSON). A day without a note is simply absent.
"""

import re
from datetime import date

MAX_NOTE_CHARS = 500
MAX_KEY_CHARS = 200_000  # serialised size cap for one habit's notes key

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class NoteStorageFull(ValueError):
    """The habit's notes key would exceed MAX_KEY_CHARS."""


def clean_note(text: str) -> tuple[str, bool]:
    """Normalise a note typed by the user. Returns (cleaned, was_truncated)."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    text = _CONTROL_RE.sub("", text).strip()
    if len(text) > MAX_NOTE_CHARS:
        return text[:MAX_NOTE_CHARS].rstrip(), True
    return text, False


def merge_notes(
    base: dict[str, str], local: dict[str, str], remote: dict[str, str]
) -> dict[str, str]:
    """Three-way merge per day: take whichever side changed against `base`; if both
    changed the same day the remote copy wins (Anki already picked a winner for the
    config block, so we stay consistent with it)."""
    merged: dict[str, str] = {}
    for day in set(base) | set(local) | set(remote):
        b, l, r = base.get(day), local.get(day), remote.get(day)
        value = l if r == b else r
        if value is not None:
            merged[day] = value
    return merged


def note_day_ok(day: date, created: int, today: date) -> bool:
    """A note may be written for any day from the habit's creation day up to today."""
    return created <= day.toordinal() <= today.toordinal()


_NOTE_ARG_RE = re.compile(r"([A-Za-z0-9_-]+):(\d{4}-\d{2}-\d{2})")


def parse_note_arg(arg: str) -> tuple[str, date] | None:
    """Parse "<habit_id>:<YYYY-MM-DD>" from the page. None if it is anything else."""
    match = _NOTE_ARG_RE.fullmatch(arg)
    if match is None:
        return None
    try:
        return match.group(1), date.fromisoformat(match.group(2))
    except ValueError:
        return None
