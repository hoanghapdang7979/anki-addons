# Todo: Habit Heatmap

Chi tiết (acceptance criteria, verification, files): xem [plan.md](./plan.md).

## Phase 0: Foundation & rủi ro cao nhất
- [x] Task 1: Skeleton + venv pin 25.9.4 + khối heatmap trên màn hình deck — DONE, xác nhận bằng screenshot Anki 25.9.4 thật (profile `IFE-Test`): khối hiện dưới bảng deck, ngay dưới dòng của Review Heatmap
- [x] Task 2: Vòng `pycmd` → `set_config` → refresh (1 habit cứng, tick hôm nay) — DONE, xác nhận trong Anki 25.9.4 thật: tick/bỏ tick đúng, và tick còn nguyên sau khi user đóng/mở lại Anki
- [x] Task 3: Spike đồng bộ — DONE bằng 2 collection thật + `anki.syncserver` cục bộ (không chạm tài khoản thật): config sync cả khối theo máy mới hơn, máy sync sau mất thay đổi chưa sync; xem SPEC mục 4

**Checkpoint 0:** hook/bridge/persist hoạt động + cách config sync đã rõ.

## Phase 1: Logic thuần (TDD)
- [x] Task 4: `days.py` (anki_today, lưới 53 tuần)
- [x] Task 5: `bitmap.py` (encode/decode, union, toggle_today)
- [x] Task 6: `stats.py` (streak, days done, %)
- [x] Task 7: `render.py` (khối HTML inline, chỉ ô hôm nay có onclick)
- [x] Task 8: `habits.py` (thêm/đổi tên/sắp xếp/lưu trữ/khôi phục/xoá hẳn)

**Checkpoint 1:** pytest pass 100% — ✅ 68/68.

## Phase 2: Tích hợp thật
- [x] Task 9: `store.py` + nối render thật (nhiều habit, Python validate "hôm nay") — DONE, user xác nhận trong Anki 25.9.4 thật (profile IFE-Test, sau restart): khối heatmap + Check today hoạt động
- [x] Task 10: `manage_dialog.py` (Tools → Habit Heatmap, xoá hẳn có xác nhận) — DONE, user xác nhận thêm/đổi tên/archive-restore/xoá hẳn trong Anki thật; shadow `IFE-Test` có 1 tombstone từ lần xoá hẳn

## Phase 3: Đồng bộ & chống mất chuỗi
- [x] Task 11: Shadow + gộp 3 chiều + sync nối tiếp — viết lại sau khi user báo sync lúc đúng lúc sai (nguyên nhân: union không lan được bỏ tick; Anki thay cả khối config). 131 test + e2e 15/15
- [x] Task 12: Verify sync end-to-end — DONE: e2e tự động 15/15 + user xác nhận sync hoạt động ổn trên 2 profile thật (sau bản gộp 3 chiều)

**Checkpoint 2:** toàn bộ Success Criteria trong SPEC đạt.

## Phase 4: Polish
- [x] Task 13: README + đóng gói `.ankiaddon` — README viết xong; `.ankiaddon` 13 file, bản giải nén qua đủ kịch bản mô phỏng. Cần đóng gói lại nếu Task 12 làm code đổi

## v2 — Review-Heatmap look, notes, tooltip, drag-to-reorder
- [x] V2-1 `days.year_grid`/`clamp_year` (thuần, TDD)
- [x] V2-2 `themes.py` + `stats.streak_runs`
- [x] V2-3 `notes.py`
- [x] V2-4 `merge3.merge_habits` + `habits.reorder`
- [x] V2-5 Store + shadow + reconcile cho note
- [x] V2-6 `render.py` + `assets.py`
- [x] V2-7 Nối vào Anki
- [x] V2-8 e2e sync
- [x] V2-9 README/SPEC + đóng gói + commit/push — DONE
- [ ] V2-10 Xác nhận trong Anki thật *(user restart Anki)*

