# Implementation Plan: Auto Date Field

> Đặt trong `auto-date-field/tasks/plan.md` — cùng quy ước với
> [inline-field-editor/tasks/plan.md](../../inline-field-editor/tasks/plan.md): mỗi add-on tự
> quản lý plan/task riêng trong folder của nó.

## Overview

Add-on nhỏ, dựa trên [SPEC.md](../SPEC.md): khi note mới được tạo qua Add Cards, tự điền ngày
hôm nay (`yyyy-mm-dd`) vào field đọc từ `config.json` (mặc định `"Date"`) — chỉ khi field đang
trống. Không cần JS/webview (khác `inline-field-editor`), thuần Python + 1 hook.

## Architecture Decisions

- **Tách logic thuần (`date_fill.py`) khỏi wiring (`__init__.py`)** — giống pattern đã dùng ở
  `inline-field-editor`: `date_fill.py` không `import aqt`/`anki`, nhận `note` như dict-like
  (duck typing) để test bằng `dict` thường, không cần mock `anki.notes.Note`.
- **Hook `aqt.gui_hooks.add_cards_did_add_note(note)`** — đã verify tồn tại trong lúc viết spec
  (`_aqt/hooks.py`, callback nhận thẳng `note: anki.notes.Note`). Hook này fire **sau khi** note
  đã được lưu vào DB, nên phải tự gọi `mw.col.update_note(note)` nếu có thay đổi field — không
  tự động lưu.
- **Venv riêng cho add-on này** (không dùng chung với `inline-field-editor/.venv`) — giữ mỗi
  add-on tự chứa được, tránh version-mismatch giữa 2 add-on về sau (đã ghi trong SPEC.md).
- **Không cần task "verify API"** riêng như `inline-field-editor` (Task 2 ở plan đó) — hook
  `add_cards_did_add_note` đã verify xong trong lúc `/spec`, ghi lại trong SPEC.md thay vì tách
  task riêng (add-on này chỉ dùng 1 hook, rủi ro API thấp hơn nhiều so với field-filter + webview
  bridge của `inline-field-editor`).

## Task List

### Phase 0: Foundation

- [x] **Task 1: Venv + add-on skeleton load sạch trong Anki thật** — DONE. Pre-verify qua
  `importlib.import_module` giả lập cơ chế Anki load add-on pass sạch; user xác nhận trong
  Tools → Add-ons thấy "Auto Date Field", không lỗi.
  - **Description:** Tạo venv riêng (`auto-date-field/.venv`, cài `pytest`; cài thêm `aqt` để có
    thể tự pre-verify bằng cách giả lập `importlib.import_module()` như đã làm cho
    `inline-field-editor`, không bắt buộc dùng để chạy Anki thật). Tạo `manifest.json` +
    `__init__.py` tối thiểu (chỉ log "Auto Date Field loaded"), tạo Junction vào `addons21/`.
  - **Acceptance criteria:**
    - [ ] Add-on hiện trong Tools → Add-ons, enabled, không traceback.
  - **Verification:**
    - [ ] Tự giả lập `importlib.import_module('auto-date-field')` qua `addons21/` trong venv
      trước (như đã làm ở inline-field-editor Task 5) để bắt lỗi sớm.
    - [ ] Manual: user restart Anki, xác nhận trong Tools → Add-ons.
  - **Dependencies:** None
  - **Files likely touched:** `auto-date-field/manifest.json`, `auto-date-field/__init__.py`
  - **Estimated scope:** XS

### Checkpoint: Foundation
- [ ] Skeleton load sạch, xác nhận bởi user.

### Phase 1: Core vertical slice — date logic + wiring

- [ ] **Task 2: `date_fill.py` — logic thuần (TDD)**
  - **Description:** Viết `today_iso(today: date | None) -> str` và
    `apply_date_if_empty(note, field_name, date_str) -> bool` theo đúng snippet trong
    SPEC.md → Code Style.
  - **Acceptance criteria:**
    - [ ] `today_iso()` trả đúng format `yyyy-mm-dd` với `today` truyền vào tường minh.
    - [ ] `apply_date_if_empty()`: field trống → set + return True; field có nội dung (kể cả
      chỉ có khoảng trắng) → không đổi + return False; field không tồn tại trong note →
      không đổi + return False.
  - **Verification:**
    - [ ] `pytest auto-date-field/tests` (chạy đúng cách — xem SPEC.md → Commands) pass 100%.
  - **Dependencies:** None (chạy song song Task 1 được — logic thuần không cần skeleton).
  - **Files likely touched:** `auto-date-field/date_fill.py`,
    `auto-date-field/tests/conftest.py`, `auto-date-field/tests/test_date_fill.py`
  - **Estimated scope:** S

