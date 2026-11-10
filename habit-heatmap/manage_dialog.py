"""Tools -> Habit Heatmap: add, rename, recolor, reorder, archive/restore and
permanently delete habits. UI only; every change goes through the pure
operations in habits.py and is saved via Store.
"""

import logging

import aqt
from aqt.qt import (
    QAction,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QMessageBox,
    QPushButton,
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
    recolor_habit,
    rename_habit,
    restore_habit,
)

logger = logging.getLogger(__name__)

_dialog: "ManageDialog | None" = None


class ManageDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Habit Heatmap - manage habits")
        self.resize(420, 360)
        self._store = make_store()
        self._list = QListWidget(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self._list)
        for row in (
            [("Add", self._add), ("Rename", self._rename), ("Color", self._recolor)],
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
        habit_id = item.data(256)  # Qt.ItemDataRole.UserRole
        return next((h for h in self._habits() if h.id == habit_id), None)

    def _reload(self, keep_id: str | None = None) -> None:
        self._list.clear()
        try:
            habits = self._habits()
        except ValueError:
            logger.exception("habit list is unreadable")
            tooltip("Habit list is unreadable - left untouched.")
            return
        for i, h in enumerate(habits):
            self._list.addItem(f"{h.name}  [archived]" if h.archived else h.name)
            self._list.item(i).setData(256, h.id)
            if h.id == keep_id:
                self._list.setCurrentRow(i)

    def _commit(self, habits: list[Habit], keep_id: str | None = None) -> None:
        self._store.save_habits(habits)
        self._reload(keep_id)
        aqt.mw.deckBrowser.refresh()

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
        current = PALETTE.index(habit.color) if habit.color in PALETTE else 0
        color, ok = QInputDialog.getItem(self, "Habit color", "Color:", PALETTE, current, False)
        if ok:
            self._commit(recolor_habit(self._habits(), habit.id, color), habit.id)

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
            f"Permanently delete '{habit.name}' and ALL of its history?\n\n"
            "This cannot be undone. (Use Archive to hide it but keep the history.)",
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
