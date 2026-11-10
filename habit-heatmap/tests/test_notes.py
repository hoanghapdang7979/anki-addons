from datetime import date

import pytest

from notes import MAX_KEY_CHARS, MAX_NOTE_CHARS, clean_note, merge_notes, note_day_ok

# --- clean_note -----------------------------------------------------------


def test_limits_match_the_spec():
    assert MAX_NOTE_CHARS == 500
    assert MAX_KEY_CHARS == 200_000


def test_clean_note_strips_surrounding_whitespace():
    assert clean_note("  hello \n") == ("hello", False)


def test_clean_note_normalises_line_endings():
    assert clean_note("a\r\nb\rc") == ("a\nb\nc", False)


def test_clean_note_removes_control_characters_but_keeps_newlines():
    assert clean_note("a\x00b\x07c\nd") == ("abc\nd", False)


def test_clean_note_turns_tabs_into_spaces():
    assert clean_note("a\tb") == ("a b", False)


def test_clean_note_whitespace_only_becomes_empty():
    assert clean_note(" \n\t ") == ("", False)


def test_clean_note_keeps_exactly_the_limit_untruncated():
    text = "x" * MAX_NOTE_CHARS
    assert clean_note(text) == (text, False)


def test_clean_note_truncates_beyond_the_limit_and_reports_it():
    cleaned, truncated = clean_note("x" * (MAX_NOTE_CHARS + 25))
    assert truncated is True
    assert cleaned == "x" * MAX_NOTE_CHARS


def test_clean_note_counts_characters_not_bytes():
    text = "ệ" * MAX_NOTE_CHARS
    assert clean_note(text) == (text, False)


def test_clean_note_trailing_whitespace_left_by_truncation_is_stripped():
    cleaned, truncated = clean_note("x" * (MAX_NOTE_CHARS - 1) + "   tail")
    assert truncated is True
    assert cleaned == "x" * (MAX_NOTE_CHARS - 1)


def test_clean_note_keeps_vietnamese_text_and_inner_newlines():
    assert clean_note("Hôm nay ốm\n\nnên bỏ lỡ") == ("Hôm nay ốm\n\nnên bỏ lỡ", False)


# --- merge_notes: per-day three-way merge ---------------------------------


def test_merge_notes_nothing_changed():
    n = {"1": "a", "2": "b"}
    assert merge_notes(n, n, n) == n


def test_merge_notes_local_addition_kept_when_remote_unchanged():
    assert merge_notes({"1": "a"}, {"1": "a", "2": "b"}, {"1": "a"}) == {"1": "a", "2": "b"}


def test_merge_notes_remote_addition_adopted_when_local_unchanged():
    assert merge_notes({"1": "a"}, {"1": "a"}, {"1": "a", "3": "c"}) == {"1": "a", "3": "c"}


def test_merge_notes_additions_for_different_days_are_combined():
    assert merge_notes({}, {"2": "L"}, {"3": "R"}) == {"2": "L", "3": "R"}


def test_merge_notes_same_day_changed_on_both_sides_remote_wins():
    assert merge_notes({"1": "old"}, {"1": "mine"}, {"1": "theirs"}) == {"1": "theirs"}


def test_merge_notes_local_edit_kept_when_remote_unchanged():
    assert merge_notes({"1": "old"}, {"1": "mine"}, {"1": "old"}) == {"1": "mine"}


def test_merge_notes_remote_edit_adopted_when_local_unchanged():
    assert merge_notes({"1": "old"}, {"1": "old"}, {"1": "new"}) == {"1": "new"}


def test_merge_notes_local_delete_propagates():
    assert merge_notes({"1": "a", "2": "b"}, {"1": "a"}, {"1": "a", "2": "b"}) == {"1": "a"}


def test_merge_notes_remote_delete_propagates():
    assert merge_notes({"1": "a", "2": "b"}, {"1": "a", "2": "b"}, {"1": "a"}) == {"1": "a"}


def test_merge_notes_local_edit_vs_remote_delete_remote_wins():
    assert merge_notes({"1": "a"}, {"1": "edited"}, {}) == {}


def test_merge_notes_is_idempotent():
    once = merge_notes({"1": "a"}, {"1": "x", "2": "L"}, {"1": "a", "3": "R"})
    assert merge_notes({"1": "a"}, once, once) == once


def test_merge_notes_does_not_mutate_its_inputs():
    base, local, remote = {"1": "a"}, {"1": "b"}, {"2": "c"}
    merge_notes(base, local, remote)
    assert (base, local, remote) == ({"1": "a"}, {"1": "b"}, {"2": "c"})


# --- note_day_ok ---------------------------------------------------------

TODAY = date(2026, 11, 11)
CREATED = date(2026, 11, 1).toordinal()


@pytest.mark.parametrize(
    "day,ok",
    [
        (date(2026, 11, 11), True),  # today
        (date(2026, 11, 10), True),  # yesterday
        (date(2026, 11, 1), True),  # creation day
        (date(2026, 10, 31), False),  # before the habit existed
        (date(2026, 11, 12), False),  # tomorrow
        (date(2027, 1, 1), False),  # far future
    ],
)
def test_note_day_ok(day, ok):
    assert note_day_ok(day, CREATED, TODAY) is ok


from notes import parse_note_arg  # noqa: E402


def test_parse_note_arg_accepts_id_and_iso_date():
    assert parse_note_arg("h_abc-1:2026-11-05") == ("h_abc-1", date(2026, 11, 5))


@pytest.mark.parametrize(
    "arg",
    ["", "h1", "h1:", ":2026-11-05", "h1:2026-02-30", "h1:2026-1-5", "h 1:2026-11-05",
     "h1:2026-11-05:x", "h1'):x(:2026-11-05", "h1:2026-11-05 ", "h1:20261105", "h1:2026-11-05
"],
)
def test_parse_note_arg_rejects_anything_else(arg):
    assert parse_note_arg(arg) is None
