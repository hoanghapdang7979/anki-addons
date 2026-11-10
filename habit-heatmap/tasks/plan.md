# Implementation Plan: Habit Heatmap

> Dựa trên [SPEC.md](../SPEC.md) (đã chốt 4 quyết định: lưu collection config, cho bỏ tick hôm
> nay, 53 tuần, lưu trữ + xoá hẳn). Cùng quy ước với các add-on khác trong repo.

## Overview

Mỗi habit = 1 khối heatmap 53 tuần trên màn hình deck, tick tay chỉ cho hôm nay, dữ liệu là bitmap
trong collection config để đi theo sync AnkiWeb, có shadow local + union-merge chống mất chuỗi.
Hai rủi ro lớn nhất chưa verify: (1) hook deck browser + `pycmd` bridge + `set_config` hoạt động
đúng ở Anki 25.9.4, và nhìn ổn cạnh Review Heatmap; (2) config có sync thật không và merge ra sao.
=> làm 2 rủi ro này **trước** parser/logic (Risk-First Slicing, đúng bài học tree-card-generator).

## Architecture Decisions

- Logic thuần (`days/bitmap/stats/render/habits`) không `import aqt`, TDD bằng pytest; chỉ
  `__init__.py`, `store.py`, `manage_dialog.py` chạm aqt, verify tay.
- **Venv pin `aqt==25.9.4 anki==25.9.4`** ngay Task 1 (`requirements.txt`) — không cài "latest".
- **Pre-verify simulation chạy từ thư mục gốc repo** (cwd trung lập), không từ trong thư mục
  add-on (bài học false-positive import).
- Khoá ngày = `date.toordinal()`; "hôm nay" tính phía Python từ `sched.day_cutoff`; JS không bao
  giờ gửi ngày.
- **Verify bằng bằng chứng cụ thể** (screenshot / dump `col.get_config`), không chỉ câu trả lời
  đúng/sai (bài học lần user chọn nhầm).
- Mọi test thủ công trên profile `IFE-Test`; Task có động chạm tài khoản AnkiWeb thật (Task 3, 12)
  do **user tự chạy sync**.

## Task List

### Phase 0: Foundation & rủi ro kỹ thuật cao nhất

- [ ] **Task 1: Skeleton + venv pin + khối heatmap tĩnh trên màn hình deck**
  - **Description:** `manifest.json`, `__init__.py`, `requirements.txt`, `tests/conftest.py`.
    Hook `deck_browser_will_render_content` nối 1 khối HTML tĩnh (lưới 53×7 ô xám + tiêu đề
    "Test habit") vào `content.stats`.
  - **Acceptance criteria:**
    - [ ] Add-on load sạch (không traceback) ở Anki 25.9.4, profile `IFE-Test`.
    - [ ] Khối hiện dưới bảng deck, cạnh Review Heatmap, không vỡ layout (screenshot).
  - **Verification:** pre-verify `importlib` từ repo root; manual: user mở Anki + screenshot.
  - **Dependencies:** None · **Files:** `manifest.json`, `__init__.py`, `requirements.txt`
  - **Scope:** S

- [ ] **Task 2: Vòng `pycmd` → `set_config` → refresh (1 habit cứng, tick hôm nay)**
  - **Description:** Nút "Hôm nay ✓" gửi `habitheatmap:toggle:test`; handler qua
    `webview_did_receive_js_message` (kiểm `context` là DeckBrowser), toggle 1 cờ trong
    `col.set_config("habitHeatmap.spike", ...)`, rồi `mw.deckBrowser.refresh()`.
  - **Acceptance criteria:**
    - [ ] Bấm → ô hôm nay đổi màu, đóng/mở Anki vẫn giữ.
    - [ ] Message lạ/không phải của add-on không bị nuốt (trả `handled` nguyên vẹn).
  - **Verification:** manual + dump config (`mw.col.get_config(...)`) làm bằng chứng.
  - **Dependencies:** Task 1 · **Files:** `__init__.py` · **Scope:** S

