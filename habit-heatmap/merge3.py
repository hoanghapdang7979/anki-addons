"""Three-way merge of tick sets and of the habit list. No aqt/anki imports.

Inputs are `base` (last state known to be in sync), `local` (what this machine
last wrote) and `remote` (what the collection config holds now, possibly just
replaced by a sync). Additions from either side are kept; a removal made by
either side propagates. This is what lets an un-tick reach the other machine
without ever resurrecting it, while still recovering local changes that a sync
overwrote.
"""

try:
    from .bitmap import Bitmap
    from .habits import Habit
except ImportError:  # pytest: modules are top-level via conftest.py sys.path
    from bitmap import Bitmap
    from habits import Habit


def merge_bitmap(base: Bitmap, local: Bitmap, remote: Bitmap) -> Bitmap:
    b, l, r = base.ticked_ordinals(), local.ticked_ordinals(), remote.ticked_ordinals()
    result = (l & r) | (l - b) | (r - b)
    out = Bitmap()
    for ordinal in result:
        out = out.with_bit(ordinal, True)
    return out


def merge_habits(base: list[Habit], local: list[Habit], remote: list[Habit]) -> list[Habit]:
    """Union by id with removal propagation. Remote order first, then local-only
    additions. If both sides edited the same habit, the remote copy wins."""
    b = {h.id: h for h in base}
    l = {h.id: h for h in local}
    r = {h.id: h for h in remote}
    order = [h.id for h in remote] + [h.id for h in local if h.id not in r]
    merged: list[Habit] = []
    for hid in order:
        if hid in l and hid in r:
            merged.append(r[hid] if r[hid] != b.get(hid) else l[hid])
        elif hid in l:  # only local has it: keep if added locally, drop if remote deleted it
            if hid not in b:
                merged.append(l[hid])
        elif hid not in b:  # only remote has it: keep if added remotely
            merged.append(r[hid])
    return merged
