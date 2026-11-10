"""Per-profile local backup of habits and tick bitmaps (a "shadow" of what the
collection config should contain). Lets us restore ticks if a sync or a full
download overwrites the config with older data. No aqt/anki imports.

NOTE: an add-on's user_files/ folder is shared by every Anki profile on the
machine, so callers must give each profile its own file.
"""

import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

try:
    from .bitmap import Bitmap
    from .habits import Habit, habits_from_json, habits_to_json
except ImportError:  # pytest: modules are top-level via conftest.py sys.path
    from bitmap import Bitmap
    from habits import Habit, habits_from_json, habits_to_json

logger = logging.getLogger(__name__)


@dataclass
class ShadowState:
    """`habits`/`bitmaps` are what this machine last wrote (local). `base_*` are
    the last values known to be in sync with the server, so a three-way merge
    can tell "removed on one side" from "never had it"."""

    habits: list[Habit] = field(default_factory=list)
    bitmaps: dict[str, Bitmap] = field(default_factory=dict)
    base_habits: list[Habit] = field(default_factory=list)
    base_bitmaps: dict[str, Bitmap] = field(default_factory=dict)
    notes: dict[str, dict[str, str]] = field(default_factory=dict)
    base_notes: dict[str, dict[str, str]] = field(default_factory=dict)


def _notes_from_json(raw) -> dict[str, dict[str, str]]:
    if not raw:
        return {}
    return {
        str(hid): {str(day): str(text) for day, text in notes.items()}
        for hid, notes in raw.items()
    }


class ShadowFile:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def load(self) -> ShadowState:
        if not self.path.exists():
            return ShadowState()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return ShadowState(
                habits=habits_from_json(raw.get("habits")),
                bitmaps={k: Bitmap.from_dict(v) for k, v in raw.get("bitmaps", {}).items()},
                base_habits=habits_from_json(raw.get("base_habits")),
                base_bitmaps={
                    k: Bitmap.from_dict(v) for k, v in raw.get("base_bitmaps", {}).items()
                },
                notes=_notes_from_json(raw.get("notes")),
                base_notes=_notes_from_json(raw.get("base_notes")),
            )  # an old file's "deleted" tombstones are ignored
        except (ValueError, AttributeError, TypeError):
            corrupt = self.path.with_name(self.path.name + ".corrupt")
            logger.exception("shadow file unreadable; moved to %s", corrupt)
            os.replace(self.path, corrupt)
            return ShadowState()

    def save(self, state: ShadowState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "habits": habits_to_json(state.habits),
            "bitmaps": {k: v.to_dict() for k, v in state.bitmaps.items()},
            "base_habits": habits_to_json(state.base_habits),
            "base_bitmaps": {k: v.to_dict() for k, v in state.base_bitmaps.items()},
            "notes": state.notes,
            "base_notes": state.base_notes,
        }
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        os.replace(tmp, self.path)

    def update(self, fn: Callable[[ShadowState], None]) -> None:
        state = self.load()
        fn(state)
        self.save(state)


def shadow_filename(profile_name: str | None) -> str:
    """File name for one profile's shadow. A short hash of the real name keeps
    names that sanitise alike ("a b" vs "a_b") apart."""
    import hashlib
    import re

    name = profile_name or "default"
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", name)[:40]
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    return f"shadow-{safe}-{digest}.json"
