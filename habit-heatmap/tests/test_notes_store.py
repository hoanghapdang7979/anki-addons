import json
from datetime import date

import pytest

from habits import PALETTE, Habit, archive_habit, habits_to_json
from notes import MAX_KEY_CHARS, MAX_NOTE_CHARS, NoteStorageFull
from reconcile import reconcile
from shadow import ShadowFile, ShadowState
from store import DATA_PREFIX, HABITS_KEY, NOTES_PREFIX, Store

TODAY = date(2026, 11, 11)
T = TODAY.toordinal()
CREATED = date(2026, 11, 1).toordinal()


class FakeDB:
    def __init__(self, col):
        self.col = col

    def scalar(self, sql, key):
        return -1 if key in self.col.pending else 0


class FakeCol:
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


def habit(hid="h1", archived=False):
    return Habit(hid, "A", PALETTE[0], CREATED, archived)


@pytest.fixture
def env(tmp_path):
    shadow = ShadowFile(tmp_path / "s.json")
    store = Store(FakeCol(), shadow=shadow)
    store.save_habits([habit()])
    store.col.pending.clear()
    return store, shadow


def key(day: date) -> str:
    return str(day.toordinal())


# --- Store.set_note / Store.notes ---------------------------------------


def test_notes_default_to_empty(env):
    store, _ = env
    assert store.notes("h1") == {}


def test_set_note_for_today_stores_cleaned_text(env):
    store, _ = env
    truncated = store.set_note("h1", TODAY, "  went for a run \r\n", TODAY)
    assert truncated is False
    assert store.notes("h1") == {key(TODAY): "went for a run"}
    assert store.col.cfg[NOTES_PREFIX + "h1"] == {key(TODAY): "went for a run"}


def test_set_note_allows_a_past_day_even_if_never_ticked(env):
    store, _ = env
    store.set_note("h1", date(2026, 11, 5), "was sick", TODAY)
    assert store.notes("h1") == {key(date(2026, 11, 5)): "was sick"}


@pytest.mark.parametrize("bad_day", [date(2026, 11, 12), date(2026, 10, 31), date(2030, 1, 1)])
def test_set_note_refuses_future_and_pre_creation_days_and_writes_nothing(env, bad_day):
    store, _ = env
    with pytest.raises(ValueError):
        store.set_note("h1", bad_day, "x", TODAY)
    assert NOTES_PREFIX + "h1" not in store.col.cfg


def test_set_note_unknown_or_archived_habit_is_refused(env):
    store, _ = env
    with pytest.raises(KeyError):
        store.set_note("nope", TODAY, "x", TODAY)
    store.save_habits(archive_habit(store.habits(), "h1"))
    with pytest.raises(KeyError):
        store.set_note("h1", TODAY, "x", TODAY)


def test_empty_text_deletes_the_note(env):
    store, _ = env
    store.set_note("h1", TODAY, "keep", TODAY)
    store.set_note("h1", TODAY, "   ", TODAY)
    assert store.notes("h1") == {}


def test_overlong_note_is_truncated_and_reported(env):
    store, _ = env
    truncated = store.set_note("h1", TODAY, "x" * (MAX_NOTE_CHARS + 50), TODAY)
    assert truncated is True
    assert len(store.notes("h1")[key(TODAY)]) == MAX_NOTE_CHARS


