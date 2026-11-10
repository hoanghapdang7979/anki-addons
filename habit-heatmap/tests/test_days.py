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
