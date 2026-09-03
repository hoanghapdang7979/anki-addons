from checklist import apply_checklist_if_empty, build_habit_checklist


def test_build_habit_checklist_returns_empty_string_for_no_habits():
    assert build_habit_checklist([]) == ""


def test_build_habit_checklist_renders_single_habit():
    assert build_habit_checklist(["Exercise"]) == "[ ] Exercise"


def test_build_habit_checklist_joins_multiple_habits_with_br_in_order():
    result = build_habit_checklist(["Exercise", "Read", "Meditate"])

    assert result == "[ ] Exercise<br>[ ] Read<br>[ ] Meditate"


def test_apply_checklist_if_empty_fills_empty_field():
    note = {"Habits": ""}

    changed = apply_checklist_if_empty(note, "Habits", "[ ] Exercise")

    assert changed is True
    assert note["Habits"] == "[ ] Exercise"


def test_apply_checklist_if_empty_fills_whitespace_only_field():
    note = {"Habits": "   "}

    changed = apply_checklist_if_empty(note, "Habits", "[ ] Exercise")

    assert changed is True
    assert note["Habits"] == "[ ] Exercise"


def test_apply_checklist_if_empty_never_overwrites_a_previously_filled_checklist():
    # This is the critical never-overwrite case (see plan.md Risks): a field
    # that already looks like our own checklist output, with ticks/notes the
    # user has since added, must never be re-rendered - that would wipe out
    # their progress and notes.
    note = {"Habits": "[x] Exercise<br>[ ] Read - chua doc xong"}

    changed = apply_checklist_if_empty(
        note, "Habits", "[ ] Exercise<br>[ ] Read<br>[ ] Meditate"
    )

    assert changed is False
    assert note["Habits"] == "[x] Exercise<br>[ ] Read - chua doc xong"


def test_apply_checklist_if_empty_does_nothing_when_field_missing():
    note = {"Front": "Hello"}

    changed = apply_checklist_if_empty(note, "Habits", "[ ] Exercise")

    assert changed is False
    assert "Habits" not in note
