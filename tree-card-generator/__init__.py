import logging

from aqt import gui_hooks

from .dialog import TreeDialog

logger = logging.getLogger(__name__)

# Kept alive here so Qt doesn't garbage-collect the dialog while it's open
# (PyQt does not keep a Python-side reference alive on its own).
_dialog_instance: TreeDialog | None = None


def _open_tree_dialog(editor) -> None:
    global _dialog_instance
    _dialog_instance = TreeDialog(editor, editor.parentWindow)
    _dialog_instance.show()


def _add_tree_card_button(buttons: list[str], editor) -> None:
    button = editor.addButton(
        None,
        "tree_card_generator",
        _open_tree_dialog,
        tip="Tree Card Generator - paste ASCII tree, generate collapsible HTML",
        label="Tree Card",
    )
    buttons.append(button)


gui_hooks.editor_did_init_buttons.append(_add_tree_card_button)

logger.info("Tree Card Generator loaded")
