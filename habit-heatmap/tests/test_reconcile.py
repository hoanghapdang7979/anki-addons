import pytest

from bitmap import Bitmap
from habits import PALETTE, Habit, habits_to_json
from reconcile import reconcile
from shadow import ShadowFile, ShadowState
from store import DATA_PREFIX, HABITS_KEY, Store

T = 739000


class FakeDB:
    def __init__(self, col):
        self.col = col

    def scalar(self, sql, key):
        return -1 if key in self.col.pending else 0


class FakeCol:
    """Config store + the sync flag Anki keeps per row (usn = -1 means unsynced)."""

    def __init__(self):
        self.cfg: dict = {}
        self.pending: set[str] = set()
        self.db = FakeDB(self)

    def get_config(self, key, default=None):
        return self.cfg.get(key, default)

    def set_config(self, key, val):
        self.cfg[key] = val
        self.pending.add(key)

    def remove_config(self, key):
        self.cfg.pop(key, None)

    def all_config(self):
        return dict(self.cfg)

    def mark_synced(self):
        self.pending.clear()


def habit(hid, name="A", archived=False):
    return Habit(hid, name, PALETTE[0], T, archived)


def bits(*days):
    bm = Bitmap()
    for d in days:
        bm = bm.with_bit(T + d, True)
    return bm


@pytest.fixture
def env(tmp_path):
    shadow = ShadowFile(tmp_path / "s.json")
    store = Store(FakeCol(), shadow=shadow)
    return store, shadow


def setup(store, shadow, *, remote, local, base, habits=None, synced=True):
    """remote = config now, local = shadow.bitmaps, base = shadow.base_bitmaps (habit h1)."""
    habits = habits if habits is not None else [habit("h1")]
    store.col.cfg[HABITS_KEY] = habits_to_json(habits)
    if remote is not None:
        store.col.cfg[DATA_PREFIX + "h1"] = remote.to_dict()
    shadow.save(
        ShadowState(
            habits=habits,
            bitmaps={"h1": local},
            base_habits=habits,
            base_bitmaps={"h1": base},
        )
    )
    store.col.pending.clear()
    if not synced:
        store.col.pending.update({HABITS_KEY, DATA_PREFIX + "h1"})


def ticks(bm):
    return bm.ticked_ordinals()


def test_remote_tick_is_adopted_and_becomes_the_new_base(env):
    store, shadow = env
    setup(store, shadow, remote=bits(1, 2), local=bits(1), base=bits(1))
    assert reconcile(store) is False  # nothing had to be written back
    assert ticks(store.bitmap("h1")) == {T + 1, T + 2}
    state = shadow.load()
    assert ticks(state.bitmaps["h1"]) == ticks(state.base_bitmaps["h1"]) == {T + 1, T + 2}


def test_remote_untick_propagates_instead_of_being_resurrected(env):
    store, shadow = env
    setup(store, shadow, remote=bits(1), local=bits(1, 2), base=bits(1, 2))
    reconcile(store)
    assert ticks(store.bitmap("h1")) == {T + 1}
    assert ticks(shadow.load().bitmaps["h1"]) == {T + 1}


def test_local_untick_is_not_undone_by_a_stale_remote_copy(env):
    store, shadow = env
    setup(store, shadow, remote=bits(1, 2), local=bits(1), base=bits(1, 2))
    assert reconcile(store) is True
    assert ticks(store.bitmap("h1")) == {T + 1}
    assert DATA_PREFIX + "h1" in store.col.pending  # rewritten, still needs pushing
    assert ticks(shadow.load().base_bitmaps["h1"]) == {T + 1, T + 2}  # base not advanced yet


def test_local_tick_overwritten_by_a_sync_is_recovered(env):
    store, shadow = env
    setup(store, shadow, remote=bits(1), local=bits(1, 5), base=bits(1))
    assert reconcile(store) is True
    assert ticks(store.bitmap("h1")) == {T + 1, T + 5}


def test_both_sides_added_different_days_are_combined(env):
    store, shadow = env
    setup(store, shadow, remote=bits(1, 3), local=bits(1, 2), base=bits(1))
    reconcile(store)
    assert ticks(store.bitmap("h1")) == {T + 1, T + 2, T + 3}


def test_pending_unsynced_local_change_is_left_alone_and_base_not_advanced(env):
    store, shadow = env
    setup(store, shadow, remote=bits(1, 2), local=bits(1, 2), base=bits(1), synced=False)
    assert reconcile(store) is False
    assert ticks(shadow.load().base_bitmaps["h1"]) == {T + 1}


def test_base_advances_once_the_change_has_been_synced(env):
    store, shadow = env
    setup(store, shadow, remote=bits(1, 2), local=bits(1, 2), base=bits(1), synced=False)
    reconcile(store)
    store.col.mark_synced()  # a later successful sync pushed it
    reconcile(store)
    assert ticks(shadow.load().base_bitmaps["h1"]) == {T + 1, T + 2}


