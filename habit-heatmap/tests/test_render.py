from datetime import date, timedelta
from html.parser import HTMLParser

import pytest

from bitmap import Bitmap
from days import year_grid
from habits import Habit
from render import (
    NAV_CMD_PREFIX,
    NOTE_CMD_PREFIX,
    STATUS_DONE,
    STATUS_MISSED,
    STATUS_NOT_STARTED,
    STATUS_TODAY_DONE,
    STATUS_TODAY_TODO,
    STATUS_UPCOMING,
    TOGGLE_CMD_PREFIX,
    build_block_html,
    build_toolbar_html,
    day_status,
    format_day,
)
from themes import THEMES

TODAY = date(2026, 11, 11)  # Wednesday
T = TODAY.toordinal()
HABIT = Habit("h_abc123", "Exercise", "lime", T - 40, False)


def bits(*ordinals: int) -> Bitmap:
    bm = Bitmap()
    for o in ordinals:
        bm = bm.with_bit(o, True)
    return bm


def iso(o: int) -> str:
    return date.fromordinal(o).isoformat()


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells: dict[str, dict] = {}
        self.blanks = 0
        self.buttons: list[dict] = []
        self.tags: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        classes = (a.get("class") or "").split()
        if "hh-cell" in classes:
            self.cells[a["data-day"]] = a
        if "hh-blank" in classes:
            self.blanks += 1
        if tag == "button":
            self.buttons.append(a)


def block(habit=HABIT, ticked=(), notes=None, today=TODAY, view_year=2026):
    html = build_block_html(habit, bits(*ticked), notes or {}, today, view_year)
    c = Collector()
    c.feed(html)
    return html, c


# --- format_day / day_status ------------------------------------------------


def test_format_day_is_locale_independent_english():
    assert format_day(date(2026, 11, 11)) == "Wednesday, 11 Nov 2026"
    assert format_day(date(2026, 3, 1)) == "Sunday, 1 Mar 2026"


@pytest.mark.parametrize(
    "day,ticked,expected",
    [
        (TODAY + timedelta(days=1), set(), STATUS_UPCOMING),
        (TODAY, {T}, STATUS_TODAY_DONE),
        (TODAY, set(), STATUS_TODAY_TODO),
        (TODAY - timedelta(days=60), set(), STATUS_NOT_STARTED),
        (TODAY - timedelta(days=5), {T - 5}, STATUS_DONE),
        (TODAY - timedelta(days=5), set(), STATUS_MISSED),
        (TODAY - timedelta(days=40), set(), STATUS_MISSED),  # creation day itself counts as started
    ],
)
def test_day_status(day, ticked, expected):
    assert day_status(day, TODAY, T - 40, ticked) == expected


def test_status_labels_are_distinct_and_human_readable():
    labels = {STATUS_UPCOMING, STATUS_TODAY_DONE, STATUS_TODAY_TODO, STATUS_NOT_STARTED, STATUS_DONE, STATUS_MISSED}
    assert len(labels) == 6
    assert STATUS_TODAY_TODO == "Today - not done yet"


# --- grid -------------------------------------------------------------------


def test_grid_has_every_day_of_the_year_and_blank_padding_up_to_whole_weeks():
    _, c = block()
    cols = len(year_grid(2026))
    assert len(c.cells) == 365
    assert len(c.cells) + c.blanks == cols * 7


def test_cells_carry_iso_day_formatted_label_and_status():
    _, c = block(ticked=[T - 3])
    cell = c.cells[iso(T - 3)]
    assert cell["data-label"] == format_day(date.fromordinal(T - 3))
    assert cell["data-status"] == STATUS_DONE
    assert c.cells[iso(T)]["data-status"] == STATUS_TODAY_TODO
    assert c.cells[iso(T + 1)]["data-status"] == STATUS_UPCOMING
    assert c.cells[iso(T - 1)]["data-status"] == STATUS_MISSED
    assert c.cells[iso(T - 50)]["data-status"] == STATUS_NOT_STARTED


def test_done_cells_use_streak_dependent_shades_of_the_theme():
    _, c = block(ticked=[T - 2, T - 1, T])  # runs of 1, 2, 3 -> levels 1, 2, 2
    lime = THEMES["lime"]
    assert lime[0] in c.cells[iso(T - 2)]["style"]
    assert lime[1] in c.cells[iso(T - 1)]["style"]
    assert lime[1] in c.cells[iso(T)]["style"]


