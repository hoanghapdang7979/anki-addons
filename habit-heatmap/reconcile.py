"""Merge the collection config with the local shadow: ticks are a grow-only
set, so a union can never lose a tick. Run on profile open and after sync.
No aqt/anki imports.

Deliberately never deletes anything: data without a habit entry is ignored,
not removed, so a stale habit list arriving through sync cannot cost anyone
their history. Only an explicit "Delete forever" (Store.delete_data) removes data.
"""

import logging

try:
    from .bitmap import Bitmap, union
    from .habits import habits_to_json
    from .store import DATA_PREFIX, HABITS_KEY, Store
except ImportError:  # pytest: modules are top-level via conftest.py sys.path
    from bitmap import Bitmap, union
    from habits import habits_to_json
    from store import DATA_PREFIX, HABITS_KEY, Store

logger = logging.getLogger(__name__)


def reconcile(store: Store) -> None:
    if store.shadow is None:
        return
    state = store.shadow.load()
    try:
        config_habits = store.habits()
    except ValueError:
        logger.exception("habit list unreadable; reconcile skipped, nothing changed")
        return

    config_ids = {h.id for h in config_habits}
    merged = [h for h in config_habits if h.id not in state.deleted] + [
        h for h in state.habits if h.id not in config_ids and h.id not in state.deleted
    ]
    if merged != config_habits:
        store.col.set_config(HABITS_KEY, habits_to_json(merged))

    for habit in merged:
        try:
            in_config = store.bitmap(habit.id)
        except ValueError:
            logger.exception("bitmap for %s unreadable; left untouched", habit.id)
            continue
        combined = union(in_config, state.bitmaps.get(habit.id, Bitmap()))
        if combined != in_config:
            store.col.set_config(DATA_PREFIX + habit.id, combined.to_dict())
        state.bitmaps[habit.id] = combined

    state.habits = merged
    store.shadow.save(state)
