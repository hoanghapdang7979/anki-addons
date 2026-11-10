import json

from bitmap import Bitmap
from habits import PALETTE, Habit
from shadow import ShadowFile, ShadowState

T = 739000
H = Habit("h1", "Exercise", PALETTE[0], T, False)


def test_missing_file_loads_empty_state(tmp_path):
    state = ShadowFile(tmp_path / "s.json").load()
    assert state.habits == [] and state.deleted == set() and state.bitmaps == {}


def test_save_then_load_roundtrip(tmp_path):
    f = ShadowFile(tmp_path / "s.json")
    f.save(ShadowState([H], {"gone"}, {"h1": Bitmap().with_bit(T, True).with_bit(T + 3, True)}))
    state = f.load()
    assert state.habits == [H]
    assert state.deleted == {"gone"}
    assert state.bitmaps["h1"].ticked_ordinals() == {T, T + 3}


def test_corrupt_file_is_set_aside_and_empty_state_returned(tmp_path):
    path = tmp_path / "s.json"
    path.write_text("{not json", encoding="utf-8")
    state = ShadowFile(path).load()
    assert state.habits == []
    assert not path.exists()
    assert (tmp_path / "s.json.corrupt").read_text(encoding="utf-8") == "{not json"


def test_save_creates_parent_directory_and_leaves_no_temp_file(tmp_path):
    f = ShadowFile(tmp_path / "nested" / "s.json")
    f.save(ShadowState())
    assert json.loads((tmp_path / "nested" / "s.json").read_text(encoding="utf-8"))
    assert [p.name for p in (tmp_path / "nested").iterdir()] == ["s.json"]


def test_update_applies_function_and_persists(tmp_path):
    f = ShadowFile(tmp_path / "s.json")
    f.update(lambda s: s.deleted.add("x"))
    assert f.load().deleted == {"x"}


from shadow import shadow_filename  # noqa: E402


def test_shadow_filename_is_filesystem_safe_and_per_profile():
    a = shadow_filename("User 1")
    b = shadow_filename("IFE-Test")
    assert a != b
    assert a.startswith("shadow-") and a.endswith(".json")
    assert all(c.isalnum() or c in "-_." for c in a)


def test_shadow_filename_distinguishes_names_that_sanitize_alike():
    assert shadow_filename("a b") != shadow_filename("a_b")


def test_shadow_filename_handles_missing_and_unicode_names():
    assert shadow_filename(None).endswith(".json")
    assert all(c.isalnum() or c in "-_." for c in shadow_filename(r"Hồ sơ 1/\:"))
