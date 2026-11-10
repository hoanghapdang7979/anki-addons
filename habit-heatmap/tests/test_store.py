from datetime import date

import pytest

from bitmap import Bitmap
from habits import PALETTE, add_habit, archive_habit
from store import DATA_PREFIX, HABITS_KEY, Store

TODAY = date(2026, 11, 11)
T = TODAY.toordinal()


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


@pytest.fixture
def store():
    return Store(FakeCol())


def test_fresh_store_has_no_habits(store):
    assert store.habits() == []


def test_save_and_load_habits_roundtrip(store):
    habits = add_habit([], "Exercise", PALETTE[0], T, id_factory=lambda: "h1")
    store.save_habits(habits)
    assert store.habits() == habits
    assert HABITS_KEY in store.col.cfg


def test_corrupt_habit_list_raises_instead_of_returning_empty(store):
    store.col.cfg[HABITS_KEY] = "garbage"
    with pytest.raises(ValueError):
        store.habits()


def test_toggle_today_ticks_then_unticks_and_persists(store):
    store.save_habits(add_habit([], "A", PALETTE[0], T, id_factory=lambda: "h1"))
    assert store.toggle_today("h1", TODAY).is_set(T)
    assert store.bitmap("h1").is_set(T)
    assert not store.toggle_today("h1", TODAY).is_set(T)
    assert not store.bitmap("h1").is_set(T)


def test_toggle_today_only_touches_today(store):
    store.save_habits(add_habit([], "A", PALETTE[0], T, id_factory=lambda: "h1"))
    store.col.cfg[DATA_PREFIX + "h1"] = Bitmap().with_bit(T - 5, True).to_dict()
    store.toggle_today("h1", TODAY)
    assert store.bitmap("h1").ticked_ordinals() == {T - 5, T}


def test_toggle_unknown_habit_raises_and_writes_nothing(store):
    with pytest.raises(KeyError):
        store.toggle_today("nope", TODAY)
    assert DATA_PREFIX + "nope" not in store.col.cfg


def test_toggle_archived_habit_is_refused(store):
    habits = add_habit([], "A", PALETTE[0], T, id_factory=lambda: "h1")
    store.save_habits(archive_habit(habits, "h1"))
    with pytest.raises(KeyError):
        store.toggle_today("h1", TODAY)


def test_toggle_on_corrupt_bitmap_raises_and_does_not_overwrite(store):
    store.save_habits(add_habit([], "A", PALETTE[0], T, id_factory=lambda: "h1"))
    bad = {"epoch": T, "bits": "!!!"}
    store.col.cfg[DATA_PREFIX + "h1"] = bad
    with pytest.raises(ValueError):
        store.toggle_today("h1", TODAY)
    assert store.col.cfg[DATA_PREFIX + "h1"] == bad


def test_delete_data_removes_the_key(store):
    store.col.cfg[DATA_PREFIX + "h1"] = Bitmap().with_bit(T, True).to_dict()
    store.delete_data("h1")
    assert DATA_PREFIX + "h1" not in store.col.cfg


def test_stored_ids_lists_only_data_keys(store):
    store.col.cfg[DATA_PREFIX + "h1"] = {}
    store.col.cfg[DATA_PREFIX + "h2"] = {}
    store.col.cfg[HABITS_KEY] = []
    store.col.cfg["somethingElse"] = 1
    assert store.stored_ids() == {"h1", "h2"}