def test_storage_cap_refuses_and_leaves_existing_notes_untouched(env):
    store, _ = env
    filler = {str(100_000 + i): "y" * MAX_NOTE_CHARS for i in range(MAX_KEY_CHARS // MAX_NOTE_CHARS + 5)}
    store.col.cfg[NOTES_PREFIX + "h1"] = dict(filler)
    with pytest.raises(NoteStorageFull):
        store.set_note("h1", TODAY, "one more", TODAY)
    assert store.col.cfg[NOTES_PREFIX + "h1"] == filler


def test_corrupt_notes_value_raises_and_is_not_overwritten(env):
    store, _ = env
    store.col.cfg[NOTES_PREFIX + "h1"] = ["not", "a", "dict"]
    with pytest.raises(ValueError):
        store.set_note("h1", TODAY, "x", TODAY)
    assert store.col.cfg[NOTES_PREFIX + "h1"] == ["not", "a", "dict"]


def test_unticking_today_keeps_the_note(env):
    store, _ = env
    store.toggle_today("h1", TODAY)
    store.set_note("h1", TODAY, "felt great", TODAY)
    store.toggle_today("h1", TODAY)  # untick
    assert store.notes("h1") == {key(TODAY): "felt great"}


def test_delete_data_removes_the_notes_key_and_shadow_notes(env):
    store, shadow = env
    store.set_note("h1", TODAY, "bye", TODAY)
    store.save_habits([])
    store.delete_data("h1")
    assert NOTES_PREFIX + "h1" not in store.col.cfg
    assert "h1" not in shadow.load().notes


def test_set_note_mirrors_into_the_shadow(env):
    store, shadow = env
    store.set_note("h1", TODAY, "mirrored", TODAY)
    assert shadow.load().notes["h1"] == {key(TODAY): "mirrored"}


def test_shadow_failure_never_blocks_saving_a_note():
    class BrokenShadow:
        def update(self, fn):
            raise OSError("disk full")

    store = Store(FakeCol(), shadow=BrokenShadow())
    store.col.cfg[HABITS_KEY] = habits_to_json([habit()])
    store.set_note("h1", TODAY, "still saved", TODAY)
    assert store.notes("h1") == {key(TODAY): "still saved"}


def test_shadow_state_roundtrips_notes(tmp_path):
    f = ShadowFile(tmp_path / "s.json")
    f.save(ShadowState(notes={"h1": {"5": "a"}}, base_notes={"h1": {"5": "old"}}))
    state = f.load()
    assert state.notes == {"h1": {"5": "a"}} and state.base_notes == {"h1": {"5": "old"}}
    raw = json.loads((tmp_path / "s.json").read_text(encoding="utf-8"))
    assert raw["notes"] == {"h1": {"5": "a"}}


# --- reconcile merges notes -----------------------------------------------


def setup_notes(store, shadow, *, remote, local, base, synced=True):
    store.col.cfg[HABITS_KEY] = habits_to_json([habit()])
    if remote is not None:
        store.col.cfg[NOTES_PREFIX + "h1"] = remote
    shadow.save(
        ShadowState(
            habits=[habit()],
            base_habits=[habit()],
            notes={"h1": local},
            base_notes={"h1": base},
        )
    )
    store.col.pending.clear()
    if not synced:
        store.col.pending.add(NOTES_PREFIX + "h1")


def test_remote_note_is_adopted_and_becomes_the_base(env):
    store, shadow = env
    setup_notes(store, shadow, remote={"1": "a", "2": "b"}, local={"1": "a"}, base={"1": "a"})
    assert reconcile(store) is False
    assert store.notes("h1") == {"1": "a", "2": "b"}
    assert shadow.load().base_notes["h1"] == {"1": "a", "2": "b"}


def test_local_note_overwritten_by_a_sync_is_recovered(env):
    store, shadow = env
    setup_notes(store, shadow, remote={"1": "a"}, local={"1": "a", "5": "mine"}, base={"1": "a"})
    assert reconcile(store) is True
    assert store.notes("h1") == {"1": "a", "5": "mine"}


def test_remote_note_deletion_propagates(env):
    store, shadow = env
    setup_notes(store, shadow, remote={"1": "a"}, local={"1": "a", "2": "b"}, base={"1": "a", "2": "b"})
    reconcile(store)
    assert store.notes("h1") == {"1": "a"}


def test_local_note_deletion_is_not_undone_by_a_stale_remote(env):
    store, shadow = env
    setup_notes(store, shadow, remote={"1": "a", "2": "b"}, local={"1": "a"}, base={"1": "a", "2": "b"})
    assert reconcile(store) is True
    assert store.notes("h1") == {"1": "a"}


def test_notes_on_different_days_from_both_machines_are_combined(env):
    store, shadow = env
    setup_notes(store, shadow, remote={"3": "R"}, local={"2": "L"}, base={})
    reconcile(store)
    assert store.notes("h1") == {"2": "L", "3": "R"}


def test_pending_note_change_does_not_advance_the_base(env):
    store, shadow = env
    setup_notes(store, shadow, remote={"1": "a"}, local={"1": "a"}, base={}, synced=False)
    reconcile(store)
    assert shadow.load().base_notes["h1"] == {}


def test_corrupt_notes_are_left_untouched_by_reconcile(env):
    store, shadow = env
    setup_notes(store, shadow, remote={"1": "a"}, local={"1": "a"}, base={"1": "a"})
    store.col.cfg[NOTES_PREFIX + "h1"] = "garbage"
    reconcile(store)
    assert store.col.cfg[NOTES_PREFIX + "h1"] == "garbage"


def test_notes_of_a_removed_habit_are_forgotten_in_shadow_but_not_deleted_from_config(env):
    store, shadow = env
    setup_notes(store, shadow, remote={"1": "a"}, local={"1": "a"}, base={"1": "a"})
    store.col.cfg[HABITS_KEY] = habits_to_json([])  # habit removed remotely
    reconcile(store)
    assert "h1" not in shadow.load().notes
    assert NOTES_PREFIX + "h1" in store.col.cfg


def test_reconcile_with_notes_is_idempotent(env):
    store, shadow = env
    setup_notes(store, shadow, remote={"1": "a", "3": "R"}, local={"1": "a", "2": "L"}, base={"1": "a"})
    reconcile(store)
    store.col.pending.clear()
    snapshot = dict(store.col.cfg)
    assert reconcile(store) is False
    assert store.col.cfg == snapshot


def test_data_prefix_and_notes_prefix_do_not_collide():
    assert not NOTES_PREFIX.startswith(DATA_PREFIX) and not DATA_PREFIX.startswith(NOTES_PREFIX)
