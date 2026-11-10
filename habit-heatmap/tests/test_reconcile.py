import pytest

from bitmap import Bitmap
from habits import PALETTE, Habit, habits_to_json
from reconcile import reconcile
from shadow import ShadowFile, ShadowState
from store import DATA_PREFIX, HABITS_KEY, Store

T = 739000


class FakeCol:
    def __init__(self):
        self.cfg: dict = {}

    def get_config(self, key, default=None):
        return self.cfg.get(key, default)

    def set_config(self, key, val):
        self.cfg[key] = val

    def remove_config(self, key):
        self.cfg.pop(key, None)

    def all_config(self):
        return dict(self.cfg)


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
    return Store(FakeCol(), shadow=shadow), shadow


def put_cfg(store, habits, data):
    store.col.cfg[HABITS_KEY] = habits_to_json(habits)
    for hid, bm in data.items():
        store.col.cfg[DATA_PREFIX + hid] = bm.to_dict()


def test_union_restores_ticks_missing_from_config(env):
    store, shadow = env
    put_cfg(store, [habit("h1")], {"h1": bits(0, 1)})
    shadow.save(ShadowState([habit("h1")], set(), {"h1": bits(1, 2, 3)}))
    reconcile(store)
    assert store.bitmap("h1").ticked_ordinals() == {T, T + 1, T + 2, T + 3}
    assert shadow.load().bitmaps["h1"].ticked_ordinals() == {T, T + 1, T + 2, T + 3}


def test_config_ticks_missing_from_shadow_are_adopted_into_shadow(env):
    store, shadow = env
    put_cfg(store, [habit("h1")], {"h1": bits(5)})
    reconcile(store)
    assert shadow.load().bitmaps["h1"].ticked_ordinals() == {T + 5}


def test_wiped_config_is_restored_from_shadow(env):
    store, shadow = env
    shadow.save(ShadowState([habit("h1", "Exercise")], set(), {"h1": bits(0, 1, 2)}))
    reconcile(store)  # e.g. after "Download from AnkiWeb" replaced the config
    assert [h.name for h in store.habits()] == ["Exercise"]
    assert store.bitmap("h1").ticked_ordinals() == {T, T + 1, T + 2}


def test_tombstoned_habit_is_not_resurrected_from_shadow_or_stale_config(env):
    store, shadow = env
    put_cfg(store, [habit("h1"), habit("h2")], {"h2": bits(0)})  # stale list still has h1
    shadow.save(ShadowState([habit("h1"), habit("h2")], {"h1"}, {"h2": bits(0)}))
    reconcile(store)
    assert [h.id for h in store.habits()] == ["h2"]


def test_archived_habits_are_reconciled_too(env):
    store, shadow = env
    put_cfg(store, [habit("h1", archived=True)], {"h1": bits(0)})
    shadow.save(ShadowState([habit("h1", archived=True)], set(), {"h1": bits(7)}))
    reconcile(store)
    assert store.bitmap("h1").ticked_ordinals() == {T, T + 7}


def test_corrupt_config_bitmap_is_left_untouched(env):
    store, shadow = env
    put_cfg(store, [habit("h1")], {})
    bad = {"epoch": T, "bits": "!!!"}
    store.col.cfg[DATA_PREFIX + "h1"] = bad
    shadow.save(ShadowState([habit("h1")], set(), {"h1": bits(1)}))
    reconcile(store)
    assert store.col.cfg[DATA_PREFIX + "h1"] == bad
    assert shadow.load().bitmaps["h1"].ticked_ordinals() == {T + 1}


def test_corrupt_habit_list_changes_nothing(env):
    store, shadow = env
    store.col.cfg[HABITS_KEY] = "garbage"
    shadow.save(ShadowState([habit("h1")], set(), {"h1": bits(1)}))
    reconcile(store)
    assert store.col.cfg[HABITS_KEY] == "garbage"
    assert DATA_PREFIX + "h1" not in store.col.cfg


def test_data_without_a_habit_entry_is_never_deleted(env):
    store, shadow = env
    put_cfg(store, [habit("h1")], {"h1": bits(0), "ghost": bits(4)})
    reconcile(store)
    assert DATA_PREFIX + "ghost" in store.col.cfg


def test_reconcile_is_idempotent(env):
    store, shadow = env
    put_cfg(store, [habit("h1")], {"h1": bits(0)})
    shadow.save(ShadowState([habit("h1")], set(), {"h1": bits(2)}))
    reconcile(store)
    snapshot = dict(store.col.cfg), shadow.load().bitmaps["h1"].ticked_ordinals()
    reconcile(store)
    assert (dict(store.col.cfg), shadow.load().bitmaps["h1"].ticked_ordinals()) == snapshot


def test_no_shadow_is_a_noop(tmp_path):
    store = Store(FakeCol())
    put_cfg(store, [habit("h1")], {"h1": bits(0)})
    before = dict(store.col.cfg)
    reconcile(store)
    assert store.col.cfg == before
