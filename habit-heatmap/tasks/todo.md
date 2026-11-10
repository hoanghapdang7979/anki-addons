# Todo: Habit Heatmap

Chi tiết (acceptance criteria, verification, files): xem [plan.md](./plan.md).

## Phase 0: Foundation & rủi ro cao nhất
- [x] Task 1: Skeleton + venv pin 25.9.4 + khối heatmap trên màn hình deck — DONE, xác nhận bằng screenshot Anki 25.9.4 thật (profile `IFE-Test`): khối hiện dưới bảng deck, ngay dưới dòng của Review Heatmap
- [x] Task 2: Vòng `pycmd` → `set_config` → refresh (1 habit cứng, tick hôm nay) — DONE, xác nhận trong Anki 25.9.4 thật: tick/bỏ tick đúng, và tick còn nguyên sau khi user đóng/mở lại Anki
- [ ] Task 3: Spike đồng bộ — config có sync không, merge thế nào *(user chạy sync)*

**Checkpoint 0:** hook/bridge/persist hoạt động + cách config sync đã rõ.

## Phase 1: Logic thuần (TDD)
- [x] Task 4: `days.py` (anki_today, lưới 53 tuần)
- [x] Task 5: `bitmap.py` (encode/decode, union, toggle_today)
- [x] Task 6: `stats.py` (streak, days done, %)
- [x] Task 7: `render.py` (khối HTML inline, chỉ ô hôm nay có onclick)
- [x] Task 8: `habits.py` (thêm/đổi tên/sắp xếp/lưu trữ/khôi phục/xoá hẳn)

**Checkpoint 1:** pytest pass 100% — ✅ 68/68.

## Phase 2: Tích hợp thật
- [ ] Task 9: `store.py` + nối render thật (nhiều habit, Python validate "hôm nay") — `store.py` (có test, 78/78) + `deckview.py` xong và mô phỏng với aqt thật; **chưa nối vào `__init__.py`** (spike hiện tại còn nguyên để user chạy Task 3) — wiring thật vào `__init__.py` xong; 100 test pass; mô phỏng với hook thật của aqt 25.9.4. **Chờ user restart Anki xem trong Anki thật**
- [ ] Task 10: `manage_dialog.py` (Tools → Habit Heatmap, xoá hẳn có xác nhận) — `manage_dialog.py` xong, mô phỏng với Qt offscreen: thêm/chặn tên rỗng/đổi tên giữ id/đổi màu/lên-xuống/lưu trữ/xoá hẳn có xác nhận mặc định No; **chưa nối vào `__init__.py`, chưa xem trong Anki thật**

## Phase 3: Đồng bộ & chống mất chuỗi
- [ ] Task 11: Shadow + union + dọn mồ côi — `shadow.py` + `reconcile.py` xong (TDD, 100 test pass), mô phỏng: config bị xoá → khôi phục từ shadow qua `sync_did_finish` thật. Chưa xem trong Anki thật
- [ ] Task 12: Verify sync end-to-end *(user chạy sync)*

**Checkpoint 2:** toàn bộ Success Criteria trong SPEC đạt.

## Phase 4: Polish
- [ ] Task 13: README + đóng gói `.ankiaddon`
