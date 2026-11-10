"""Deck-browser integration: render one heatmap block per active habit and
handle the "check today" click. Touches aqt; logic lives in the pure modules.
"""

import html as html_lib
import logging

import aqt
from aqt import gui_hooks
from aqt.deckbrowser import DeckBrowser
from aqt.utils import tooltip

from .days import anki_today
from .habits import active
from .render import TOGGLE_CMD_PREFIX, build_block_html
from .store import Store

logger = logging.getLogger(__name__)


def _notice(text: str) -> str:
    return (
        '<div style="margin:12px auto;max-width:720px;padding:0 8px;font-size:12px;'
        f'opacity:0.85;">{html_lib.escape(text)}</div>'
    )


def _on_deck_browser_render(deck_browser: DeckBrowser, content) -> None:
    col = aqt.mw.col
    store = Store(col)
    today = anki_today(col.sched.day_cutoff)
    try:
        habits = active(store.habits())
    except ValueError:
        logger.exception("habit list is unreadable; not rendering, not overwriting")
        content.stats += _notice("Habit Heatmap: habit list is unreadable (left untouched).")
        return
    for habit in habits:
        try:
            content.stats += build_block_html(habit, store.bitmap(habit.id), today)
        except ValueError:
            logger.exception("data for habit %s is unreadable", habit.id)
            content.stats += _notice(f"Habit Heatmap: data for '{habit.name}' is unreadable (left untouched).")


def _on_js_message(handled: tuple[bool, object], message: str, context: object):
    if handled[0] or not message.startswith(TOGGLE_CMD_PREFIX):
        return handled
    if not isinstance(context, DeckBrowser):
        return handled
    habit_id = message[len(TOGGLE_CMD_PREFIX) :]
    col = aqt.mw.col
    try:
        Store(col).toggle_today(habit_id, anki_today(col.sched.day_cutoff))
    except (KeyError, ValueError):
        logger.warning("toggle refused for habit %r", habit_id, exc_info=True)
        tooltip("Habit Heatmap: could not update this habit.")
    context.refresh()
    return (True, None)


def register() -> None:
    gui_hooks.deck_browser_will_render_content.append(_on_deck_browser_render)
    gui_hooks.webview_did_receive_js_message.append(_on_js_message)
