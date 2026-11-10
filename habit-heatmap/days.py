"""Pure date logic for the heatmap: which calendar day Anki considers "today"
and the calendar-year grid layout. No aqt/anki imports.
"""

from datetime import date, datetime, timedelta


def anki_today(day_cutoff: int) -> date:
    """Calendar date of the current Anki day.

    `day_cutoff` is the timestamp at which the next Anki day starts
    (sched.day_cutoff). Taking the local date of the cutoff and subtracting one
    calendar day (instead of subtracting 86400s) keeps this correct across DST
    changes.
    """
    return datetime.fromtimestamp(day_cutoff).date() - timedelta(days=1)


def year_grid(year: int) -> list[list[date | None]]:
    """Calendar-year grid: one column per week (Monday first), 7 rows, from the
    week containing Jan 1 to the week containing Dec 31. Cells outside the year are None."""
    first = date(year, 1, 1)
    last = date(year, 12, 31)
    monday = first - timedelta(days=first.weekday())
    sunday = last + timedelta(days=6 - last.weekday())
    weeks = ((sunday - monday).days + 1) // 7
    grid: list[list[date | None]] = []
    for w in range(weeks):
        column: list[date | None] = []
        for d in range(7):
            cell = monday + timedelta(weeks=w, days=d)
            column.append(cell if first <= cell <= last else None)
        grid.append(column)
    return grid


def clamp_year(year: int, min_year: int, max_year: int) -> int:
    """Clamp into [min_year, max_year]; if the range is inverted, max_year wins."""
    return max(min(year, max_year), min(min_year, max_year))
