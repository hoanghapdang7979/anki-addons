"""Habit Heatmap - Task 1/2 spike: one hard-coded habit rendered on the deck
browser, toggled via pycmd and persisted with col.set_config. Replaced by the
real store-backed wiring in Task 9.
"""

import logging

import aqt
from aqt import gui_hooks
from aqt.deckbrowser import DeckBrowser

from .bitmap import Bitmap, toggle_today
from .days import anki_today
from .habits import PALETTE, Habit
from .render import TOGGLE_CMD_PREFIX, build_block_html

logger = logging.getLogger(__name__)

SPIKE_ID = "spike"
SPIKE_KEY = "habitHeatmap.spike"


def _load(col) -> Bitmap:
    try:
        return Bitmap.from_dict(col.get_config(SPIKE_KEY))
    except ValueError:
        logger.exception("corrupt %s, showing empty bitmap (not overwriting)", SPIKE_KEY)
        return Bitmap()


def _on_deck_browser_render(deck_browser: DeckBrowser, content) -> None:
    col = aqt.mw.col
    today = anki_today(col.sched.day_cutoff)
    habit = Habit(SPIKE_ID, "Spike habit (Task 2)", PALETTE[0], today.toordinal() - 30)
    content.stats += build_block_html(habit, _load(col), today)


def _on_js_message(handled: tuple[bool, object], message: str, context: object):
    if handled[0] or not message.startswith(TOGGLE_CMD_PREFIX):
        return handled
    if not isinstance(context, DeckBrowser):
        return handled
    if message[len(TOGGLE_CMD_PREFIX) :] != SPIKE_ID:
        return handled
    col = aqt.mw.col
    today = anki_today(col.sched.day_cutoff)
    col.set_config(SPIKE_KEY, toggle_today(_load(col), today).to_dict())
    context.refresh()
    return (True, None)


gui_hooks.deck_browser_will_render_content.append(_on_deck_browser_render)
gui_hooks.webview_did_receive_js_message.append(_on_js_message)
logger.info("Habit Heatmap loaded")
