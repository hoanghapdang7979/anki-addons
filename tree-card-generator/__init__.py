import logging

from aqt import gui_hooks, mw
from aqt.qt import QApplication, QMimeData

logger = logging.getLogger(__name__)

# TEMPORARY (Task 2 of tasks/plan.md): verifies QMimeData.setHtml() actually
# pastes as rendered HTML into Anki's current NewEditor, not as escaped
# plain text. This is the highest-risk unverified assumption in SPEC.md -
# checking it before writing the real parser/renderer/dialog. Remove this
# button once Task 5 replaces it with the real "Tree Card" button.
_TEST_HTML = "<b>test bold</b><br><span style='color:red'>red text</span>"


def _on_test_clipboard_button(editor) -> None:
    mime = QMimeData()
    mime.setHtml(_TEST_HTML)
    QApplication.clipboard().setMimeData(mime)
    logger.info("Copied test HTML to clipboard via QMimeData.setHtml()")


def _add_test_clipboard_button(buttons: list[str], editor) -> None:
    button = editor.addButton(
        None,
        "test_clipboard_html",
        _on_test_clipboard_button,
        tip="[TEMP Task 2] Copy test HTML to clipboard",
        label="TestClipHTML",
    )
    buttons.append(button)


gui_hooks.editor_did_init_buttons.append(_add_test_clipboard_button)

logger.info("Tree Card Generator loaded")
