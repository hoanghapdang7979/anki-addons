"""Pure HTML rendering of the heatmap: a shared year-navigation toolbar and one
block per habit (calendar-year grid, per-day status, notes, stats). No
aqt/anki imports.

Layout is inline so a block never depends on the page-level <style>/<script>
(those live in assets.py and only add the custom tooltip and the note marker).
Every cell carries `data-*` attributes for that tooltip plus a native `title`
as a fallback.
"""

import html as html_lib
import re
from datetime import date

try:
    from .bitmap import Bitmap
    from .days import year_grid
    from .habits import Habit
    from .stats import completion_pct, current_streak, days_done, longest_streak, streak_runs
    from .themes import resolve_theme, shade, streak_level
except ImportError:  # pytest: modules are top-level via conftest.py sys.path
    from bitmap import Bitmap
    from days import year_grid
    from habits import Habit
    from stats import completion_pct, current_streak, days_done, longest_streak, streak_runs
    from themes import resolve_theme, shade, streak_level

TOGGLE_CMD_PREFIX = "habitheatmap:toggle:"
NOTE_CMD_PREFIX = "habitheatmap:note:"
NAV_CMD_PREFIX = "habitheatmap:nav:"

STATUS_UPCOMING = "Upcoming"
STATUS_TODAY_DONE = "Done today"
STATUS_TODAY_TODO = "Today - not done yet"
STATUS_NOT_STARTED = "Not started"
STATUS_DONE = "Done"
STATUS_MISSED = "Missed"

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

_GREY = {
    STATUS_MISSED: "rgba(128,128,128,0.22)",
    STATUS_TODAY_TODO: "rgba(128,128,128,0.22)",
    STATUS_NOT_STARTED: "rgba(128,128,128,0.10)",
    STATUS_UPCOMING: "rgba(128,128,128,0.40)",
}
_CELL_PX = 12  # 10px cell + 2px gap, used to cap the grid width like Review Heatmap


def format_day(d: date) -> str:
    """e.g. "Wednesday, 11 Nov 2026" - built by hand so it never depends on the locale."""
    return f"{_WEEKDAYS[d.weekday()]}, {d.day} {_MONTHS[d.month - 1]} {d.year}"


def day_status(day: date, today: date, created: int, ticked: set[int]) -> str:
    ordinal = day.toordinal()
    if ordinal > today.toordinal():
        return STATUS_UPCOMING
    if ordinal == today.toordinal():
        return STATUS_TODAY_DONE if ordinal in ticked else STATUS_TODAY_TODO
    if ordinal < created:
        return STATUS_NOT_STARTED
    return STATUS_DONE if ordinal in ticked else STATUS_MISSED


def _pycmd(command: str) -> str:
    return f"pycmd('{command}')"


def build_toolbar_html(view_year: int, min_year: int, max_year: int) -> str:
    """Shared ‹ ○ › bar. The arrows are disabled at the edges of the allowed range."""
    style = "min-width:28px;padding:0 8px;"

    def button(label: str, command: str, disabled: bool = False) -> str:
        flag = " disabled" if disabled else ""
        return f'<button style="{style}" onclick="{_pycmd(NAV_CMD_PREFIX + command)}"{flag}>{label}</button>'

    return (
        '<div class="hh-toolbar" style="display:flex;justify-content:center;gap:6px;margin:14px 0 0;">'
        + button("&#8249;", "prev", view_year <= min_year)
        + button("&#9675;", "today")
        + button("&#8250;", "next", view_year >= max_year)
        + "</div>"
    )


