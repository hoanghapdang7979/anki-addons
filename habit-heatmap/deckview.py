"""Deck-browser integration: render the year toolbar and one heatmap block per
active habit, and handle the page's three commands (toggle today, note, nav).
Touches aqt; the logic lives in the pure modules.

Both hooks run on the main screen, so they must never raise: any unexpected
error is logged and the screen renders without the heatmap.

Trust boundary: the page can only send a habit id and, for notes, an ISO date.
The tick command carries no date at all (Python computes today); the note
command's date is parsed and range-checked in Store.set_note. Note text never
comes from the page - it is typed in a Qt dialog.
"""

import html as html_lib
import logging
from datetime import date

import aqt
from aqt import gui_hooks
from aqt.deckbrowser import DeckBrowser
from aqt.qt import QInputDialog
from aqt.utils import tooltip

from .assets import build_assets_html
from .context import make_store
from .days import MAX_VIEW_YEAR, MIN_VIEW_YEAR, anki_today, navigate_year
from .habits import active
from .notes import MAX_NOTE_CHARS, NoteStorageFull, parse_note_arg
from .render import (
    NAV_CMD_PREFIX,
    NOTE_CMD_PREFIX,
    TOGGLE_CMD_PREFIX,
    build_block_html,
    build_toolbar_html,
    format_day,
)

logger = logging.getLogger(__name__)

# Year being viewed; None = the current year. In memory only, so every Anki
# start opens on the current year.
_view_year: int | None = None


def _notice(text: str) -> str:
    return (
        '<div style="margin:12px auto;max-width:720px;padding:0 8px;font-size:12px;'
        f'opacity:0.85;">{html_lib.escape(text)}</div>'
    )


def _render_blocks(content) -> None:
    col = aqt.mw.col
    store = make_store()
    today = anki_today(col.sched.day_cutoff)
    try:
        habits = active(store.habits())
    except ValueError:
        logger.exception("habit list is unreadable; not rendering, not overwriting")
        content.stats += _notice("Habit Heatmap: habit list is unreadable (left untouched).")
        return
    if not habits:
        content.stats += _notice("Habit Heatmap: no habits yet - add one from Tools > Habit Heatmap...")
        return

    view_year = navigate_year(_view_year, "stay", today.year, MIN_VIEW_YEAR, MAX_VIEW_YEAR)
    content.stats += build_toolbar_html(view_year, MIN_VIEW_YEAR, MAX_VIEW_YEAR)
    for habit in habits:
        try:
            content.stats += build_block_html(
                habit, store.bitmap(habit.id), store.notes(habit.id), today, view_year
            )
        except ValueError:
            logger.exception("data for habit %s is unreadable", habit.id)
            content.stats += _notice(
                f"Habit Heatmap: data for '{habit.name}' is unreadable (left untouched)."
            )
    content.stats += build_assets_html()


def _on_deck_browser_render(deck_browser: DeckBrowser, content) -> None:
    try:
        _render_blocks(content)
    except Exception:
        logger.exception("Habit Heatmap failed to render; showing the screen without it")


def _do_toggle(habit_id: str) -> None:
    col = aqt.mw.col
    make_store().toggle_today(habit_id, anki_today(col.sched.day_cutoff))


def _do_nav(command: str) -> None:
    global _view_year
    col = aqt.mw.col
    today = anki_today(col.sched.day_cutoff)
    _view_year = navigate_year(_view_year, command, today.year, MIN_VIEW_YEAR, MAX_VIEW_YEAR)


def _do_note(arg: str) -> None:
    parsed = parse_note_arg(arg)
    if parsed is None:
        logger.warning("ignored malformed note command %r", arg)
        return
    habit_id, day = parsed
    col = aqt.mw.col
    store = make_store()
    today = anki_today(col.sched.day_cutoff)
    habit = next((h for h in active(store.habits()) if h.id == habit_id), None)
    if habit is None:
        tooltip("Habit Heatmap: that habit no longer exists.")
        return
    existing = store.notes(habit_id).get(str(day.toordinal()), "")
    text, accepted = QInputDialog.getMultiLineText(
        aqt.mw,
        f"Note - {habit.name}",
        f"{format_day(day)}  (up to {MAX_NOTE_CHARS} characters; leave empty to delete)",
        existing,
    )
    if not accepted:
        return
    try:
        truncated = store.set_note(habit_id, day, text, today)
    except NoteStorageFull:
        tooltip("Habit Heatmap: the notes of this habit are full - shorten or delete some.")
        return
    if truncated:
        tooltip(f"Note shortened to {MAX_NOTE_CHARS} characters")


def _on_js_message(handled: tuple[bool, object], message: str, context: object):
    if handled[0] or not isinstance(context, DeckBrowser):
        return handled
    try:
        if message.startswith(TOGGLE_CMD_PREFIX):
            _do_toggle(message[len(TOGGLE_CMD_PREFIX) :])
        elif message.startswith(NOTE_CMD_PREFIX):
            _do_note(message[len(NOTE_CMD_PREFIX) :])
        elif message.startswith(NAV_CMD_PREFIX):
            _do_nav(message[len(NAV_CMD_PREFIX) :])
        else:
            return handled
    except (KeyError, ValueError):
        logger.warning("refused command %r", message, exc_info=True)
        tooltip("Habit Heatmap: could not update this habit.")
    except Exception:
        logger.exception("Habit Heatmap: unexpected error while handling %r", message)
        tooltip("Habit Heatmap: unexpected error (see the log).")
    context.refresh()
    return (True, None)


def register() -> None:
    gui_hooks.deck_browser_will_render_content.append(_on_deck_browser_render)
    gui_hooks.webview_did_receive_js_message.append(_on_js_message)
