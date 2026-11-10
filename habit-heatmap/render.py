"""Pure HTML rendering of one habit's heatmap block.

Inline styles only (no <style>/<script>): the block is injected into Anki's
deck-browser page next to other add-ons' content, and must not depend on or
clash with their CSS. No aqt/anki imports.
"""

import html as html_lib
import re
from datetime import date

try:
    from .bitmap import Bitmap
    from .days import build_grid
    from .habits import PALETTE, Habit
    from .stats import completion_pct, current_streak, days_done, longest_streak
except ImportError:  # pytest: modules are top-level via conftest.py sys.path
    from bitmap import Bitmap
    from days import build_grid
    from habits import PALETTE, Habit
    from stats import completion_pct, current_streak, days_done, longest_streak

TOGGLE_CMD_PREFIX = "habitheatmap:toggle:"
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{3,8}$")
_TODO_BG = "rgba(128,128,128,0.22)"


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _toggle_onclick(habit_id: str) -> str:
    return f"pycmd('{TOGGLE_CMD_PREFIX}{habit_id}')"


def build_block_html(habit: Habit, bitmap: Bitmap, today: date) -> str:
    """Render one habit as a header (name + today button), a 53x7 grid and a stats line.

    Only today's cell and the header button carry an onclick; past cells are
    never interactive. Raises ValueError for a habit id that is not safe to
    embed in an inline JS string.
    """
    if not _SAFE_ID_RE.match(habit.id):
        raise ValueError(f"unsafe habit id: {habit.id!r}")
    color = habit.color if _COLOR_RE.match(habit.color) else PALETTE[0]
    onclick = _toggle_onclick(habit.id)
    ticked = bitmap.ticked_ordinals()
    today_ord = today.toordinal()
    grid = build_grid(today)

    slots: list[str] = []
    for column in grid:
        for cell in column:
            if cell is None:
                slots.append('<div data-slot style="visibility:hidden;aspect-ratio:1/1;"></div>')
                continue
            done = cell.toordinal() in ticked
            style = f"aspect-ratio:1/1;border-radius:2px;background:{color if done else _TODO_BG};"
            attrs = f'title="{cell.isoformat()}"'
            if cell == today:
                style += "outline:1.5px solid currentColor;outline-offset:1px;cursor:pointer;"
                attrs += f' onclick="{onclick}"'
            slots.append(
                f'<div data-slot data-day="{cell.isoformat()}" '
                f'data-state="{"done" if done else "todo"}" {attrs} style="{style}"></div>'
            )

    start = max(grid[0][0].toordinal(), habit.created)
    cur = current_streak(ticked, today_ord)
    best = longest_streak(ticked, today_ord)
    done_n = days_done(ticked, today_ord)
    pct = completion_pct(ticked, start, today_ord)
    label = "&#10003; Done today (click to undo)" if today_ord in ticked else "Check today"
    name = html_lib.escape(habit.name)

    return (
        '<div class="habit-heatmap" style="margin:18px auto;max-width:720px;padding:0 8px;">'
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
        f'<span style="font-weight:700;"><span style="color:{color};">&#9679;</span> {name}</span>'
        f'<button onclick="{onclick}">{label}</button>'
        "</div>"
        '<div style="display:grid;grid-template-columns:repeat(53,minmax(0,1fr));'
        f'grid-auto-flow:column;grid-template-rows:repeat(7,auto);gap:2px;">{"".join(slots)}</div>'
        '<div style="margin-top:6px;font-size:12px;opacity:0.85;">'
        f"Current streak: {_plural(cur, 'day')} &nbsp; "
        f"Longest streak: {_plural(best, 'day')} &nbsp; "
        f"Days done: {done_n} ({pct}%)"
        "</div></div>"
    )
