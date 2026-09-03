# Implementation Plan: Habit Checklist

> Đặt trong `habit-checklist/tasks/plan.md` — cùng quy ước với
> [auto-date-field/tasks/plan.md](../../auto-date-field/tasks/plan.md).

## Overview

Add-on dựa trên [SPEC.md](../SPEC.md): khi note Diary mới được tạo, tự điền danh sách habit
(đọc từ `config.json`) vào field chỉ định — mỗi habit 1 dòng `[ ] Tên habit`, chỉ khi field
đang trống. Kiến trúc gần như giống hệt `auto-date-field` (cùng hook, cùng nguyên tắc
never-overwrite), khác nội dung điền.

## Architecture Decisions

- **Tái dùng đúng pattern của `auto-date-field`** (hook `add_cards_did_add_note`, tách logic
  thuần khỏi wiring, import `anki.collection` trước để tránh circular import) — không tái dùng
  *code* (không import chéo giữa 2 add-on, theo CLAUDE.md), chỉ tái dùng *kiến trúc/pattern* đã
  chứng minh hoạt động đúng.
- **Không cần task "verify API" riêng** — hook đã verify ở `auto-date-field`, cùng 1 hook dùng
  lại ở đây, rủi ro API thấp.
- **Rủi ro lớn nhất của add-on này không phải kỹ thuật mà là an toàn dữ liệu**: never
  re-render field đã có nội dung (đã ghi rõ trong SPEC.md Boundaries) — vì field này chứa tick +
  ghi chú tay của user, mất là mất thật (khác `auto-date-field` chỉ mất 1 ngày tháng dễ gõ lại).
  Task 2 phải có test riêng khẳng định rõ hành vi này, không chỉ ngầm định qua test "field có
  nội dung → không đổi" chung chung.

## Task List

### Phase 0: Foundation

- [x] **Task 1: Venv + add-on skeleton load sạch trong Anki thật** — DONE. Pre-verify qua
  `importlib.import_module` giả lập cơ chế Anki load add-on pass sạch.
  - **Description:** Venv riêng (`habit-checklist/.venv`, cài `pytest` + `aqt` để pre-verify).
    `manifest.json` + `__init__.py` tối thiểu (log "Habit Checklist loaded"), Junction vào
    `addons21/`.
  - **Acceptance criteria:**
    - [ ] Add-on hiện trong Tools → Add-ons, enabled, không traceback.
  - **Verification:**
    - [ ] Tự giả lập `importlib.import_module('habit-checklist')` qua `addons21/` trước.
    - [ ] Manual: user restart Anki, xác nhận trong Tools → Add-ons.
  - **Dependencies:** None
  - **Files likely touched:** `habit-checklist/manifest.json`, `habit-checklist/__init__.py`
  - **Estimated scope:** XS

### Checkpoint: Foundation
- [ ] Skeleton load sạch, xác nhận bởi user.

### Phase 1: Core vertical slice — checklist logic + wiring

- [x] **Task 2: `checklist.py` — logic thuần (TDD)** — DONE, 7/7 test pass (bao gồm test
  never-overwrite quan trọng nhất).
  - **Description:** Viết `build_habit_checklist(habits: list[str]) -> str` và
    `apply_checklist_if_empty(note, field_name, checklist_text) -> bool` theo đúng snippet
    trong SPEC.md → Code Style.
  - **Acceptance criteria:**
    - [ ] `build_habit_checklist([])` → `""`; 1 habit → `"[ ] X"`; nhiều habit → nối bằng
      `<br>`, đúng thứ tự.
    - [ ] `apply_checklist_if_empty()`: field trống/chỉ khoảng trắng → set + True; field có
      nội dung thật (kể cả nội dung trông giống checklist cũ, vd đã có `[x] Exercise`) →
      **không đổi** + False — test riêng case này để khẳng định rõ never-overwrite, không chỉ
      ngầm định qua "có nội dung nói chung"; field không tồn tại → không đổi + False.
  - **Verification:**
    - [ ] `pytest habit-checklist/tests` (chạy đúng cách — xem SPEC.md → Commands) pass 100%.
  - **Dependencies:** None (song song Task 1 được).
  - **Files likely touched:** `habit-checklist/checklist.py`,
    `habit-checklist/tests/conftest.py`, `habit-checklist/tests/test_checklist.py`
  - **Estimated scope:** S