def test_long_streak_gets_the_darkest_shade():
    _, c = block(ticked=range(T - 14, T + 1))  # 15 consecutive days
    assert THEMES["lime"][4] in c.cells[iso(T)]["style"]


def test_theme_comes_from_the_habit_and_legacy_hex_maps_to_a_theme():
    ice = Habit("h_abc123", "X", "ice", T - 40, False)
    legacy = Habit("h_abc123", "X", "#4c8bf5", T - 40, False)
    _, c1 = block(habit=ice, ticked=[T - 3])
    _, c2 = block(habit=legacy, ticked=[T - 3])
    assert THEMES["ice"][0] in c1.cells[iso(T - 3)]["style"]
    assert c2.cells[iso(T - 3)]["style"] == c1.cells[iso(T - 3)]["style"]


def test_missed_not_started_and_upcoming_are_grey_and_distinct():
    _, c = block()
    styles = {c.cells[iso(d)]["style"] for d in (T - 1, T - 50, T + 1)}
    assert len(styles) == 3
    assert all("rgba(128,128,128" in s for s in styles)


def test_future_days_are_drawn_not_hidden():
    _, c = block()
    assert iso(date(2026, 12, 31).toordinal()) in c.cells


def test_todays_cell_has_an_outline():
    _, c = block()
    assert "outline" in c.cells[iso(T)]["style"]
    assert "outline" not in c.cells[iso(T - 1)]["style"]


# --- interactivity ----------------------------------------------------------


def test_only_todays_cell_toggles_the_tick():
    _, c = block(ticked=[T - 3])
    toggles = [d for d, a in c.cells.items() if TOGGLE_CMD_PREFIX in a.get("onclick", "")]
    assert toggles == [iso(T)]
    assert f"{TOGGLE_CMD_PREFIX}h_abc123" in c.cells[iso(T)]["onclick"]


def test_past_days_since_creation_open_the_note_dialog_for_that_exact_day():
    _, c = block()
    a = c.cells[iso(T - 5)]
    assert a["onclick"] == f"pycmd('{NOTE_CMD_PREFIX}h_abc123:{iso(T - 5)}')"
    assert a["data-hint"] == "Click to add a note"


def test_creation_day_is_noteable_but_the_day_before_is_not():
    _, c = block()
    assert "onclick" in c.cells[iso(T - 40)]
    assert "onclick" not in c.cells[iso(T - 41)]


def test_future_and_pre_creation_cells_are_not_clickable():
    _, c = block()
    for d in (T + 1, date(2026, 12, 31).toordinal(), T - 41, T - 300):
        a = c.cells[iso(d)]
        assert "onclick" not in a and not a.get("data-hint")


def test_hint_says_edit_when_a_note_exists():
    _, c = block(notes={str(T - 5): "was sick"})
    assert c.cells[iso(T - 5)]["data-hint"] == "Click to edit note"


def test_past_cells_never_carry_a_tick_toggle():
    _, c = block()
    assert all(TOGGLE_CMD_PREFIX not in a.get("onclick", "") for d, a in c.cells.items() if d != iso(T))


# --- notes ------------------------------------------------------------------


def test_cells_with_notes_are_marked_and_carry_the_text():
    _, c = block(notes={str(T - 5): "was sick\nflu"})
    a = c.cells[iso(T - 5)]
    assert "hh-note" in a["class"].split()
    assert a["data-note"] == "was sick\nflu"
    assert "hh-note" not in c.cells[iso(T - 4)]["class"].split()
    assert not c.cells[iso(T - 4)].get("data-note")


def test_note_text_cannot_break_out_of_the_attribute():
    evil = '"><script>alert(1)</script><img src=x onerror=alert(2)>'
    html, c = block(notes={str(T - 5): evil})
    assert "<script>" not in html and "<img" not in html
    assert c.cells[iso(T - 5)]["data-note"] == evil  # parsed back out intact


def test_native_title_fallback_contains_label_status_and_note():
    _, c = block(notes={str(T - 5): "was sick"})
    title = c.cells[iso(T - 5)]["title"]
    assert format_day(date.fromordinal(T - 5)) in title and STATUS_MISSED in title and "was sick" in title