- [ ] **Task 3: Spike đồng bộ — config có sync không, merge thế nào** *(user chạy sync)*
  - **Description:** Dùng key `habitHeatmap.spike` của Task 2. Profile A tick → sync AnkiWeb →
    Profile B (cùng tài khoản) sync → đọc giá trị. Rồi thử tick offline ở cả hai, sync lần lượt,
    ghi lại bên nào thắng / có per-key merge không.
  - **Acceptance criteria:**
    - [ ] Biết chắc: config sync được (có/không), kiểu xung đột (ghi đè cả khối / theo key).
    - [ ] Kết quả ghi vào SPEC mục Đồng bộ (đổi [UNVERIFIED] → [VERIFIED] kèm bằng chứng).
  - **Verification:** manual, **user tự bấm sync** (tác động tài khoản thật); dump giá trị 2 bên.
  - **Dependencies:** Task 2 · **Files:** `SPEC.md` · **Scope:** S
  - **Nếu kết quả bất ngờ** (config không sync): dừng, bàn phương án khác trước Phase 1.

### Checkpoint 0
- [ ] Hook/bridge/persist hoạt động + cách config sync đã rõ. Review với user trước khi sang logic.

### Phase 1: Logic thuần (TDD)

- [ ] **Task 4: `days.py`** — `anki_today(day_cutoff) -> date`, lưới 53 tuần (cột = tuần, hàng =
  thứ), mapping ô ↔ ordinal. **AC:** ranh giới rollover (03:59 vs 04:01), DST, đổi năm, tuần đầu
  lệch thứ. **Dep:** Task 1. **Scope:** S
- [ ] **Task 5: `bitmap.py`** — encode/decode base64, `get/set/clear bit`, tự mở rộng, `union`
  (giao hoán + idempotent), `toggle_today(bits, epoch, today)`. **AC:** roundtrip; 5 năm × 10
  habit mỗi key < 1 KB; không API nào nhận ngày tuỳ ý ngoài `today`. **Dep:** Task 4. **Scope:** S
- [ ] **Task 6: `stats.py`** — current/longest streak, days done, %. **AC:** hôm nay chưa tick
  không làm đứt streak; đứt giữa chừng; ngày tương lai bị bỏ; bitmap rỗng. **Dep:** Task 5.
  **Scope:** S
- [ ] **Task 7: `render.py`** — `build_block_html(habit, bits, today) -> str`, chỉ inline style.
  **AC:** đúng 53×7 ô; ô quá khứ **không** có `onclick`, chỉ ô hôm nay có; tên habit escape;
  dòng thống kê đúng; không `<style>`/`<script>`. **Dep:** Task 4-6. **Scope:** M
- [ ] **Task 8: `habits.py`** — thao tác danh sách habit thuần: thêm (id ổn định), đổi tên/màu,
  sắp xếp, **lưu trữ/khôi phục**, **xoá hẳn**. **AC:** đổi tên giữ id; lưu trữ giữ dữ liệu;
  xoá trả về id cần dọn (config key + shadow). **Dep:** None. **Scope:** S

### Checkpoint 1
- [ ] `pytest` pass 100%, chưa cần Anki thật.

### Phase 2: Tích hợp thật

- [ ] **Task 9: `store.py` + nối render thật** — đọc/ghi `habitHeatmap.habits` và
  `habitHeatmap.d.<id>`, thay habit cứng của Task 2; toggle bằng `toggle_today` (Python tự tính
  hôm nay, re-validate mỗi click). **AC:** nhiều habit → nhiều khối; ô quá khứ không tick được kể
  cả khi gửi lệnh giả; habit lưu trữ không hiện. **Verify:** manual + dump config. **Dep:** Task
  2, 7, 8. **Scope:** M
