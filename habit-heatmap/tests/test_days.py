from datetime import date, datetime, timedelta

import pytest

from days import anki_today, clamp_year, year_grid


def _ts(y, m, d, hh, mm=0):
    return datetime(y, m, d, hh, mm).timestamp()


def test_anki_today_before_rollover_is_still_previous_day():
    # now is 02:00 on Jan 2; next day starts at 04:00 => cutoff is Jan 2 04:00
    assert anki_today(_ts(2026, 1, 2, 4)) == date(2026, 1, 1)


def test_anki_today_after_rollover_is_calendar_day():
    # now is 05:00 on Jan 2; cutoff is Jan 3 04:00
    assert anki_today(_ts(2026, 1, 3, 4)) == date(2026, 1, 2)


def test_anki_today_midnight_rollover():
    assert anki_today(_ts(2026, 1, 3, 0)) == date(2026, 1, 2)


def test_anki_today_crosses_year_boundary():
    assert anki_today(_ts(2026, 1, 1, 4)) == date(2025, 12, 31)


def _days(grid):
    return [c for col in grid for c in col if c is not None]


@pytest.mark.parametrize("year", [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027])
def test_year_grid_covers_every_day_of_the_year_exactly_once_in_order(year):
    days = _days(year_grid(year))
    last = date(year, 12, 31)
    assert days[0] == date(year, 1, 1) and days[-1] == last
    assert len(days) == (last - date(year, 1, 1)).days + 1
    assert all((b - a).days == 1 for a, b in zip(days, days[1:]))


@pytest.mark.parametrize("year", range(2018, 2032))
def test_year_grid_has_53_or_54_columns_of_7_rows(year):
    grid = year_grid(year)
    assert len(grid) in (53, 54)
    assert all(len(col) == 7 for col in grid)


def test_year_grid_rows_are_weekdays_monday_first():
    for col in year_grid(2026):
        for row, cell in enumerate(col):
            if cell is not None:
                assert cell.weekday() == row


def test_year_grid_cells_outside_the_year_are_none():
    grid = year_grid(2026)  # Jan 1 2026 is a Thursday -> Mon-Wed of the first column are None
    assert [c is None for c in grid[0][:3]] == [True, True, True]
    assert grid[0][3] == date(2026, 1, 1)
    assert [c is None for c in grid[-1][4:]] == [True, True, True]  # Dec 31 2026 is a Thursday
    assert grid[-1][3] == date(2026, 12, 31)


def test_year_grid_leap_year_has_feb_29():
    assert date(2024, 2, 29) in _days(year_grid(2024))
    assert date(2023, 2, 28) in _days(year_grid(2023))
    assert len(_days(year_grid(2023))) == 365


def test_year_grid_year_starting_on_monday_has_no_leading_blanks():
    assert date(2024, 1, 1).weekday() == 0
    assert year_grid(2024)[0][0] == date(2024, 1, 1)


def test_year_grid_year_ending_on_sunday_has_no_trailing_blanks():
    assert date(2023, 12, 31).weekday() == 6
    assert year_grid(2023)[-1][-1] == date(2023, 12, 31)


def test_year_grid_first_column_starts_on_a_monday_week_that_contains_jan_1():
    first = year_grid(2026)[0]
    jan1 = date(2026, 1, 1)
    monday = jan1 - timedelta(days=jan1.weekday())
    assert [(c - monday).days if c else None for c in first] == [None, None, None, 3, 4, 5, 6]


@pytest.mark.parametrize(
    "year,lo,hi,expected",
    [(2026, 2024, 2026, 2026), (2027, 2024, 2026, 2026), (2020, 2024, 2026, 2024), (2025, 2025, 2025, 2025)],
)
def test_clamp_year(year, lo, hi, expected):
    assert clamp_year(year, lo, hi) == expected


def test_clamp_year_when_min_exceeds_max_returns_max():
    assert clamp_year(2000, 2030, 2026) == 2026


from days import navigate_year  # noqa: E402


@pytest.mark.parametrize(
    "view,command,expected",
    [
        (None, "prev", 2025),  # default view is the current year
        (None, "next", 2026),  # cannot go past the current year
        (2025, "next", 2026),
        (2024, "prev", 2024),  # earliest allowed
        (2024, "today", 2026),
        (2025, "today", 2026),
        (2026, "bogus", 2026),  # unknown command leaves the year alone
    ],
)
def test_navigate_year(view, command, expected):
    assert navigate_year(view, command, current_year=2026, min_year=2024, max_year=2026) == expected


def test_navigate_year_clamps_a_stale_view_year_into_range():
    assert navigate_year(2010, "bogus", current_year=2026, min_year=2024, max_year=2026) == 2024


from days import MAX_VIEW_YEAR, MIN_VIEW_YEAR  # noqa: E402


def test_arrows_work_even_when_every_habit_was_created_this_year():
    kw = dict(current_year=2026, min_year=MIN_VIEW_YEAR, max_year=MAX_VIEW_YEAR)
    assert navigate_year(None, "prev", **kw) == 2025
    assert navigate_year(None, "next", **kw) == 2027
    assert navigate_year(2027, "today", **kw) == 2026


def test_view_year_range_is_generous_but_valid_for_year_grid():
    assert MIN_VIEW_YEAR < 2026 < MAX_VIEW_YEAR
    assert year_grid(MIN_VIEW_YEAR) and year_grid(MAX_VIEW_YEAR)
