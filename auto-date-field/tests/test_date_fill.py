from datetime import date

from date_fill import apply_date_if_empty, today_iso


def test_today_iso_formats_explicit_date_as_yyyy_mm_dd():
    assert today_iso(date(2026, 9, 3)) == "2026-09-03"


def test_apply_date_if_empty_fills_empty_field():
    note = {"Date": ""}

    changed = apply_date_if_empty(note, "Date", "2026-09-03")

    assert changed is True
    assert note["Date"] == "2026-09-03"


def test_apply_date_if_empty_fills_whitespace_only_field():
    note = {"Date": "   "}

    changed = apply_date_if_empty(note, "Date", "2026-09-03")

    assert changed is True
    assert note["Date"] == "2026-09-03"


def test_apply_date_if_empty_does_not_overwrite_existing_content():
    note = {"Date": "2020-01-01"}

    changed = apply_date_if_empty(note, "Date", "2026-09-03")

    assert changed is False
    assert note["Date"] == "2020-01-01"


def test_apply_date_if_empty_does_nothing_when_field_missing():
    note = {"Front": "Hello"}

    changed = apply_date_if_empty(note, "Date", "2026-09-03")

    assert changed is False
    assert "Date" not in note
