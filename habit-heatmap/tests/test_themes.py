import re

import pytest

from stats import streak_runs
from themes import LEVELS, THEME_NAMES, THEMES, resolve_theme, shade, streak_level

HEX = re.compile(r"^#[0-9a-f]{6}$")


def test_there_are_five_named_themes_each_with_five_levels():
    assert THEME_NAMES == ["lime", "olive", "ice", "magenta", "flame"]
    assert LEVELS == 5
    for name in THEME_NAMES:
        assert len(THEMES[name]) == 5
        assert all(HEX.match(c) for c in THEMES[name])


def test_levels_get_progressively_darker():
    def luminance(h):
        r, g, b = (int(h[i : i + 2], 16) for i in (1, 3, 5))
        return 0.299 * r + 0.587 * g + 0.114 * b

    for name in THEME_NAMES:
        lums = [luminance(c) for c in THEMES[name]]
        assert lums == sorted(lums, reverse=True), name


@pytest.mark.parametrize(
    "run,level",
    [(1, 1), (2, 2), (3, 2), (4, 3), (6, 3), (7, 4), (13, 4), (14, 5), (400, 5)],
)
def test_streak_level_boundaries(run, level):
    assert streak_level(run) == level


def test_streak_level_for_nonpositive_run_is_the_lowest_level():
    assert streak_level(0) == 1


def test_shade_returns_the_theme_colour_for_a_level():
    assert shade("lime", 1) == THEMES["lime"][0]
    assert shade("flame", 5) == THEMES["flame"][4]


def test_shade_clamps_the_level():
    assert shade("ice", 0) == THEMES["ice"][0]
    assert shade("ice", 99) == THEMES["ice"][4]


def test_resolve_theme_accepts_theme_names():
    assert resolve_theme("magenta") == "magenta"


@pytest.mark.parametrize(
    "legacy,theme",
    [
        ("#40c463", "lime"),
        ("#30a14e", "lime"),
        ("#216e39", "lime"),
        ("#4c8bf5", "ice"),
        ("#a371f7", "magenta"),
        ("#f78166", "flame"),
        ("#e3b341", "olive"),
    ],
)
def test_resolve_theme_maps_v1_hex_colours(legacy, theme):
    assert resolve_theme(legacy) == theme


def test_resolve_theme_falls_back_to_lime_for_anything_unknown():
    assert resolve_theme("#123456") == "lime"
    assert resolve_theme("") == "lime"
    assert resolve_theme("javascript:alert(1)") == "lime"


def test_streak_runs_counts_consecutive_days_ending_at_each_tick():
    assert streak_runs({10, 11, 12, 20, 22, 23}) == {10: 1, 11: 2, 12: 3, 20: 1, 22: 1, 23: 2}


def test_streak_runs_empty():
    assert streak_runs(set()) == {}
