"""Habit Heatmap: one heatmap block per habit on the deck-browser screen, tick
today only, data kept in the collection config (rides AnkiWeb sync) with a
local per-profile shadow backup that is three-way merged after each sync."""

import logging
import time

import aqt
from aqt import gui_hooks

from . import deckview, manage_dialog
from .context import make_store
from .reconcile import reconcile, should_followup

logger = logging.getLogger(__name__)

_LEGACY_SPIKE_KEY = "habitHeatmap.spike"  # left over from the Task 1-2 spike
_FOLLOWUP_DELAY_MS = 1500

_last_followup_at: float | None = None


def _reconcile_now() -> bool:
    """Merge config with the local shadow. Never raises into Anki. True if it wrote."""
    try:
        col = aqt.mw.col
        if col is None:
            return False
        if col.get_config(_LEGACY_SPIKE_KEY) is not None:
            col.remove_config(_LEGACY_SPIKE_KEY)
        return reconcile(make_store())
    except Exception:
        logger.exception("Habit Heatmap: reconcile failed")
        return False


def _on_profile_open() -> None:
    _reconcile_now()


def _on_sync_did_finish() -> None:
    """Note: Anki fires this even when the sync failed; reconcile is safe either way.

    If the merge had to write the config back, push it with one more sync soon:
    Anki lets a machine's config change win only if no other machine synced since
    it was written, so waiting for the next manual sync could lose the race again.
    """
    global _last_followup_at
    wrote = _reconcile_now()
    now = time.monotonic()
    if should_followup(wrote, _last_followup_at, now):
        _last_followup_at = now
        aqt.mw.progress.single_shot(_FOLLOWUP_DELAY_MS, _run_followup_sync)


def _run_followup_sync() -> None:
    try:
        mw = aqt.mw
        if mw.col is None or not mw.pm.sync_auth() or mw.media_syncer.is_syncing():
            return
        mw.on_sync_button_clicked()
    except Exception:
        logger.exception("Habit Heatmap: follow-up sync failed to start")


deckview.register()
manage_dialog.register()
gui_hooks.profile_did_open.append(_on_profile_open)
gui_hooks.sync_did_finish.append(_on_sync_did_finish)
logger.info("Habit Heatmap loaded")