def build_block_html(
    habit: Habit, bitmap: Bitmap, notes: dict[str, str], today: date, view_year: int
) -> str:
    """One habit: header (name + Note/Check buttons when viewing this year), the
    year grid, the year label and the stats line.

    Only today's cell toggles the tick. Past days since the habit was created
    open the note dialog for exactly that day. Everything else is inert. Raises
    ValueError for a habit id that is not safe to embed in an inline JS string.
    """
    if not _SAFE_ID_RE.match(habit.id):
        raise ValueError(f"unsafe habit id: {habit.id!r}")
    theme = resolve_theme(habit.color)
    ticked = bitmap.ticked_ordinals()
    runs = streak_runs(ticked)
    today_ord = today.toordinal()
    toggle_cmd = _pycmd(TOGGLE_CMD_PREFIX + habit.id)

    grid = year_grid(view_year)
    slots: list[str] = []
    for column in grid:
        for cell in column:
            if cell is None:
                slots.append('<div class="hh-blank" style="aspect-ratio:1/1;visibility:hidden;"></div>')
                continue
            ordinal = cell.toordinal()
            status = day_status(cell, today, habit.created, ticked)
            note = notes.get(str(ordinal), "")
            if status in (STATUS_DONE, STATUS_TODAY_DONE):
                background = shade(theme, streak_level(runs.get(ordinal, 1)))
            else:
                background = _GREY[status]
            style = f"aspect-ratio:1/1;position:relative;background:{background};"
            classes = ["hh-cell"]
            if note:
                classes.append("hh-note")
            attrs = ""
            hint = ""
            if cell == today:
                style += "outline:1.5px solid currentColor;outline-offset:1px;cursor:pointer;"
                attrs = f' onclick="{toggle_cmd}"'
            elif habit.created <= ordinal < today_ord:
                hint = "Click to edit note" if note else "Click to add a note"
                style += "cursor:pointer;"
                attrs = f' onclick="{_pycmd(f"{NOTE_CMD_PREFIX}{habit.id}:{cell.isoformat()}")}"'
            label = format_day(cell)
            tooltip = "\n".join(part for part in (label, status, note, hint) if part)
            slots.append(
                f'<div class="{" ".join(classes)}" data-day="{cell.isoformat()}" '
                f'data-label="{html_lib.escape(label)}" data-status="{html_lib.escape(status)}" '
                f'data-note="{html_lib.escape(note, quote=True)}" '
                f'data-hint="{html_lib.escape(hint)}" '
                f'title="{html_lib.escape(tooltip, quote=True)}" style="{style}"{attrs}></div>'
            )

    cur = current_streak(ticked, today_ord)
    best = longest_streak(ticked, today_ord)
    done_n = days_done(ticked, today_ord)
    pct = completion_pct(ticked, habit.created, today_ord)

    buttons = ""
    if view_year == today.year:
        check_label = "&#10003; Done today (click to undo)" if today_ord in ticked else "Check today"
        note_label = "Edit note" if str(today_ord) in notes else "Add note"
        note_cmd = _pycmd(f"{NOTE_CMD_PREFIX}{habit.id}:{today.isoformat()}")
        buttons = (
            f'<span style="display:flex;gap:6px;">'
            f'<button onclick="{note_cmd}">{note_label}</button>'
            f'<button onclick="{toggle_cmd}">{check_label}</button></span>'
        )

    accent = shade(theme, 3)
    value = f'style="color:{accent};"'
    columns = len(grid)
    return (
        f'<div class="hh-block" style="margin:18px auto;max-width:{columns * _CELL_PX + 16}px;padding:0 8px;">'
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
        f'<span style="font-weight:700;"><span style="color:{accent};">&#9679;</span> '
        f"{html_lib.escape(habit.name)}</span>{buttons}</div>"
        '<div style="display:grid;'
        f"grid-template-columns:repeat({columns},minmax(0,1fr));"
        f'grid-auto-flow:column;grid-template-rows:repeat(7,auto);gap:2px;">{"".join(slots)}</div>'
        f'<div style="text-align:center;font-size:11px;opacity:0.6;margin-top:4px;">{view_year}</div>'
        '<div style="text-align:center;margin-top:6px;font-size:12px;">'
        f'Current streak: <b {value}>{_plural(cur, "day")}</b> &nbsp; '
        f'Longest streak: <b {value}>{_plural(best, "day")}</b> &nbsp; '
        f'Days done: <b {value}>{done_n} ({pct}%)</b>'
        "</div></div>"
    )


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"
