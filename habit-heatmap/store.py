"""Reads/writes habits and tick bitmaps in the collection config.

`col` is duck-typed (get_config/set_config/remove_config/all_config) so this
module needs no aqt/anki import and is unit-testable with a fake.
Config rides AnkiWeb sync, so values are kept tiny (see bitmap.py).
"""

import logging
from datetime import date

try:
    from .bitmap import Bitmap, toggle_today as toggle_bitmap_today
    from .habits import Habit, active, habits_from_json, habits_to_json
except ImportError:  # pytest: modules are top-level via conftest.py sys.path
    from bitmap import Bitmap, toggle_today as toggle_bitmap_today
    from habits import Habit, active, habits_from_json, habits_to_json

logger = logging.getLogger(__name__)

HABITS_KEY = "habitHeatmap.habits"
DATA_PREFIX = "habitHeatmap.d."


class Store:
    def __init__(self, col, shadow=None) -> None:
        self.col = col
        self.shadow = shadow  # ShadowFile-like (update(fn)); best-effort local backup

    def _mirror(self, fn) -> None:
        """Apply `fn(state)` to the shadow. A failing backup must never block the user."""
        if self.shadow is None:
            return
        try:
            self.shadow.update(fn)
        except OSError:
            logger.exception("could not update the local shadow backup")

    def habits(self) -> list[Habit]:
        """Raises ValueError on corrupt data rather than returning an empty list
        that a later save would write over the recoverable original."""
        return habits_from_json(self.col.get_config(HABITS_KEY))

    def save_habits(self, habits: list[Habit]) -> None:
        self.col.set_config(HABITS_KEY, habits_to_json(habits))
        self._mirror(lambda state: setattr(state, "habits", list(habits)))

    def bitmap(self, habit_id: str) -> Bitmap:
        return Bitmap.from_dict(self.col.get_config(DATA_PREFIX + habit_id))

    def save_bitmap(self, habit_id: str, bitmap: Bitmap) -> None:
        self.col.set_config(DATA_PREFIX + habit_id, bitmap.to_dict())

    def toggle_today(self, habit_id: str, today: date) -> Bitmap:
        """Flip today's tick for an existing, non-archived habit. Raises KeyError
        for unknown/archived ids, ValueError for a corrupt stored bitmap (left untouched)."""
        if habit_id not in {h.id for h in active(self.habits())}:
            raise KeyError(habit_id)
        updated = toggle_bitmap_today(self.bitmap(habit_id), today)
        self.save_bitmap(habit_id, updated)
        self._mirror(lambda state: state.bitmaps.__setitem__(habit_id, updated))
        return updated

    def delete_data(self, habit_id: str) -> None:
        """Permanent deletion. The local shadow forgets the habit but keeps its base
        entry, which is how the merge later knows this was a deliberate removal."""
        self.col.remove_config(DATA_PREFIX + habit_id)

        def forget(state) -> None:
            state.bitmaps.pop(habit_id, None)
            state.habits = [h for h in state.habits if h.id != habit_id]

        self._mirror(forget)

    def is_pending(self, key: str) -> bool:
        """True unless the config row is confirmed synced. Anki marks a row usn=-1
        when written and sets the server usn after a successful sync; a failed sync
        leaves it -1. Treat anything unreadable as pending (the safe answer)."""
        try:
            usn = self.col.db.scalar("select usn from config where key = ?", key)
        except Exception:
            logger.warning("could not read sync state of %s", key, exc_info=True)
            return True
        return usn is None or usn == -1

    def stored_ids(self) -> set[str]:
        return {
            key[len(DATA_PREFIX) :]
            for key in self.col.all_config()
            if key.startswith(DATA_PREFIX)
        }
