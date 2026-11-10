"""Popup dialog for pasting ASCII tree text and writing the rendered HTML
directly into the currently-focused field of the note open in the Editor.

UI code - not unit tested (needs a live Qt event loop); verified manually
in real Anki. All actual logic (parsing, rendering) lives in
tree_parser.py/tree_renderer.py, which ARE tested.

Real-world finding (see tasks/plan.md Task 5/6): Anki's paste-into-field
sanitization strips <style>/<script>/<details> and most inline style
properties (only character-level ones like "color" survive), so a
clipboard-copy-then-paste delivery mechanism cannot carry a collapsible
tree's structure/styling at all - confirmed via the raw HTML actually
stored after a real paste, not assumed. Writing directly to the note's
field and refreshing the Editor's display bypasses paste sanitization
entirely, since sanitization is a paste-time safeguard, not something
applied to already-stored field content.

Add Cards vs. existing notes need different persistence: in Add Cards
(editor.addMode) the note has no id yet (note.id == 0) - it isn't in the
collection until the user clicks "Add", so there is nothing to save here,
only the in-memory note object to mutate. For an existing note (Browse,
etc.) the change must be persisted via aqt.operations.note.update_note -
the same op Editor._save_current_note() uses internally. Either way,
editor.loadNote(focusTo=...) refreshes the on-screen field from the
already-mutated note object. See tasks/plan.md Task 5 for the full
architecture history (3 pivots) and the real Anki-25.9.4-vs-dev-venv
version mismatch that caused an earlier AttributeError.
"""

from aqt.operations.note import update_note
from aqt.qt import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .tree_parser import parse_tree
from .tree_renderer import render_html


class TreeDialog(QDialog):
    def __init__(self, editor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editor = editor
        self.setWindowTitle("Tree Card Generator")
        self.resize(600, 500)

        self._text_edit = QPlainTextEdit(self)
        self._text_edit.setPlaceholderText(
            "Dán text dạng cây ASCII (├──/│/└──) vào đây..."
        )

        self._status_label = QLabel("", self)
        self._status_label.setWordWrap(True)

        generate_button = QPushButton("Generate", self)
        generate_button.clicked.connect(self._on_generate)

        close_button = QPushButton("Đóng", self)
        close_button.clicked.connect(self.close)

        button_row = QHBoxLayout()
        button_row.addWidget(generate_button)
        button_row.addWidget(close_button)
        button_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self._text_edit)
        layout.addLayout(button_row)
        layout.addWidget(self._status_label)

    def _on_generate(self) -> None:
        text = self._text_edit.toPlainText()
        if not text.strip():
            self._status_label.setText("Chưa dán text tree nào.")
            return

        try:
            root = parse_tree(text)
            html = render_html(root)
        except Exception as exc:  # malformed input - show, don't crash the dialog
            self._status_label.setText(f"Lỗi parse: {exc}")
            return

        note = self._editor.note
        if note is None:
            self._status_label.setText(
                "Không tìm thấy note trong Editor - mở Add Cards hoặc Browse rồi thử lại."
            )
            return
        if self._editor.last_field_index is None:
            self._status_label.setText(
                "Chưa xác định được field nào - click vào field muốn điền trước khi "
                "bấm nút Tree Card, rồi thử lại."
            )
            return

        field_index = self._editor.last_field_index
        note.fields[field_index] = html

        if not self._editor.addMode:
            # In Add Cards the note has no id yet (note.id == 0) - it only
            # gets persisted once the user clicks "Add", using this same
            # in-memory note object, so there is nothing to save here.
            # Outside Add Cards (Browse, etc.) the note already exists in
            # the collection, so persist through the same op Anki's own
            # editor internals use (aqt.editor.Editor._save_current_note).
            update_note(parent=self._editor.widget, note=note).run_in_background(
                initiator=self._editor
            )
        self._editor.loadNote(focusTo=field_index)

        self._status_label.setText(
            "Đã ghi vào field — không cần Ctrl+V."
        )
