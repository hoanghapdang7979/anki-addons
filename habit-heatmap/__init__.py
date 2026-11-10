"""Habit Heatmap: one heatmap block per habit on the deck-browser screen, tick
today only, data kept in the collection config (rides AnkiWeb sync) with a
local per-profile shadow backup merged back by union."""

import logging

import aqt
from aqt import gui_hooks

from . import deckview, manage_dialog
from .context import make_store
from .reconcile import reconcile

logger = logging.getLogger(__name__)

_LEGACY_SPIKE_KEY = "habitHeatmap.spike"  # left over from the Task 1-2 spike


def _reconcile_now() -> None:
    """Never raise into Anki's profile-open/sync flow."""
    try:
        col = aqt.mw.col
        if col is None:
            return
        if col.get_config(_LEGACY_SPIKE_KEY) is not None:
            col.remove_config(_LEGACY_SPIKE_KEY)
        reconcile(make_store())
    except Exception:
        logger.exception("Habit Heatmap: reconcile failed")


deckview.register()
manage_dialog.register()
gui_hooks.profile_did_open.append(_reconcile_now)
gui_hooks.sync_did_finish.append(_reconcile_now)
logger.info("Habit Heatmap loaded")
