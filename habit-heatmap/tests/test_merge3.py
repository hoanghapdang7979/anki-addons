from bitmap import Bitmap
from habits import PALETTE, Habit
from merge3 import merge_bitmap, merge_habits

T = 739000


def bits(*days):
    bm = Bitmap()
    for d in days:
        bm = bm.with_bit(T + d, True)
    return bm


def h(hid, name="A", archived=False, color=PALETTE[0]):
    return Habit(hid, name, color, T, archived)


# --- bitmaps: (L & R) | (L - B) | (R - B) ------------------------------

def test_nothing_changed_stays_the_same():
    assert merge_bitmap(bits(1, 2), bits(1, 2), bits(1, 2)) == bits(1, 2)


def test_local_tick_is_kept_when_remote_unchanged():
    assert merge_bitmap(bits(1), bits(1, 2), bits(1)) == bits(1, 2)


def test_remote_tick_is_adopted_when_local_unchanged():
    assert merge_bitmap(bits(1), bits(1), bits(1, 3)) == bits(1, 3)


def test_ticks_added_on_both_sides_are_combined():
    assert merge_bitmap(bits(1), bits(1, 2), bits(1, 3)) == bits(1, 2, 3)


def test_remote_untick_propagates_when_local_unchanged():
    assert merge_bitmap(bits(1, 2), bits(1, 2), bits(1)) == bits(1)


def test_local_untick_wins_over_a_stale_remote_copy():
    assert merge_bitmap(bits(1, 2), bits(1), bits(1, 2)) == bits(1)


def test_untick_on_one_side_and_new_tick_on_the_other_both_apply():
    assert merge_bitmap(bits(1, 2), bits(1), bits(1, 2, 5)) == bits(1, 5)


def test_remote_wiped_but_local_has_only_new_ticks_keeps_them():
    # e.g. "Download from AnkiWeb" replaced the config with an older/empty copy
    assert merge_bitmap(bits(), bits(4, 5), bits()) == bits(4, 5)


def test_first_ever_merge_with_empty_base_adopts_remote_and_local():
    assert merge_bitmap(bits(), bits(), bits(1, 2)) == bits(1, 2)
    assert merge_bitmap(bits(), bits(1, 2), bits(1, 2)) == bits(1, 2)


def test_merge_bitmap_is_idempotent():
    once = merge_bitmap(bits(1, 2), bits(1, 5), bits(2, 3))
    assert merge_bitmap(bits(1, 2), once, once) == once


# --- habit list ----------------------------------------------------------

def ids(habits):
    return [x.id for x in habits]


def test_habits_unchanged():
    base = [h("a"), h("b")]
    assert merge_habits(base, base, base) == base


def test_habit_added_locally_is_kept_and_remote_add_is_adopted():
    base = [h("a")]
    merged = merge_habits(base, [h("a"), h("L")], [h("a"), h("R")])
    assert sorted(ids(merged)) == ["L", "R", "a"]


def test_remote_order_comes_first_then_local_only_additions():
    base = [h("a"), h("b")]
    assert ids(merge_habits(base, [h("a"), h("b"), h("L")], [h("b"), h("a")])) == ["b", "a", "L"]


def test_delete_on_remote_propagates_when_local_unchanged():
    base = [h("a"), h("b")]
    assert ids(merge_habits(base, base, [h("a")])) == ["a"]


def test_delete_on_local_wins_over_a_stale_remote_copy():
    base = [h("a"), h("b")]
    assert ids(merge_habits(base, [h("a")], base)) == ["a"]


def test_remote_rename_is_adopted_when_local_unchanged():
    base = [h("a", "Old")]
    assert merge_habits(base, base, [h("a", "New")])[0].name == "New"


def test_local_rename_is_kept_when_remote_unchanged():
    base = [h("a", "Old")]
    assert merge_habits(base, [h("a", "Mine")], base)[0].name == "Mine"


def test_both_renamed_remote_wins_deterministically():
    base = [h("a", "Old")]
    assert merge_habits(base, [h("a", "Mine")], [h("a", "Theirs")])[0].name == "Theirs"


def test_remote_archive_propagates():
    base = [h("a")]
    assert merge_habits(base, base, [h("a", archived=True)])[0].archived is True


def test_everything_wiped_remotely_but_never_synced_before_restores_local():
    assert ids(merge_habits([], [h("a")], [])) == ["a"]