- [ ] **Task 3: `config.json` + wiring trong `__init__.py`**
  - **Description:** Tạo `config.json` (`{"field_name": "Habits", "habits": []}`) + `config.md`.
    Trong `__init__.py`: đọc config, đăng ký `gui_hooks.add_cards_did_add_note`, gọi
    `checklist.build_habit_checklist` + `apply_checklist_if_empty`, nếu thay đổi thì
    `mw.col.update_note(note)`.
  - **Acceptance criteria:**
    - [ ] Note Diary mới, field `"Habits"` trống → sau Add, field đúng checklist theo config.
    - [ ] Note Diary mới, field `"Habits"` đã có nội dung → giữ nguyên sau Add.
    - [ ] Note type khác không có field `"Habits"` → Add bình thường, không lỗi.
    - [ ] Tự tay sửa `[ ]` → `[x]` + gõ note ngay trong Editor, lưu lại → mở lại note vẫn giữ
      đúng nội dung đã sửa (add-on không đụng lại field này sau khi note đã tồn tại).
  - **Verification:**
    - [ ] Manual trong Anki thật (bắt buộc — vertical slice cốt lõi), test đủ cả 4 case trên
      với profile test (không dùng profile thật), cần cấu hình `habits` trong Config có ít
      nhất 2-3 tên habit để test thực tế.
  - **Dependencies:** Task 1, Task 2
  - **Files likely touched:** `habit-checklist/__init__.py`, `habit-checklist/config.json`,
    `habit-checklist/config.md`
  - **Estimated scope:** S

### Checkpoint: Core vertical slice
- [ ] Cả 4 case ở Task 3 verify OK trong Anki thật → đạt toàn bộ Success Criteria trong SPEC.md.
- [ ] `pytest habit-checklist/tests` pass 100%.
- [ ] Review với user trước khi sang Phase 2.

### Phase 2: Polish

- [ ] **Task 4: README cho add-on + đóng gói thử `.ankiaddon`**
  - **Description:** Viết `habit-checklist/README.md` ngắn (cách dùng, cách cấu hình
    `field_name`/`habits` qua Config, cách tick/ghi chú). Chạy lệnh zip đóng gói, cài thử
    `.ankiaddon` vào profile test.
  - **Acceptance criteria:**
    - [ ] README tồn tại, đúng nội dung thực tế.
    - [ ] File `.ankiaddon` cài lại được, hoạt động đúng.
  - **Verification:**
    - [ ] Manual: cài `.ankiaddon`, test lại flow cơ bản (add note, checklist tự điền).
  - **Dependencies:** Task 3
  - **Files likely touched:** `habit-checklist/README.md`
  - **Estimated scope:** XS

### Checkpoint: Complete
- [ ] Toàn bộ Success Criteria trong SPEC.md đạt.
- [ ] README xong, `.ankiaddon` cài thử OK.
- [ ] Đề xuất commit message cho user xác nhận — không tự `git commit`/`push`.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Field đã có nội dung (tick + ghi chú tay) bị vô tình ghi đè do bug logic "is empty" | **High** (mất dữ liệu user đã nhập tay, không phục hồi được) | `apply_checklist_if_empty` dùng đúng check `.strip()` đã verify ở `auto-date-field`; Task 2 có test riêng cho case "nội dung trông giống checklist cũ" để không lẫn với "trống". Boundaries trong SPEC.md ghi rõ never re-render. |
| User quên điền `habits` trong Config (để `[]` rỗng) rồi mới tạo note | Low | `build_habit_checklist([])` trả `""` — field vẫn coi là trống sau `.strip()`, không có gì bị "khoá": note đó chỉ đơn giản không có checklist nào (không mất dữ liệu, không chặn note sau). Nhắc trong README (Task 4): điền `habits` qua Config **trước khi** tạo note đầu tiên để không bị bỏ lỡ. |
| Test thủ công lỡ đụng profile Anki thật (`User 1`) | Medium | Dùng profile test `IFE-Test` — không test trên `User 1`. |

## Open Questions

- Không phát sinh thêm ở bước planning — 3 Open Question trong SPEC.md (tên field, danh sách
  habit mặc định, khả năng trùng field name với mục đích khác) sẽ được xác nhận/quan sát trong
  lúc thực hiện Task 3.
