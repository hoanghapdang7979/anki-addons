"""Popup dialog for pasting ASCII tree text and copying the rendered HTML
to the clipboard.

UI code - not unit tested (needs a live Qt event loop); verified manually
in real Anki (see tasks/plan.md Task 5/6). All actual logic (parsing,
rendering) lives in tree_parser.py/tree_renderer.py, which ARE tested.
"""

from aqt.qt import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMimeData,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .tree_parser import parse_tree
from .tree_renderer import render_html


class TreeDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tree Card Generator")
        self.resize(600, 500)

        self._text_edit = QPlainTextEdit(self)
        self._text_edit.setPlaceholderText(
            "Dán text dạng cây ASCII (├──/│/└──) vào đây..."
        )

        self._status_label = QLabel("", self)

        generate_button = QPushButton("Generate && Copy", self)
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

        mime = QMimeData()
        mime.setHtml(html)
        QApplication.clipboard().setMimeData(mime)
        self._status_label.setText(
            "Đã copy HTML vào clipboard — Ctrl+V để dán vào field."
        )
