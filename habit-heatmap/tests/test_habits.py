import pytest

from habits import (
    PALETTE,
    Habit,
    active,
    add_habit,
    archive_habit,
    archived,
    delete_habit,
    habits_from_json,
    habits_to_json,
    move_habit,
    orphan_ids,
    recolor_habit,
    rename_habit,
    restore_habit,
)

TODAY = 739000


def make(*names):
    habits: list[Habit] = []
    for i, n in enumerate(names):
        habits = add_habit(habits, n, PALETTE[0], TODAY, id_factory=lambda i=i: f"h{i}")
    return habits


def test_add_habit_appends_with_given_id_color_and_created():
    habits = add_habit([], "  Exercise ", "#123456", TODAY, id_factory=lambda: "abc")
    assert habits == [Habit("abc", "Exercise", "#123456", TODAY, False)]


def test_add_habit_blank_name_rejected():
    with pytest.raises(ValueError):
        add_habit([], "   ", PALETTE[0], TODAY)


def test_add_habit_generates_unique_ids_by_default():
    habits = add_habit([], "A", PALETTE[0], TODAY)
    habits = add_habit(habits, "B", PALETTE[0], TODAY)
    assert habits[0].id != habits[1].id


def test_add_habit_does_not_mutate_input():
    base = make("A")
    add_habit(base, "B", PALETTE[0], TODAY)
    assert len(base) == 1


def test_rename_keeps_id_and_other_fields():
    habits = rename_habit(make("A", "B"), "h1", " Read ")
    assert habits[1] == Habit("h1", "Read", PALETTE[0], TODAY, False)
    assert habits[0].name == "A"


def test_rename_blank_rejected_and_unknown_id_raises():
    with pytest.raises(ValueError):
        rename_habit(make("A"), "h0", " ")
    with pytest.raises(KeyError):
        rename_habit(make("A"), "nope", "X")


def test_recolor():
    assert recolor_habit(make("A"), "h0", "#abcdef")[0].color == "#abcdef"


def test_move_up_and_down_and_clamp():
    habits = make("A", "B", "C")
    assert [h.id for h in move_habit(habits, "h2", -1)] == ["h0", "h2", "h1"]
    assert [h.id for h in move_habit(habits, "h0", +1)] == ["h1", "h0", "h2"]
    assert [h.id for h in move_habit(habits, "h0", -1)] == ["h0", "h1", "h2"]
    assert [h.id for h in move_habit(habits, "h2", +1)] == ["h0", "h1", "h2"]


def test_archive_keeps_habit_and_filters_views():
    habits = archive_habit(make("A", "B"), "h0")
    assert len(habits) == 2
    assert [h.id for h in active(habits)] == ["h1"]
    assert [h.id for h in archived(habits)] == ["h0"]


def test_restore_makes_habit_active_again():
    habits = restore_habit(archive_habit(make("A"), "h0"), "h0")
    assert [h.id for h in active(habits)] == ["h0"]


def test_delete_removes_habit_and_unknown_raises():
    habits = delete_habit(make("A", "B"), "h0")
    assert [h.id for h in habits] == ["h1"]
    with pytest.raises(KeyError):
        delete_habit(habits, "h0")


def test_json_roundtrip():
    habits = archive_habit(make("A", "B"), "h1")
    assert habits_from_json(habits_to_json(habits)) == habits


def test_from_json_none_is_empty_and_malformed_raises():
    assert habits_from_json(None) == []
    with pytest.raises(ValueError):
        habits_from_json([{"id": "x"}])
    with pytest.raises(ValueError):
        habits_from_json("nope")


def test_orphan_ids_are_stored_ids_without_a_habit():
    habits = make("A", "B")
    assert orphan_ids(habits, {"h0", "h1", "ghost"}) == {"ghost"}
    assert orphan_ids(habits, {"h0"}) == set()


from habits import priority_numbers, reorder  # noqa: E402


def test_reorder_follows_the_given_id_order():
    habits = make("A", "B", "C")
    assert [x.id for x in reorder(habits, ["h2", "h0", "h1"])] == ["h2", "h0", "h1"]


def test_reorder_ignores_unknown_and_duplicate_ids_and_keeps_missing_ones_at_the_end():
    habits = make("A", "B", "C")
    assert [x.id for x in reorder(habits, ["h2", "nope", "h2"])] == ["h2", "h0", "h1"]


def test_reorder_does_not_mutate_the_input():
    habits = make("A", "B")
    reorder(habits, ["h1", "h0"])
    assert [x.id for x in habits] == ["h0", "h1"]


def test_priority_numbers_count_only_active_habits_in_list_order():
    habits = archive_habit(make("A", "B", "C"), "h1")
    assert priority_numbers(habits) == {"h0": 1, "h2": 2}
