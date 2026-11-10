from datetime import date
from html.parser import HTMLParser

import pytest

from bitmap import Bitmap
from habits import Habit
from render import build_block_html

TODAY = date(2026, 11, 11)  # Wednesday
T = TODAY.toordinal()
HABIT = Habit("h_abc123", "Exercise", "#40c463", T - 400, False)


def bits(*ordinals: int) -> Bitmap:
    bm = Bitmap()
    for o in ordinals:
        bm = bm.with_bit(o, True)
    return bm


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells: list[dict] = []
        self.buttons: list[dict] = []
        self.tags: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        if "data-day" in a:
            self.cells.append(a)
        if tag == "button":
            self.buttons.append(a)


def parse(html: str) -> Collector:
    c = Collector()
    c.feed(html)
    return c


def test_visible_cell_count_is_52_weeks_plus_this_week_so_far():
    c = parse(build_block_html(HABIT, bits(), TODAY))
    assert len(c.cells) == 52 * 7 + TODAY.weekday() + 1


def test_total_grid_slots_is_53_by_7_including_future_placeholders():
    html = build_block_html(HABIT, bits(), TODAY)
    assert html.count("data-slot") == 53 * 7


def test_done_cells_match_ticks_and_use_habit_color():
    c = parse(build_block_html(HABIT, bits(T, T - 1, T - 30), TODAY))
    done = [x for x in c.cells if x["data-state"] == "done"]
    assert sorted(x["data-day"] for x in done) == sorted(
        date.fromordinal(o).isoformat() for o in (T, T - 1, T - 30)
    )
    assert all("#40c463" in x["style"] for x in done)
    todo = [x for x in c.cells if x["data-state"] == "todo"]
    assert all("#40c463" not in x["style"] for x in todo)


def test_only_todays_cell_is_clickable():
    c = parse(build_block_html(HABIT, bits(T - 3), TODAY))
    clickable = [x for x in c.cells if "onclick" in x]
    assert [x["data-day"] for x in clickable] == [TODAY.isoformat()]
    assert "habitheatmap:toggle:h_abc123" in clickable[0]["onclick"]


def test_button_toggles_same_habit_and_label_reflects_state():
    undone = parse(build_block_html(HABIT, bits(), TODAY))
    done = parse(build_block_html(HABIT, bits(T), TODAY))
    assert "habitheatmap:toggle:h_abc123" in undone.buttons[0]["onclick"]
    assert "habitheatmap:toggle:h_abc123" in done.buttons[0]["onclick"]
    assert "Check today" in build_block_html(HABIT, bits(), TODAY)
    assert "Check today" not in build_block_html(HABIT, bits(T), TODAY)
    assert "Done" in build_block_html(HABIT, bits(T), TODAY)


def test_habit_name_is_escaped():
    habit = Habit("h_abc123", "<script>alert(1)</script>&", "#40c463", T, False)
    html = build_block_html(habit, bits(), TODAY)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_no_style_or_script_blocks():
    tags = parse(build_block_html(HABIT, bits(T), TODAY)).tags
    assert "style" not in tags and "script" not in tags


@pytest.mark.parametrize("bad_id", ["a'b", 'a"b', "a b", "", "a);x("])
def test_unsafe_habit_id_is_rejected(bad_id):
    habit = Habit(bad_id, "X", "#40c463", T, False)
    with pytest.raises(ValueError):
        build_block_html(habit, bits(), TODAY)


def test_stats_line_shows_streaks_and_days_done():
    html = build_block_html(HABIT, bits(T, T - 1, T - 2), TODAY)
    assert "Current streak: 3 days" in html
    assert "Longest streak: 3 days" in html
    assert "Days done: 3" in html


def test_stats_percent_uses_window_since_habit_was_created():
    habit = Habit("h_abc123", "X", "#40c463", T - 3, False)  # 4-day window
    html = build_block_html(habit, bits(T, T - 1), TODAY)
    assert "50%" in html
