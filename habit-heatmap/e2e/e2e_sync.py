"""End-to-end sync check: real anki Collections + Anki's own local sync server +
the real habit-heatmap Store/reconcile. Each Device mimics one Anki profile.
Touches no real Anki profile or AnkiWeb account (temp dirs, localhost only).

Run from the repo root (takes ~2 minutes: operations are spaced 1.1s apart because
Anki's config mtime has 1-second resolution):

    SYNC_USER1=u:p SYNC_BASE=<empty dir> SYNC_HOST=127.0.0.1 SYNC_PORT=8791         habit-heatmap/.venv/Scripts/python -m anki.syncserver        # in another shell
    habit-heatmap/.venv/Scripts/python -I habit-heatmap/e2e/e2e_sync.py

Set FOLLOWUP=0 to see why the add-on's follow-up sync is needed (4 scenarios fail).
"""
import os
import shutil
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / ".venv" / "Lib" / "site-packages"))
sys.path.insert(0, str(HERE))
import anki.lang

anki.lang.set_lang("en")
from anki.collection import Collection

from habits import PALETTE, add_habit, archive_habit, delete_habit, rename_habit, reorder
from reconcile import reconcile
from shadow import ShadowFile
from store import Store

EP = "http://127.0.0.1:8791/"
FOLLOWUP = os.environ.get("FOLLOWUP", "1") == "1"
ROOT = Path(tempfile.mkdtemp(prefix="e2e_"))
BASE = date(2026, 11, 1)
D = lambda k: BASE + timedelta(days=k)  # noqa: E731


_n = [0]


class Device:
    def __init__(self, name):
        self.name = name
        _n[0] += 1
        folder = ROOT / f"{name}{_n[0]}"
        folder.mkdir(parents=True)
        self.col = Collection(str(folder / "c.anki2"))
        self.shadow = ShadowFile(folder / "shadow.json")
        self.store = Store(self.col, shadow=self.shadow)

    def _full(self, upload):
        auth = self.col.sync_login("u", "p", EP)
        out = self.col.sync_collection(auth, False)
        self.col.close_for_full_sync()
        self.col.full_upload_or_download(auth=auth, server_usn=out.server_media_usn, upload=upload)
        self.col.reopen(after_full_sync=True)

    def full_upload(self):
        self._full(True)
        reconcile(self.store)

    def full_download(self):
        self._full(False)
        reconcile(self.store)

    def sync(self, ok=True):
        """Normal sync, then what the add-on does on sync_did_finish (it fires even on failure)."""
        time.sleep(1.1)  # Anki's config mtime has 1-second resolution; real syncs are never this close
        if ok:
            auth = self.col.sync_login("u", "p", EP)
            out = self.col.sync_collection(auth, False)
            assert out.required == out.NO_CHANGES, f"{self.name}: unexpected full sync {out.required}"
        wrote = reconcile(self.store)
        if wrote and ok and FOLLOWUP:
            # what the add-on would do: the merged config is pending, push it right away
            time.sleep(1.1)
            auth = self.col.sync_login("u", "p", EP)
            self.col.sync_collection(auth, False)
            reconcile(self.store)
        return wrote

    def view(self):
        out = {}
        for h in self.store.habits():
            out[h.name + ("*" if h.archived else "")] = sorted(
                (date.fromordinal(o) - BASE).days for o in self.store.bitmap(h.id).ticked_ordinals()
            )
        return out

    def hid(self, name=None):
        return next(h.id for h in self.store.habits() if name is None or h.name == name)

    def tick(self, k):
        time.sleep(1.1)
        self.store.toggle_today(self.hid(), D(k))

    def note(self, day_k, text, today_k):
        time.sleep(1.1)
        self.store.set_note(self.hid(), D(day_k), text, D(today_k))

    def notes_view(self):
        return {
            (date.fromordinal(int(o)) - BASE).days: t for o, t in self.store.notes(self.hid()).items()
        }

    def order(self):
        return [h.name for h in self.store.habits()]

    def reorder(self, names):
        time.sleep(1.1)
        by_name = {h.name: h.id for h in self.store.habits()}
        self.store.save_habits(reorder(self.store.habits(), [by_name[n] for n in names]))


