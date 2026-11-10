import logging
from typing import Any

# Import order matters here: anki.hooks -> anki.hooks_gen -> anki.cards ->
# anki.collection -> ... -> anki.models hits a circular import in anki
# 26.8.1 if anki.collection hasn't been fully imported yet. Anki's own
# bootstrap always imports anki.collection early (it builds mw.col before
# any add-on loads), so this never surfaces in a real Anki session - only
# when anki.hooks is imported in isolation (e.g. under pytest). Importing
# it first here sidesteps the cycle without patching the anki package.
import anki.collection  # noqa: F401
from anki import hooks
from aqt import gui_hooks, mw
from aqt.reviewer import Reviewer
from aqt.webview import WebContent

from .editor_hook import edit_field_filter, parse_save_message

logger = logging.getLogger(__name__)

hooks.field_filter.append(edit_field_filter)


def _addon_package() -> str:
    return mw.addonManager.addonFromModule(__name__)


def _on_webview_will_set_content(web_content: WebContent, context: Any) -> None:
    if not isinstance(context, Reviewer):
        return
    web_content.js.append(f"/_addons/{_addon_package()}/web/inline_edit.js")


def _on_webview_did_receive_js_message(
    handled: tuple[bool, Any], message: str, context: Any
) -> tuple[bool, Any]:
    if not isinstance(context, Reviewer):
        return handled
    parsed = parse_save_message(message)
    if parsed is None:
        return handled

    field_name, new_html = parsed
    note = context.card.note()
    if field_name not in note:
        logger.warning(
            "Inline Field Editor: unknown field %r, ignoring save", field_name
        )
        return (True, None)

    note[field_name] = new_html
    mw.col.update_note(note)
    return (True, None)


gui_hooks.webview_will_set_content.append(_on_webview_will_set_content)
gui_hooks.webview_did_receive_js_message.append(_on_webview_did_receive_js_message)

logger.info("Inline Field Editor loaded")
