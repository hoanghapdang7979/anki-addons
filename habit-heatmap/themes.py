"""Colour themes for the heatmap (the first five follow the Review Heatmap
add-on) and the streak -> shade mapping. No aqt/anki imports.

`Habit.color` stores a theme name. Hex values written by v1 are mapped to a
theme when read; nothing is migrated on disk.
"""

# Five shades per theme, light -> dark (level 1 = a streak of one day).
THEMES: dict[str, list[str]] = {
    "lime": ["#9be9a8", "#40c463", "#30a14e", "#216e39", "#0d4429"],
    "olive": ["#e5e0a8", "#c4c06a", "#9a9a3c", "#6e7326", "#464b14"],
    "ice": ["#c6e2ff", "#79b8ff", "#2f81f7", "#1158c7", "#0a3069"],
    "magenta": ["#fbcfe8", "#f08ac8", "#d13fa3", "#9b1d79", "#661252"],
    "flame": ["#ffe0a3", "#ffb454", "#f47b20", "#d1451b", "#8f2410"],
    "teal": ["#b2f0e8", "#5dd5c6", "#1fb5a3", "#0f857a", "#074f49"],
    "purple": ["#e5d4fb", "#c4a1f2", "#9a63e0", "#6f35b8", "#43206f"],
    "crimson": ["#fbc4c4", "#f08080", "#dc3a3a", "#a82020", "#661212"],
    "gold": ["#fbeab0", "#f5d062", "#e0aa1a", "#b07d0a", "#6e4c05"],
    "indigo": ["#c9d0fb", "#8f9cf0", "#5a68d8", "#3744a8", "#1f2766"],
    "rose": ["#fdd5e0", "#f9a3bd", "#ee6a95", "#c73a6c", "#872046"],
    "slate": ["#d7dce2", "#aab3be", "#7c8896", "#525d6b", "#2e3641"],
}
THEME_NAMES = list(THEMES)
LEVELS = 5

_LEGACY_HEX = {
    "#40c463": "lime",
    "#30a14e": "lime",
    "#216e39": "lime",
    "#4c8bf5": "ice",
    "#a371f7": "magenta",
    "#f78166": "flame",
    "#e3b341": "olive",
}


def resolve_theme(color: str) -> str:
    if color in THEMES:
        return color
    return _LEGACY_HEX.get(color.lower(), "lime")


def streak_level(run: int) -> int:
    """Shade level for a done day that ends a run of `run` consecutive done days."""
    if run >= 14:
        return 5
    if run >= 7:
        return 4
    if run >= 4:
        return 3
    if run >= 2:
        return 2
    return 1


def shade(theme: str, level: int) -> str:
    colors = THEMES[resolve_theme(theme)]
    return colors[max(1, min(LEVELS, level)) - 1]