def fresh_pair():
    a, b = Device("A"), Device("B")
    a.store.save_habits(add_habit([], "Run", PALETTE[0], D(0).toordinal(), id_factory=lambda: "h_run"))
    a.tick(0)
    a.full_upload()
    b.full_download()
    return a, b


def three_habit_pair():
    a, b = Device("A"), Device("B")
    habits = []
    for name, hid in (("Run", "h_run"), ("Read", "h_read"), ("Walk", "h_walk")):
        habits = add_habit(habits, name, PALETTE[0], D(0).toordinal(), id_factory=lambda hid=hid: hid)
    a.store.save_habits(habits)
    a.full_upload()
    b.full_download()
    return a, b


def converge(*devices, rounds=2):
    for _ in range(rounds):
        for d in devices:
            d.sync()


results = []


def check(label, cond, detail=""):
    results.append(cond)
    print(("PASS " if cond else "FAIL ") + label + ("" if cond else f"   -> {detail}"))


# 1. both directions
a, b = fresh_pair()
check("baseline: B downloaded A's habit + tick", b.view() == {"Run": [0]}, b.view())
a.tick(1); a.sync(); b.sync()
check("1a. A ticks, A sync, B sync -> B == A", b.view() == a.view() == {"Run": [0, 1]}, (a.view(), b.view()))
b.tick(2); b.sync(); a.sync()
check("1b. B ticks, B sync, A sync -> A == B", a.view() == b.view() == {"Run": [0, 1, 2]}, (a.view(), b.view()))

# 2. un-tick propagation, both directions, and not resurrected afterwards
a.tick(1); a.sync(); b.sync()
check("2a. A un-ticks day 1 -> B loses it after sync", b.view() == {"Run": [0, 2]}, b.view())
converge(a, b)
check("2b. ...and it stays gone after more syncs (no resurrection)", a.view() == b.view() == {"Run": [0, 2]}, (a.view(), b.view()))
b.tick(2); b.sync(); a.sync(); converge(a, b)
check("2c. B un-ticks day 2 -> A loses it", a.view() == b.view() == {"Run": [0]}, (a.view(), b.view()))

# 3. both machines tick different days before syncing
a.tick(3); b.tick(4)
converge(a, b, rounds=3)
check("3. both tick offline, then sync -> both end with every tick", a.view() == b.view() == {"Run": [0, 3, 4]}, (a.view(), b.view()))

# 4. one un-ticks while the other ticks (offline on both)
a.tick(0); b.tick(5)
converge(a, b, rounds=3)
check("4. A un-ticks day 0 while B ticks day 5 -> both: 0 gone, 5 present", a.view() == b.view() == {"Run": [3, 4, 5]}, (a.view(), b.view()))

# 5. a FAILED sync must not make the add-on think things were synced
a.tick(6)
a.sync(ok=False)
a.sync(ok=False)
converge(b, a, rounds=3)
check("5. add-on ran after failed syncs, then real syncs -> B gets the tick", b.view() == a.view() == {"Run": [3, 4, 5, 6]}, (a.view(), b.view()))

# 6. brand-new device downloads
c = Device("C")
c.full_download()
check("6. new device C (Download) shows everything", c.view() == a.view(), (a.view(), c.view()))

# 7. habit-level changes propagate
b.store.save_habits(rename_habit(b.store.habits(), "h_run", "Running"))
b.sync(); a.sync(); converge(a, b)
check("7a. rename on B reaches A", list(a.view()) == ["Running"] and a.view() == b.view(), (a.view(), b.view()))
a.store.save_habits(archive_habit(a.store.habits(), "h_run"))
a.sync(); b.sync(); converge(a, b)
check("7b. archive on A reaches B (history kept)", list(b.view()) == ["Running*"] and b.view() == a.view(), (a.view(), b.view()))
a.store.save_habits(delete_habit(a.store.habits(), "h_run")); a.store.delete_data("h_run")
a.sync(); b.sync(); converge(a, b)
check("7c. Delete forever on A -> gone on B and not resurrected", a.view() == b.view() == {}, (a.view(), b.view()))