# --- header buttons ---------------------------------------------------------


def test_current_year_shows_check_and_add_note_buttons():
    html, c = block()
    cmds = [b.get("onclick", "") for b in c.buttons]
    assert any(f"{TOGGLE_CMD_PREFIX}h_abc123" in x for x in cmds)
    assert any(f"{NOTE_CMD_PREFIX}h_abc123:{TODAY.isoformat()}" in x for x in cmds)
    assert "Check today" in html and "Add note" in html


def test_button_labels_reflect_state():
    html, _ = block(ticked=[T], notes={str(T): "done early"})
    assert "Done today" in html and "Check today" not in html
    assert "Edit note" in html and "Add note" not in html


def test_note_button_is_available_even_when_today_is_not_ticked():
    _, c = block()
    assert any(NOTE_CMD_PREFIX in b.get("onclick", "") for b in c.buttons)


def test_other_year_has_no_header_buttons_and_no_today_cell():
    habit = Habit("h_abc123", "X", "lime", date(2025, 3, 1).toordinal(), False)
    _, c = block(habit=habit, view_year=2025)
    assert c.buttons == []
    assert not any(TOGGLE_CMD_PREFIX in a.get("onclick", "") for a in c.cells.values())


def test_other_year_still_lets_you_add_notes_to_past_days():
    habit = Habit("h_abc123", "X", "lime", date(2025, 3, 1).toordinal(), False)
    _, c = block(habit=habit, view_year=2025)
    assert NOTE_CMD_PREFIX in c.cells["2025-06-01"]["onclick"]
    assert "onclick" not in c.cells["2025-02-28"]  # before creation


# --- stats, label, safety ---------------------------------------------------


def test_stats_line_shows_streaks_and_days_done():
    html, _ = block(ticked=[T, T - 1, T - 2])
    assert "Current streak:" in html and "3 days" in html
    assert "Longest streak:" in html and "Days done:" in html


def test_stats_use_the_whole_history_not_the_year_in_view():
    habit = Habit("h_abc123", "X", "lime", date(2025, 3, 1).toordinal(), False)
    html_now, _ = block(habit=habit, ticked=[T, T - 1], view_year=2026)
    html_prev, _ = block(habit=habit, ticked=[T, T - 1], view_year=2025)
    pick = lambda h: h[h.index("Current streak:") :]  # noqa: E731
    assert pick(html_now) == pick(html_prev)


def test_year_label_is_shown():
    html, _ = block(view_year=2026)
    assert ">2026<" in html


def test_block_itself_contains_no_style_or_script_tags():
    _, c = block(ticked=[T])
    assert "style" not in c.tags and "script" not in c.tags


def test_habit_name_is_escaped():
    habit = Habit("h_abc123", "<script>alert(1)</script>&", "lime", T - 40, False)
    html, _ = block(habit=habit)
    assert "<script>" not in html and "&lt;script&gt;" in html


@pytest.mark.parametrize("bad_id", ["a'b", 'a"b', "a b", "", "a);x("])
def test_unsafe_habit_id_is_rejected(bad_id):
    with pytest.raises(ValueError):
        block(habit=Habit(bad_id, "X", "lime", T - 40, False))


# --- toolbar ----------------------------------------------------------------


def toolbar(view_year, lo, hi):
    c = Collector()
    c.feed(build_toolbar_html(view_year, lo, hi))
    return c.buttons


def test_toolbar_has_prev_today_next_commands():
    cmds = [b["onclick"] for b in toolbar(2026, 2024, 2026)]
    assert cmds == [
        f"pycmd('{NAV_CMD_PREFIX}prev')",
        f"pycmd('{NAV_CMD_PREFIX}today')",
        f"pycmd('{NAV_CMD_PREFIX}next')",
    ]


def test_toolbar_disables_prev_at_the_earliest_year_and_next_at_the_latest():
    prev, today, nxt = toolbar(2024, 2024, 2026)
    assert "disabled" in prev and "disabled" not in nxt
    prev, today, nxt = toolbar(2026, 2024, 2026)
    assert "disabled" in nxt and "disabled" not in prev
    assert "disabled" not in today


def test_toolbar_with_a_single_year_disables_both_arrows():
    prev, _, nxt = toolbar(2026, 2026, 2026)
    assert "disabled" in prev and "disabled" in nxt