def test_new_device_with_empty_shadow_adopts_downloaded_data(env):
    store, shadow = env
    store.col.cfg[HABITS_KEY] = habits_to_json([habit("h1", "Exercise")])
    store.col.cfg[DATA_PREFIX + "h1"] = bits(0, 1, 2).to_dict()
    reconcile(store)
    assert [h.name for h in store.habits()] == ["Exercise"]
    assert ticks(store.bitmap("h1")) == {T, T + 1, T + 2}
    assert ticks(shadow.load().base_bitmaps["h1"]) == {T, T + 1, T + 2}


def test_wiped_config_is_restored_when_local_has_never_synced_those_ticks(env):
    store, shadow = env
    shadow.save(ShadowState([habit("h1", "Exercise")], {"h1": bits(0, 1, 2)}))
    reconcile(store)
    assert [h.name for h in store.habits()] == ["Exercise"]
    assert ticks(store.bitmap("h1")) == {T, T + 1, T + 2}


def test_habit_deleted_remotely_propagates(env):
    store, shadow = env
    setup(store, shadow, remote=bits(1), local=bits(1), base=bits(1), habits=[habit("h1"), habit("h2")])
    store.col.cfg[HABITS_KEY] = habits_to_json([habit("h2")])  # server list lost h1
    reconcile(store)
    assert [h.id for h in store.habits()] == ["h2"]
    assert [h.id for h in shadow.load().habits] == ["h2"]


def test_habit_deleted_locally_is_not_resurrected_by_a_stale_remote_list(env):
    store, shadow = env
    setup(store, shadow, remote=bits(1), local=bits(1), base=bits(1), habits=[habit("h1"), habit("h2")])
    shadow.update(lambda s: setattr(s, "habits", [habit("h2")]))  # user deleted h1 here
    reconcile(store)
    assert [h.id for h in store.habits()] == ["h2"]


def test_remote_rename_is_adopted(env):
    store, shadow = env
    setup(store, shadow, remote=bits(1), local=bits(1), base=bits(1), habits=[habit("h1", "Old")])
    store.col.cfg[HABITS_KEY] = habits_to_json([habit("h1", "New")])
    reconcile(store)
    assert store.habits()[0].name == "New"


def test_corrupt_config_bitmap_is_left_untouched(env):
    store, shadow = env
    setup(store, shadow, remote=bits(), local=bits(1), base=bits())
    bad = {"epoch": T, "bits": "!!!"}
    store.col.cfg[DATA_PREFIX + "h1"] = bad
    reconcile(store)
    assert store.col.cfg[DATA_PREFIX + "h1"] == bad
    assert ticks(shadow.load().bitmaps["h1"]) == {T + 1}


def test_corrupt_habit_list_changes_nothing(env):
    store, shadow = env
    store.col.cfg[HABITS_KEY] = "garbage"
    shadow.save(ShadowState([habit("h1")], {"h1": bits(1)}))
    assert reconcile(store) is False
    assert store.col.cfg[HABITS_KEY] == "garbage"
    assert DATA_PREFIX + "h1" not in store.col.cfg


def test_data_without_a_habit_entry_is_never_deleted(env):
    store, shadow = env
    setup(store, shadow, remote=bits(0), local=bits(0), base=bits(0))
    store.col.cfg[DATA_PREFIX + "ghost"] = bits(4).to_dict()
    reconcile(store)
    assert DATA_PREFIX + "ghost" in store.col.cfg


def test_reconcile_is_idempotent(env):
    store, shadow = env
    setup(store, shadow, remote=bits(1, 3), local=bits(1, 2), base=bits(1))
    reconcile(store)
    snapshot = dict(store.col.cfg), ticks(shadow.load().bitmaps["h1"])
    store.col.mark_synced()
    assert reconcile(store) is False
    assert (dict(store.col.cfg), ticks(shadow.load().bitmaps["h1"])) == snapshot


def test_unreadable_sync_state_is_treated_as_pending_and_never_advances_base(env):
    store, shadow = env
    setup(store, shadow, remote=bits(1, 2), local=bits(1, 2), base=bits(1))
    store.col.db = None  # is_pending() cannot read usn
    reconcile(store)
    assert ticks(shadow.load().base_bitmaps["h1"]) == {T + 1}


def test_no_shadow_is_a_noop():
    store = Store(FakeCol())
    store.col.cfg[HABITS_KEY] = habits_to_json([habit("h1")])
    before = dict(store.col.cfg)
    assert reconcile(store) is False
    assert store.col.cfg == before


from reconcile import should_followup  # noqa: E402


def test_followup_only_when_reconcile_wrote_something():
    assert should_followup(wrote=False, last_followup_at=None, now=1000.0) is False
    assert should_followup(wrote=True, last_followup_at=None, now=1000.0) is True


def test_followup_is_rate_limited_so_it_can_never_loop():
    assert should_followup(wrote=True, last_followup_at=1000.0, now=1030.0) is False
    assert should_followup(wrote=True, last_followup_at=1000.0, now=1060.0) is True