# 8. user picks "Download from AnkiWeb" while holding an un-synced tick
a, b = fresh_pair()
a.tick(7)                       # un-synced local tick
a.full_download()               # server copy replaces the local collection
check("8a. un-synced tick survives a forced Download (restored from shadow)", a.view() == {"Run": [0, 7]}, a.view())
converge(a, b)
check("8b. ...and then reaches B", b.view() == a.view() == {"Run": [0, 7]}, (a.view(), b.view()))

# 9. notes propagate like ticks
a, b = fresh_pair()
a.note(1, "felt great", 3); a.sync(); b.sync()
check("9a. note added on A reaches B", b.notes_view() == {1: "felt great"}, b.notes_view())
b.note(1, "felt great!!", 3); b.sync(); a.sync(); converge(a, b)
check("9b. note edited on B reaches A", a.notes_view() == b.notes_view() == {1: "felt great!!"}, (a.notes_view(), b.notes_view()))
a.note(1, "", 3); a.sync(); b.sync(); converge(a, b)
check("9c. note deleted on A disappears on B and stays gone", a.notes_view() == b.notes_view() == {}, (a.notes_view(), b.notes_view()))

# 10. notes on different days written on both machines before syncing
a.note(1, "A-note", 3); b.note(2, "B-note", 3)
converge(a, b, rounds=3)
check("10. notes for different days written offline on both -> both kept",
      a.notes_view() == b.notes_view() == {1: "A-note", 2: "B-note"}, (a.notes_view(), b.notes_view()))

# 11. same day edited on both machines: one wins consistently, nothing is lost silently on one side only
a.note(1, "mine", 3); b.note(1, "theirs", 3)
converge(a, b, rounds=3)
check("11. same day edited on both -> both machines end identical", a.notes_view() == b.notes_view() and set(a.notes_view()) == {1, 2},
      (a.notes_view(), b.notes_view()))

# 12. an un-synced note survives a forced Download
a, b = fresh_pair()
a.note(2, "unsynced", 3)
a.full_download()
check("12a. un-synced note survives Download (restored from shadow)", a.notes_view() == {2: "unsynced"}, a.notes_view())
converge(a, b)
check("12b. ...and then reaches B", b.notes_view() == {2: "unsynced"}, b.notes_view())

# 13. habit order (priority) propagates
a, b = three_habit_pair()
check("13-baseline. B downloaded the order", b.order() == ["Run", "Read", "Walk"], b.order())
b.reorder(["Walk", "Run", "Read"]); b.sync(); a.sync(); converge(a, b)
check("13a. reorder on B reaches A", a.order() == b.order() == ["Walk", "Run", "Read"], (a.order(), b.order()))
a.reorder(["Read", "Walk", "Run"]); a.sync(); b.sync(); converge(a, b)
check("13b. reorder on A reaches B", a.order() == b.order() == ["Read", "Walk", "Run"], (a.order(), b.order()))
a.reorder(["Run", "Read", "Walk"]); b.reorder(["Walk", "Read", "Run"])
converge(a, b, rounds=3)
check("13c. both reorder offline -> both machines end with the same order", a.order() == b.order() and sorted(a.order()) == ["Read", "Run", "Walk"],
      (a.order(), b.order()))
a.reorder(["Walk", "Run", "Read"]); a.sync(); b.sync(); converge(a, b)
check("13d. a later reorder still wins after a conflict", a.order() == b.order() == ["Walk", "Run", "Read"], (a.order(), b.order()))

print(f"\n{sum(results)}/{len(results)} passed")
for dev in (a, b, c):
    dev.col.close()
sys.exit(0 if all(results) else 1)
