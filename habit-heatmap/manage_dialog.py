"""Tools -> Habit Heatmap: add, rename, pick a colour theme, reorder by drag and
drop (the order is the priority), archive/restore and permanently delete habits.
UI only; every change goes through the pure operations in habits.py and is
saved via Store.
"""

import logging

import aqt
from aqt.qt import (
    QAbstractItemView,
    QAction,
    QBrush,
    QColor,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    Qt,
    QTimer,
    QVBoxLayout,
)
from aqt.utils import tooltip

from .context import make_store
from .days import anki_today
from .habits import (
    PALETTE,
    Habit,
    add_habit,
    archive_habit,
    delete_habit,
    move_habit,
    priority_numbers,
    recolor_habit,
    rename_habit,
    reorder,
    restore_habit,
)
from .themes import THEME_NAMES, resolve_theme, shade

logger = logging.getLogger(__name__)

_dialog: "ManageDialog | None" = None
_ROLE_ID = 256  # Qt.ItemDataRole.UserRole


class ManageDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Habit Heatmap - manage habits")
        self.resize(440, 420)
        self._store = make_store()
        self._list = QListWidget(self)
        self._list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._list.model().rowsMoved.connect(self._on_rows_moved)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Drag rows to change priority (top = highest).", self))
        layout.addWidget(self._list)
        for row in (
            [("Add", self._add), ("Rename", self._rename), ("Color theme", self._recolor)],
            [("Move up", lambda: self._move(-1)), ("Move down", lambda: self._move(1))],
            [("Archive / Restore", self._toggle_archive), ("Delete forever", self._delete)],
        ):
            box = QHBoxLayout()
            for label, slot in row:
                button = QPushButton(label, self)
                button.clicked.connect(slot)
                box.addWidget(button)
            layout.addLayout(box)
        self._reload()

    def _habits(self) -> list[Habit]:
        return self._store.habits()

    def _selected(self) -> Habit | None:
        item = self._list.currentItem()
        if item is None:
            return None
        habit_id = item.data(_ROLE_ID)
        return next((h for h in self._habits() if h.id == habit_id), None)

    def _reload(self, keep_id: str | None = None) -> None:
        self._list.clear()
        try:
            habits = self._habits()
        except ValueError:
            logger.exception("habit list is unreadable")
            tooltip("Habit list is unreadable - left untouched.")
            return
        numbers = priority_numbers(habits)
        for i, h in enumerate(habits):
            if h.archived:
                self._list.addItem(f"{h.name}  [archived]")
                self._list.item(i).setForeground(QBrush(QColor(128, 128, 128)))
            else:
                self._list.addItem(f"{numbers[h.id]}. {h.name}")
            self._list.item(i).setData(_ROLE_ID, h.id)
            if h.id == keep_id:
                self._list.setCurrentRow(i)

    def _commit(self, habits: list[Habit], keep_id: str | None = None) -> None:
        self._store.save_habits(habits)
        self._reload(keep_id)
        aqt.mw.deckBrowser.refresh()

    def _on_rows_moved(self, *_args) -> None:
        # Qt is still inside the drop; rebuild the list once it has finished.
        QTimer.singleShot(0, self._apply_list_order)

    def _apply_list_order(self) -> None:
        """Persist the order the user just dragged the rows into."""
        selected = self._selected()
        ids = [self._list.item(i).data(_ROLE_ID) for i in range(self._list.count())]
        self._commit(reorder(self._habits(), ids), selected.id if selected else None)

    def _add(self) -> None:
        name, ok = QInputDialog.getText(self, "Add habit", "Name:")
        if not ok:
            return
        habits = self._habits()
        today = anki_today(aqt.mw.col.sched.day_cutoff).toordinal()
        try:
            updated = add_habit(habits, name, PALETTE[len(habits) % len(PALETTE)], today)
        except ValueError:
            tooltip("Habit name must not be blank.")
            return
        self._commit(updated, updated[-1].id)

    def _rename(self) -> None:
        habit = self._selected()
        if habit is None:
            return
        name, ok = QInputDialog.getText(self, "Rename habit", "Name:", text=habit.name)
        if not ok:
            return
        try:
            self._commit(rename_habit(self._habits(), habit.id, name), habit.id)
        except ValueError:
            tooltip("Habit name must not be blank.")

    def _recolor(self) -> None:
        habit = self._selected()
        if habit is None:
            return
        theme = self._pick_theme(resolve_theme(habit.color))
        if theme is not None:
            self._commit(recolor_habit(self._habits(), habit.id, theme), habit.id)

    def _pick_theme(self, current: str) -> str | None:
        """Modal list of the themes, each row painted in its own colour. None if cancelled."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Color theme")
        themes = QListWidget(dialog)
        for i, name in enumerate(THEME_NAMES):
            themes.addItem(name)
            background = QColor(shade(name, 3))
            lightness = 0.299 * background.red() + 0.587 * background.green() + 0.114 * background.blue()
            item = themes.item(i)
            item.setBackground(QBrush(background))
            item.setForeground(QBrush(QColor("black" if lightness > 150 else "white")))
            if name == current:
                themes.setCurrentRow(i)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, parent=dialog
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        themes.itemDoubleClicked.connect(lambda *_: dialog.accept())
        layout = QVBoxLayout(dialog)
        layout.addWidget(themes)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted or themes.currentItem() is None:
            return None
        return themes.currentItem().text()

    def _move(self, delta: int) -> None:
        habit = self._selected()
        if habit is not None:
            self._commit(move_habit(self._habits(), habit.id, delta), habit.id)

    def _toggle_archive(self) -> None:
        habit = self._selected()
        if habit is None:
            return
        op = restore_habit if habit.archived else archive_habit
        self._commit(op(self._habits(), habit.id), habit.id)

    def _delete(self) -> None:
        habit = self._selected()
        if habit is None:
            return
        yes, no = QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No
        answer = QMessageBox.question(
            self,
            "Delete forever",
            f"Permanently delete '{habit.name}' and ALL of its history and notes?\n\n"
            "This cannot be undone. (Use Archive to hide it but keep everything.)",
            yes | no,
            no,
        )
        if answer != yes:
            return
        # Save the list first: if removing the data then fails, we are left with
        # harmless orphan data rather than a habit whose history is gone.
        self._commit(delete_habit(self._habits(), habit.id))
        self._store.delete_data(habit.id)


def _open_dialog() -> None:
    global _dialog  # keep a reference so Qt does not garbage-collect the dialog
    _dialog = ManageDialog(aqt.mw)
    _dialog.show()


def register() -> None:
    action = QAction("Habit Heatmap...", aqt.mw)
    action.triggered.connect(_open_dialog)
    aqt.mw.form.menuTools.addAction(action)
