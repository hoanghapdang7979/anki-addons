from datetime import date, datetime

from days import GRID_WEEKS, anki_today, build_grid


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


def test_grid_shape_is_53_columns_of_7_rows():
    grid = build_grid(date(2026, 11, 11))
    assert GRID_WEEKS == 53
    assert len(grid) == 53
    assert all(len(col) == 7 for col in grid)


def test_grid_today_is_in_last_column_at_its_weekday_row():
    today = date(2026, 11, 11)  # Wednesday
    grid = build_grid(today)
    assert grid[-1][today.weekday()] == today


def test_grid_cells_after_today_in_last_column_are_none():
    today = date(2026, 11, 11)  # Wednesday => rows 3..6 are future
    grid = build_grid(today)
    assert [c is None for c in grid[-1]] == [False, False, False, True, True, True, True]


def test_grid_when_today_is_monday_only_first_row_filled_in_last_column():
    today = date(2026, 11, 9)  # Monday
    grid = build_grid(today)
    assert grid[-1][0] == today
    assert all(c is None for c in grid[-1][1:])


def test_grid_when_today_is_sunday_last_column_is_full():
    today = date(2026, 11, 15)  # Sunday
    grid = build_grid(today)
    assert all(c is not None for c in grid[-1])
    assert grid[-1][6] == today


def test_grid_first_cell_is_monday_52_weeks_before_this_weeks_monday():
    today = date(2026, 11, 11)
    grid = build_grid(today)
    first = grid[0][0]
    assert first.weekday() == 0
    assert (date(2026, 11, 9) - first).days == 52 * 7


def test_grid_dates_are_contiguous_in_column_major_order():
    grid = build_grid(date(2026, 11, 11))
    flat = [c for col in grid for c in col if c is not None]
    assert all((b - a).days == 1 for a, b in zip(flat, flat[1:]))
    assert len(flat) == 52 * 7 + date(2026, 11, 11).weekday() + 1
