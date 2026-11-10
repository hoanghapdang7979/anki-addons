"""Pure habit-list operations (add/rename/recolor/reorder/archive/delete) and
(de)serialisation. Every function returns a new list; nothing is mutated.
No aqt/anki imports.
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, replace

# Default colours handed to new habits, in turn. Habit.color holds a theme name
# (see themes.py); hex values written by v1 are mapped to a theme when read.
PALETTE = ["lime", "ice", "flame", "magenta", "olive"]


@dataclass(frozen=True)
class Habit:
    id: str
    name: str
    color: str
    created: int  # date ordinal of the day the habit was added
    archived: bool = False


def _new_id() -> str:
    return "h_" + uuid.uuid4().hex[:8]


def _clean_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("habit name must not be blank")
    return name


def _index(habits: list[Habit], habit_id: str) -> int:
    for i, h in enumerate(habits):
        if h.id == habit_id:
            return i
    raise KeyError(habit_id)


def _replace(habits: list[Habit], habit_id: str, **changes) -> list[Habit]:
    i = _index(habits, habit_id)
    return habits[:i] + [replace(habits[i], **changes)] + habits[i + 1 :]


def add_habit(
    habits: list[Habit],
    name: str,
    color: str,
    today: int,
    id_factory: Callable[[], str] = _new_id,
) -> list[Habit]:
    return habits + [Habit(id_factory(), _clean_name(name), color, today, False)]


def rename_habit(habits: list[Habit], habit_id: str, name: str) -> list[Habit]:
    return _replace(habits, habit_id, name=_clean_name(name))


def recolor_habit(habits: list[Habit], habit_id: str, color: str) -> list[Habit]:
    return _replace(habits, habit_id, color=color)


def move_habit(habits: list[Habit], habit_id: str, delta: int) -> list[Habit]:
    i = _index(habits, habit_id)
    j = max(0, min(len(habits) - 1, i + delta))
    out = list(habits)
    out.insert(j, out.pop(i))
    return out


def archive_habit(habits: list[Habit], habit_id: str) -> list[Habit]:
    return _replace(habits, habit_id, archived=True)


def restore_habit(habits: list[Habit], habit_id: str) -> list[Habit]:
    return _replace(habits, habit_id, archived=False)


def delete_habit(habits: list[Habit], habit_id: str) -> list[Habit]:
    i = _index(habits, habit_id)
    return habits[:i] + habits[i + 1 :]


def active(habits: list[Habit]) -> list[Habit]:
    return [h for h in habits if not h.archived]


def archived(habits: list[Habit]) -> list[Habit]:
    return [h for h in habits if h.archived]


def orphan_ids(habits: list[Habit], stored_ids: set[str]) -> set[str]:
    """Ids that have stored tick data but no entry in the habit list."""
    return stored_ids - {h.id for h in habits}


def habits_to_json(habits: list[Habit]) -> list[dict]:
    return [
        {"id": h.id, "name": h.name, "color": h.color, "created": h.created, "archived": h.archived}
        for h in habits
    ]


def habits_from_json(raw: list | None) -> list[Habit]:
    """Raises ValueError on malformed data rather than silently dropping habits."""
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("habit list must be a list")
    out: list[Habit] = []
    for item in raw:
        try:
            out.append(
                Habit(
                    id=str(item["id"]),
                    name=str(item["name"]),
                    color=str(item["color"]),
                    created=int(item["created"]),
                    archived=bool(item.get("archived", False)),
                )
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ValueError(f"malformed habit entry: {item!r}") from exc
    return out


def reorder(habits: list[Habit], ordered_ids: list[str]) -> list[Habit]:
    """Habits in the given id order. Unknown/duplicate ids are ignored; habits not
    mentioned keep their relative order at the end."""
    by_id = {h.id: h for h in habits}
    seen: set[str] = set()
    out: list[Habit] = []
    for hid in ordered_ids:
        if hid in by_id and hid not in seen:
            out.append(by_id[hid])
            seen.add(hid)
    return out + [h for h in habits if h.id not in seen]


def priority_numbers(habits: list[Habit]) -> dict[str, int]:
    """1-based priority of each active habit (list order = priority order)."""
    return {h.id: n for n, h in enumerate(active(habits), start=1)}