- [ ] **Task 10: `manage_dialog.py` (Tools → Habit Heatmap)** — thêm/đổi tên/màu/lên-xuống/lưu
  trữ/khôi phục/**xoá hẳn có dialog xác nhận "không hoàn tác"**. **AC:** mọi thao tác phản ánh
  ngay trên màn hình deck; xoá hẳn dọn đúng key. **Verify:** manual. **Dep:** Task 8, 9.
  **Scope:** M

### Phase 3: Đồng bộ & chống mất chuỗi

- [ ] **Task 11: Shadow + union + dọn mồ côi** — shadow `user_files/shadow.json`; ghi cả config
  lẫn shadow mỗi lần tick/bỏ tick; `sync_did_finish` + `profile_did_open`: OR bitmap với shadow rồi
  `set_config` nếu khác; ~~dọn key `d.<id>` mồ côi~~ (bỏ: không tự xoá dữ liệu); xoá hẳn xoá cả entry shadow + ghi tombstone;
  union cả danh sách habit (theo id, trừ tombstone) để khôi phục khi config bị ghi đè.
  Phần merge là hàm thuần → TDD. **AC:** unit test union/dọn mồ côi; không hồi sinh habit đã xoá.
  **Dep:** Task 3, 5, 9. **Scope:** M
- [ ] **Task 12: Verify sync end-to-end** *(user chạy sync)* — 2 profile cùng tài khoản: tick
  ở A, sync, B thấy; tick offline ở cả hai (ngày khác nhau + cùng ngày), sync lần lượt → không mất
  tick; "Download from AnkiWeb" xong mở lại → shadow phục hồi. **Bằng chứng:** screenshot + dump.
  **Dep:** Task 11. **Scope:** S

### Checkpoint 2
- [ ] Toàn bộ Success Criteria trong SPEC đạt. Review với user.

### Phase 4: Polish

- [ ] **Task 13: README + đóng gói `.ankiaddon`** — README (cách dùng, giới hạn đã biết: không chặn
  được chỉnh đồng hồ máy, union có thể hồi sinh tick đã bỏ), đóng gói bằng `zipfile` (không có
  `zip`), chỉ gồm file add-on (không `tests/`, `.venv/`, `tasks/`, `user_files/`, `__pycache__`).
  **Dep:** Task 12. **Scope:** XS

### Checkpoint: Complete
- [ ] Success Criteria đạt, README xong. Đề xuất commit (chỉ code, không `.venv/`).

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Config không sync / merge ghi đè cả khối | **High** | Task 3 spike trước mọi logic; nếu fail dừng bàn lại. |
| 2 máy tick offline ghi đè nhau | High | Shadow + union (Task 11), verify Task 12. |
| API khác giữa bản dev và Anki thật | High | Pin `aqt/anki==25.9.4`, đọc source đúng version. |
| Config phình quá vài KB | Medium | Bitmap, test kích thước key < 1 KB (Task 5). |
| Rollover tính sai ngày | Medium | `anki_today` thuần + test biên (Task 4). |
| Xoá hẳn bị union hồi sinh | Medium | Xoá cả shadow + dọn mồ côi (Task 8/11). |
| Layout vỡ cạnh Review Heatmap | Low | Nhìn thật ở Task 1. |
| Test lỡ đụng profile/tài khoản thật | Medium | Chỉ `IFE-Test`; sync do user chủ động. |

## Open Questions

- Bảng màu cố định hay hex tự do; có nút lên/xuống (mặc định: bảng màu cố định + có lên/xuống) —
  quyết trong Task 10, không chặn các task trước.

## Ghi chú thực thi (autopilot)

- Task 4–8 xong theo TDD (RED → GREEN, 68 test). Task 7 đã nhìn thật qua trình duyệt (lưới 53
  cột co theo chiều rộng, màu riêng từng habit).
- Task 1–2: code spike xong; **pre-verify bằng `aqt` 25.9.4 thật** (đăng ký hook thật, mô phỏng
  vòng click → `set_config` → `refresh`, message lạ/sai context/id lạ đều không bị nuốt). Kỹ thuật
  mô phỏng: chạy từ repo root với `python -I`; import `aqt.deckbrowser` ngoài Anki cần
  `anki.lang.set_lang("en")` trước, và venv cần `pywin32` (đã thêm vào `requirements.txt`).
- Chưa tick Task 1–3: cần user cài Junction vào `addons21` (autopilot không tự làm) và xem/bấm
  trong Anki thật; Task 3 cần user tự sync AnkiWeb.

## Ghi chú: sync sai lệch do user phát hiện (Task 12, vòng 1)

- User báo "A đổi → sync → B sync → B phải giống A, và ngược lại, nhưng lúc được lúc không".
  Nguyên nhân gốc (đo, không đoán): (1) union chỉ thêm nên **bỏ tick không lan** và bị hồi sinh;
  (2) Anki thay **cả khối config** theo máy mới hơn nên máy sync sau mất thay đổi chưa sync, và một
  sync xen giữa (kể cả không đổi gì) làm bản gộp của ta thua lần nữa; (3) `sync_did_finish` chạy cả khi
  sync lỗi nên không thể suy ra "đã sync".
- Cách đo: `anki.syncserver` (có sẵn trong gói `anki`) + 2 `Collection` headless trong thư mục tạm —
  không chạm Anki hay AnkiWeb thật. Script giữ lại ở `e2e/e2e_sync.py` làm test hồi quy.
- Bài học: kiểm chứng sync bằng **kịch bản đo được** thay vì chỉ suy luận từ docstring; ban đầu tôi
  chỉ dựa vào câu "config được gửi mỗi lần sync" và thiết kế quá lạc quan.


---

# v2 — Kế hoạch: giao diện kiểu Review Heatmap, note theo ngày, tooltip, kéo thả thứ tự

> Dựa trên mục "v2" của [SPEC.md](../SPEC.md). v1 (Task 1–13) đã xong. Thứ tự: logic thuần (TDD) →
> lưu trữ + sync → render → nối vào Anki → xác nhận trong Anki thật.

**Rủi ro lớn nhất:** `<style>`/`<script>` có chạy ở màn hình deck không (CSP chỉ chặn trang Editor
theo source, chưa thử thật). Cần user restart Anki để xem → tôi dựng sẵn **phương án dự phòng**
(`title` thuần, script gỡ `title` chỉ khi khởi tạo xong) nên phần còn lại không bị chặn.

## Task list

- [x] **V2-1 `days.year_grid`/`clamp_year`** (thuần, TDD) — lưới năm lịch (tuần bắt đầu thứ Hai,
  53/54 cột, ô ngoài năm = None). Bỏ `build_grid` cũ. **AC:** năm nhuận; 1/1 rơi vào cả 7 thứ; ô
  ngoài năm None; `clamp_year` ở biên.
- [x] **V2-2 `themes.py` + `stats.streak_runs`** — 5 theme × 5 mức, `streak_level`
  (1/2–3/4–6/7–13/≥14), `resolve_theme` (hex v1 → theme), độ dài đoạn tick tại mỗi ngày.
- [x] **V2-3 `notes.py`** — `clean_note` (cắt 500, `\r\n`, ký tự điều khiển), `merge_notes` (3 chiều
  theo ngày), `note_day_ok(day, created, today)`.
- [x] **V2-4 `merge3.merge_habits` + `habits.reorder`** — gộp thứ tự (local nếu thứ tự tương đối của
  remote không đổi so với base), `reorder(habits, ids)`, số ưu tiên.
- [x] **V2-5 Store + shadow + reconcile cho note** — `Store.notes/set_note` (kiểm ngày, habit còn
  dùng, 200 000 ký tự), `delete_data` xoá cả note, shadow có `notes/base_notes`, reconcile gộp note.
- [x] **V2-6 `render.py` + `assets.py`** — `day_status`, thanh ‹ ○ ›, khối habit mới (lưới năm, màu
  theo streak, chấm note, ô tương lai xám đậm, nút Check/Note, nhãn năm, thống kê tô màu), dữ liệu
  `data-*`, `title` dự phòng, đúng 1 `<style>` + 1 `<script>` (tooltip bằng `textContent`).
- [x] **V2-7 Nối vào Anki** — `deckview` (nav, note + hộp nhập, năm đang xem, assets một lần),
  `manage_dialog` (chọn theme, kéo thả đổi thứ tự, số ưu tiên). Mô phỏng với `aqt` thật.
- [x] **V2-8 e2e sync** — thêm kịch bản đổi thứ tự lan sang máy kia, note thêm/sửa/xoá lan hai chiều,
  hai máy sửa note hai ngày khác nhau / cùng ngày, note qua Download, note còn khi untick.
- [x] **V2-9 README/SPEC + đóng gói + commit/push.**
- [ ] **V2-10 Xác nhận trong Anki thật** *(user restart Anki)* — script/tooltip chạy, chế độ tối, cửa sổ
  hẹp, điều hướng năm, bấm ô quá khứ thêm note, kéo thả.

**Checkpoint:** sau V2-5 (`pytest` pass 100%), sau V2-8 (`e2e` pass), sau V2-10 (user xác nhận).

