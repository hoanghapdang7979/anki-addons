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
    """Union by id with removal propagation. If both sides edited the same habit,
    the remote copy wins.

    Order (drag-to-reorder is a priority list, so it must survive sync): if the
    remote side did not reorder the habits it already shared with `base`, keep the
    local order; otherwise use the remote order. Habits only the other side has
    are appended after.
    """
    b = {h.id: h for h in base}
    l = {h.id: h for h in local}
    r = {h.id: h for h in remote}
    chosen: dict[str, Habit] = {}
    for hid in [h.id for h in remote] + [h.id for h in local if h.id not in r]:
        if hid in l and hid in r:
            chosen[hid] = r[hid] if r[hid] != b.get(hid) else l[hid]
        elif hid in l:  # only local has it: keep if added locally, drop if remote deleted it
            if hid not in b:
                chosen[hid] = l[hid]
        elif hid not in b:  # only remote has it: keep if added remotely
            chosen[hid] = r[hid]

    base_order = [h.id for h in base if h.id in chosen]
    remote_shared = [h.id for h in remote if h.id in chosen and h.id in b]
    # With no shared base yet (first sync) "the remote order did not change" is meaningless,
    # so only trust the local order once there is a base to compare the remote against.
    remote_unchanged = bool(base_order) and remote_shared == [i for i in base_order if i in r]
    primary = local if remote_unchanged else remote
    order = [h.id for h in primary if h.id in chosen]
    order += [h.id for h in remote if h.id in chosen and h.id not in order]
    order += [h.id for h in local if h.id in chosen and h.id not in order]
    return [chosen[hid] for hid in order]
