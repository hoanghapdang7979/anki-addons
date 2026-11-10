"""Deck-browser integration: render one heatmap block per active habit and
handle the "check today" click. Touches aqt; logic lives in the pure modules.

Both hooks run on the main screen, so they must never raise: any unexpected
error is logged and the screen renders without the heatmap.
"""

import html as html_lib
import logging

import aqt
from aqt import gui_hooks
from aqt.deckbrowser import DeckBrowser
from aqt.utils import tooltip

from .context import make_store
from .days import anki_today
from .habits import active
from .render import TOGGLE_CMD_PREFIX, build_block_html

logger = logging.getLogger(__name__)


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
    for habit in habits:
        try:
            content.stats += build_block_html(habit, store.bitmap(habit.id), today)
        except ValueError:
            logger.exception("data for habit %s is unreadable", habit.id)
            content.stats += _notice(
                f"Habit Heatmap: data for '{habit.name}' is unreadable (left untouched)."
            )


def _on_deck_browser_render(deck_browser: DeckBrowser, content) -> None:
    try:
        _render_blocks(content)
    except Exception:
        logger.exception("Habit Heatmap failed to render; showing the screen without it")


def _on_js_message(handled: tuple[bool, object], message: str, context: object):
    if handled[0] or not message.startswith(TOGGLE_CMD_PREFIX):
        return handled
    if not isinstance(context, DeckBrowser):
        return handled
    habit_id = message[len(TOGGLE_CMD_PREFIX) :]
    try:
        col = aqt.mw.col
        make_store().toggle_today(habit_id, anki_today(col.sched.day_cutoff))
    except (KeyError, ValueError):
        logger.warning("toggle refused for habit %r", habit_id, exc_info=True)
        tooltip("Habit Heatmap: could not update this habit.")
    except Exception:
        logger.exception("Habit Heatmap: unexpected error while toggling %r", habit_id)
        tooltip("Habit Heatmap: unexpected error (see the log).")
    context.refresh()
    return (True, None)


def register() -> None:
    gui_hooks.deck_browser_will_render_content.append(_on_deck_browser_render)
    gui_hooks.webview_did_receive_js_message.append(_on_js_message)
