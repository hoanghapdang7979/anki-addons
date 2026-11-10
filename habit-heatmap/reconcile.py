"""Merge the collection config with the local shadow after a sync (or on
profile open). No aqt/anki imports.

Why: Anki replaces the whole config with whichever side changed last, so a
sync can silently drop this machine's un-synced ticks - or bring back an
older copy. A three-way merge (base = last synced, local = shadow, remote =
config now) recovers local additions/removals and lets removals from the
other machine propagate. The base only advances for values that are confirmed
synced (config row usn != -1); a failed sync therefore never advances it.

Never deletes data: a key without a habit entry is ignored, not removed.
"""

import logging

try:
    from .bitmap import Bitmap
    from .habits import habits_to_json
    from .merge3 import merge_bitmap, merge_habits
    from .store import DATA_PREFIX, HABITS_KEY, Store
except ImportError:  # pytest: modules are top-level via conftest.py sys.path
    from bitmap import Bitmap
    from habits import habits_to_json
    from merge3 import merge_bitmap, merge_habits
    from store import DATA_PREFIX, HABITS_KEY, Store

logger = logging.getLogger(__name__)


def reconcile(store: Store) -> bool:
    """Returns True if it wrote anything back to the config (so it still needs a sync)."""
    if store.shadow is None:
        return False
    state = store.shadow.load()
    try:
        remote_habits = store.habits()
    except ValueError:
        logger.exception("habit list unreadable; reconcile skipped, nothing changed")
        return False

    wrote = False
    merged = merge_habits(state.base_habits, state.habits, remote_habits)
    list_changed = merged != remote_habits
    if list_changed:
        store.col.set_config(HABITS_KEY, habits_to_json(merged))
        wrote = True
    if not list_changed and not store.is_pending(HABITS_KEY):
        state.base_habits = list(merged)
    state.habits = merged

    kept = {h.id for h in merged}
    for habit in merged:
        key = DATA_PREFIX + habit.id
        try:
            remote = store.bitmap(habit.id)
        except ValueError:
            logger.exception("bitmap for %s unreadable; left untouched", habit.id)
            continue
        result = merge_bitmap(
            state.base_bitmaps.get(habit.id, Bitmap()),
            state.bitmaps.get(habit.id, Bitmap()),
            remote,
        )
        changed = result != remote
        if changed:
            store.col.set_config(key, result.to_dict())
            wrote = True
        if not changed and not store.is_pending(key):
            state.base_bitmaps[habit.id] = result
        state.bitmaps[habit.id] = result

    # Forget shadow entries of habits that are gone (the config data key, if any, is left alone).
    for stale in set(state.bitmaps) - kept:
        del state.bitmaps[stale]
    for stale in set(state.base_bitmaps) - kept:
        del state.base_bitmaps[stale]

    store.shadow.save(state)
    return wrote


FOLLOWUP_MIN_GAP_SECONDS = 60


def should_followup(wrote: bool, last_followup_at: float | None, now: float) -> bool:
    """After a reconcile that wrote the merged config back, one more sync pushes it.
    Anki's config sync only lets a machine's change win if no other machine synced
    since that change was written, so the follow-up must come right away. Rate
    limited so two machines can never trigger each other in a loop."""
    if not wrote:
        return False
    return last_followup_at is None or now - last_followup_at >= FOLLOWUP_MIN_GAP_SECONDS