- [ ] **Task 3: `config.json` + wiring trong `__init__.py`**
  - **Description:** Tạo `config.json` (`{"field_name": "Date"}`) + `config.md` mô tả field
    này. Trong `__init__.py`: đọc config qua `mw.addonManager.getConfig(__name__)`, đăng ký
    `gui_hooks.add_cards_did_add_note`, gọi `date_fill.apply_date_if_empty`, nếu thay đổi thì
    `mw.col.update_note(note)`.
  - **Acceptance criteria:**
    - [ ] Thêm note mới có field `"Date"` trống → sau Add, field = ngày hôm nay.
    - [ ] Note có field `"Date"` đã nhập sẵn nội dung → giữ nguyên sau Add.
    - [ ] Note type không có field `"Date"` → Add bình thường, không lỗi.
  - **Verification:**
    - [ ] Manual trong Anki thật (bắt buộc — đây là vertical slice cốt lõi), test đủ cả 3 case
      trên với profile test (không dùng profile thật).
  - **Dependencies:** Task 1, Task 2
  - **Files likely touched:** `auto-date-field/__init__.py`, `auto-date-field/config.json`,
    `auto-date-field/config.md`
  - **Estimated scope:** S

### Checkpoint: Core vertical slice
- [ ] Cả 3 case ở Task 3 verify OK trong Anki thật → đạt toàn bộ Success Criteria trong SPEC.md.
- [ ] `pytest auto-date-field/tests` pass 100%.
- [ ] Review với user trước khi sang Phase 2 (Phase 2 chỉ là polish, có thể dừng ở đây nếu user
  đã thấy đủ dùng).

### Phase 2: Polish

- [ ] **Task 4: README cho add-on + đóng gói thử `.ankiaddon`**
  - **Description:** Viết `auto-date-field/README.md` ngắn (cách dùng, cách đổi field name qua
    Config). Chạy lệnh zip đóng gói, cài thử `.ankiaddon` vào profile test.
  - **Acceptance criteria:**
    - [ ] README tồn tại, đúng nội dung thực tế.
    - [ ] File `.ankiaddon` cài lại được, hoạt động đúng.
  - **Verification:**
    - [ ] Manual: cài `.ankiaddon`, test lại flow cơ bản (add note, field tự điền).
  - **Dependencies:** Task 3
  - **Files likely touched:** `auto-date-field/README.md`
  - **Estimated scope:** XS

### Checkpoint: Complete
- [ ] Toàn bộ Success Criteria trong SPEC.md đạt.
- [ ] README xong, `.ankiaddon` cài thử OK.
- [ ] Đề xuất commit message cho user xác nhận — không tự `git commit`/`push`.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Note type dùng field name khác `"Date"` mà user không biết cần đổi config | Low | Open Question #1 trong SPEC.md đã hỏi user xác nhận tên field mặc định trước khi build. |
| Add-on khác đã cài (Review Heatmap, AnkiConnect, Edit Field During Review gốc `1020366288`) vô tình đụng field `"Date"` hoặc hook `add_cards_did_add_note` | Low | Không phát hiện xung đột lúc viết spec (Open Question #2). Nếu Task 3 manual verify thấy hành vi lạ, dừng lại kiểm tra thay vì đoán. |
| Test thủ công lỡ đụng vào profile Anki thật (`User 1`) | Medium | Dùng lại profile test `IFE-Test` (đã có sẵn từ add-on trước) hoặc tạo profile test riêng — không test trên `User 1`, đúng hard-stop trong `autopilot.md`. |

## Open Questions

- Không phát sinh thêm ở bước planning — 2 Open Question trong SPEC.md (tên field mặc định, khả
  năng xung đột add-on khác) sẽ được xác nhận/quan sát trong lúc thực hiện Task 3.
