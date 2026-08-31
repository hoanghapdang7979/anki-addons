# Implementation Plan: Inline Field Editor

> Đặt trong `inline-field-editor/tasks/plan.md` (không phải root repo) — cùng lý do với
> [SPEC.md](../SPEC.md): repo chứa nhiều add-on, mỗi add-on tự quản lý plan/task riêng.

## Overview

Add-on cho phép sửa field ngay trong lúc review, dựa trên [SPEC.md](../SPEC.md). Cơ chế cốt lõi:
Python đăng ký 1 **field filter** (hook xử lý cú pháp `{{edit:FieldName}}` trong template lúc
Anki render card) để bọc field đó thành 1 `<span contenteditable>`; JS trong reviewer webview
gắn sự kiện `blur` lên vùng đó, gửi nội dung mới về Python qua bridge (`pycmd`); Python nhận và
ghi lại vào note thật.

## Architecture Decisions

- **Field filter render ở Python, không phải JS parse `{{edit:Field}}`.** Anki xử lý cú pháp
  `{{...}}` ở tầng template *trước khi* xuất HTML — lúc JS chạy trong webview, `{{edit:Field}}`
  đã biến mất, chỉ còn HTML cuối. Nên phần "biến field thành editable" phải làm ở Python (field
  filter), JS chỉ có nhiệm vụ gắn listener lên kết quả đã render (`[data-ife-field]`). Bản mô tả
  sơ bộ trong SPEC.md ("JS bắt DOM {{edit:Field}} render ra") không chính xác về cơ chế — sửa lại
  đúng ở plan này.
- **Tạo riêng 1 Anki profile để test** (không dùng profile `User 1` thật đang có dữ liệu học
  thật) — máy hiện có 1 profile thật với 2 add-on đã cài (`Review Heatmap` + 1 add-on khác). Mọi
  bước "manual verify trong Anki thật" trong plan này đều chạy trên profile test riêng, đúng
  hard-stop "không đụng dữ liệu Anki thật của user" đã có trong `.claude/commands/autopilot.md`.
- **Namespace prefix `ife:` cho mọi bridge message** (`pycmd`) — máy đã có add-on khác cài, tránh
  đụng độ message giữa các add-on.
- **Không cài `anki`/`aqt` qua `pip install` vào máy thật** để chạy — chỉ cài vào 1 venv riêng
  (`.venv/`, đã có trong `.gitignore`) dùng để *đọc source* xác nhận API, không dùng venv đó để
  chạy Anki thật (Anki thật chạy qua bản `anki-release` launcher đã cài sẵn).

## Task List

### Phase 0: Foundation & Verification

- [ ] **Task 1: Tạo Anki profile test riêng**
  - **Description:** Tạo 1 profile Anki mới (vd tên `IFE-Test`) chỉ chứa 1-2 note giả (note type
    Basic, field Front/Back) để dùng cho mọi bước test thủ công sau này — không đụng profile
    `User 1` thật.
  - **Acceptance criteria:**
    - [ ] Profile `IFE-Test` tồn tại, tách biệt hoàn toàn với `User 1` (khác thư mục dữ liệu).
    - [ ] Có ít nhất 1 note type test với field editable dự kiến dùng cho add-on.
  - **Verification:**
    - [ ] Manual: mở Anki → chọn profile → xác nhận đang ở `IFE-Test`, không thấy deck thật của
      `User 1`.
  - **Dependencies:** None
  - **Files likely touched:** none (thao tác trong Anki UI, ngoài repo)
  - **Estimated scope:** XS

- [x] **Task 2: Verify Anki API thật (không đoán từ trí nhớ)** — DONE, xem
  [docs/api-notes.md](../docs/api-notes.md). Kết luận: cả 3 API đều khả dụng đúng như giả định
  trong SPEC.md ở bản `aqt`/`anki` 26.8.1, không cần đổi kiến trúc.
  - **Description:** Cài `aqt` (kéo theo `anki`) vào 1 venv riêng của repo, đọc source đã cài để
    trả lời dứt điểm 3 Open Question trong SPEC.md: (a) hàm cập nhật note hiện hành trong
    `anki.collection.Collection`, (b) cơ chế đăng ký field filter tùy biến cho cú pháp
    `{{edit:Field}}` trong template rendering, (c) hook nhận message từ webview JS gửi lên Python
    (`aqt.gui_hooks`) hiện hành.
  - **Acceptance criteria:**
    - [ ] Cả 3 mục (a)/(b)/(c) có câu trả lời kèm trích dẫn `file:line` cụ thể trong package đã
      cài — không phải suy đoán.
    - [ ] Nếu field filter kiểu cũ không còn hoạt động ở version đã cài, ghi rõ phương án thay
      thế tìm được (xem "Risks").
  - **Verification:**
    - [ ] `pip show aqt` trong venv ra đúng version đã dùng để verify.
    - [ ] File `inline-field-editor/docs/api-notes.md` có đủ 3 trích dẫn.
  - **Dependencies:** None (chạy song song Task 1 được)
  - **Files likely touched:** `inline-field-editor/docs/api-notes.md` (mới)
  - **Estimated scope:** S

- [ ] **Task 3: Add-on skeleton load được trong Anki thật**
  - **Description:** Tạo `manifest.json` + `__init__.py` tối thiểu (chỉ log "Inline Field Editor
    loaded"), symlink vào `addons21/` của profile `IFE-Test`, xác nhận Anki khởi động không lỗi.
  - **Acceptance criteria:**
    - [ ] Add-on hiện trong Tools → Add-ons, trạng thái enabled, không có traceback.
  - **Verification:**
    - [ ] Manual: khởi động Anki với profile `IFE-Test`, kiểm tra log/console sạch lỗi.
  - **Dependencies:** Task 1
  - **Files likely touched:** `inline-field-editor/manifest.json`, `inline-field-editor/__init__.py`
  - **Estimated scope:** XS

### Checkpoint: Foundation (sau Task 1-3)
- [ ] API thật đã verify (Task 2) — nếu phương án field filter không khả thi như spec giả định,
  dừng lại báo user trước khi sang Phase 1 (đổi kiến trúc là quyết định cần xác nhận, không tự ý).
- [ ] Add-on skeleton load sạch trong profile test.
- [ ] Review với user trước khi tiếp tục.

### Phase 1: Vertical slice — 1 field edit + save hoạt động end-to-end

- [ ] **Task 4: Field filter render `{{edit:Field}}` thành vùng editable**
  - **Description:** Đăng ký field filter (theo API đã verify ở Task 2) xử lý cú pháp
    `edit:FieldName`, trả về `<span data-ife-field="FieldName" contenteditable="true"
    class="ife-editable">{content}</span>` thay vì render field thô.
  - **Acceptance criteria:**
    - [ ] Card có `{{edit:Front}}` trong template → HTML render ra đúng span wrapper với đúng
      `data-ife-field` và nội dung field gốc.
    - [ ] Field không đánh dấu `edit:` vẫn render bình thường, không bị đổi.
  - **Verification:**
    - [ ] `pytest inline-field-editor/tests/test_field_filter.py` — test hàm build wrapper HTML
      (input: field name + content → output: HTML string), không cần Anki thật.
    - [ ] Manual: xem "Card Info" / HTML source trong Anki thật (profile `IFE-Test`) thấy đúng
      span.
  - **Dependencies:** Task 2, Task 3
  - **Files likely touched:** `inline-field-editor/editor_hook.py`,
    `inline-field-editor/tests/test_field_filter.py`
  - **Estimated scope:** S

- [ ] **Task 5: JS wiring — blur gửi nội dung mới về Python, Python lưu vào note**
  - **Description:** `inline_edit.js` (inject qua hook đã verify) tìm mọi `[data-ife-field]`, gắn
    listener `blur` → gửi `pycmd("ife:save:<noteId>:<fieldName>", newHTML)`. Python nhận qua
    bridge hook, tìm đúng note, cập nhật field, gọi API lưu đã verify ở Task 2.
  - **Acceptance criteria:**
    - [ ] Gõ text mới vào field trong Anki thật (profile test), click ra ngoài → mở Browser tìm
      đúng note thấy field đã cập nhật.
    - [ ] Field khác (không editable) không bị đụng tới.
  - **Verification:**
    - [ ] Manual (bắt buộc — đây là vertical slice cốt lõi).
    - [ ] `pytest` cho hàm parse message string (`"ife:save:<noteId>:<fieldName>"` →
      `(note_id, field_name)`) nếu logic đủ để tách hàm riêng test được.
  - **Dependencies:** Task 4
  - **Files likely touched:** `inline-field-editor/web/inline_edit.js`,
    `inline-field-editor/editor_hook.py`, `inline-field-editor/tests/test_bridge_message.py`
  - **Estimated scope:** M

- [ ] **Task 6: Xác nhận việc edit không ảnh hưởng scheduling**
  - **Description:** Trên 1 note test, sửa field editable rồi bấm Again/Good như bình thường —
    đối chiếu interval/due date trước/sau qua "Card Info" để chắc chắn add-on không vô tình
    trigger `answerCard` hoặc đổi scheduling.
  - **Acceptance criteria:**
    - [ ] Interval/due chỉ đổi do bấm Again/Good, không đổi do hành động edit/save field.
  - **Verification:**
    - [ ] Manual, ghi lại Card Info trước và sau trong `docs/api-notes.md` hoặc note riêng.
  - **Dependencies:** Task 5
  - **Files likely touched:** none
  - **Estimated scope:** XS

### Checkpoint: Core vertical slice (sau Task 4-6)
- [ ] 1 field edit + auto-save hoạt động thật trong Anki, scheduling không bị ảnh hưởng.
- [ ] Đây là lúc đạt phần lõi nhất của "Success Criteria" trong SPEC.md — **dừng lại, review với
  user trước khi làm Phase 2** (đúng tinh thần incremental — chưa cần format/sanitize nếu user
  muốn dừng ở đây đã dùng được).

### Phase 2: Formatting + an toàn dữ liệu

- [ ] **Task 7: Bold/Italic/Underline shortcuts trong vùng editable**
  - **Description:** JS bắt `keydown` Ctrl+B/I/U khi focus trong `.ife-editable`, toggle format
    (qua `document.execCommand` hoặc Selection/Range API nếu `execCommand` không còn hoạt động
    trong Qt WebEngine bundle của Anki — verify trong lúc làm task này).
  - **Acceptance criteria:**
    - [ ] Ctrl+B/I/U hoạt động đúng khi đang focus trong field editable.
    - [ ] Phím tắt review gốc (Space, số 1-4, Enter...) vẫn hoạt động bình thường khi KHÔNG
      focus trong field editable.
  - **Verification:**
    - [ ] Manual trong Anki thật (profile test) — test từng phím tắt riêng.
  - **Dependencies:** Task 5
  - **Files likely touched:** `inline-field-editor/web/inline_edit.js`
  - **Estimated scope:** S

- [ ] **Task 8: Fail-safe khi lưu lỗi + sanitize HTML input**
  - **Description:** Bọc try/except quanh bước lưu note — lỗi thì giữ nguyên field cũ, không ghi
    đè, log lỗi rõ ràng. Thêm hàm sanitize loại `<script>` và attribute `on*=` khỏi HTML trước khi
    lưu.
  - **Acceptance criteria:**
    - [ ] Giả lập lỗi lưu (note bị xoá giữa chừng) → field cũ trong DB không đổi.
    - [ ] Input `<script>alert(1)</script>` → lưu vào field không còn tag script.
  - **Verification:**
    - [ ] `pytest inline-field-editor/tests/test_html_sanitize.py`
    - [ ] `pytest inline-field-editor/tests/test_save_failure.py` (mock Collection API để giả lập
      lỗi).
  - **Dependencies:** Task 5
  - **Files likely touched:** `inline-field-editor/editor_hook.py`,
    `inline-field-editor/tests/test_html_sanitize.py`,
    `inline-field-editor/tests/test_save_failure.py`
  - **Estimated scope:** S

### Checkpoint: Formatting & safety (sau Task 7-8)
- [ ] `pytest inline-field-editor/tests` pass 100%.
- [ ] Format shortcuts + fail-safe đã verify thủ công trong Anki thật.

### Phase 3: Polish

- [ ] **Task 9: Visual indicator (hover/focus outline) cho vùng editable**
  - **Description:** CSS outline nhẹ khi hover, rõ hơn khi focus, để phân biệt field editable với
    field thường ngay khi nhìn vào card.
  - **Acceptance criteria:**
    - [ ] Nhìn card lúc review thấy rõ field nào editable trước khi click.
  - **Verification:**
    - [ ] Manual, so sánh trước/sau bằng mắt.
  - **Dependencies:** Task 4
  - **Files likely touched:** `inline-field-editor/web/inline_edit.css`
  - **Estimated scope:** XS

- [ ] **Task 10: README cho add-on + đóng gói thử `.ankiaddon`**
  - **Description:** Viết `inline-field-editor/README.md` (cách dùng `{{edit:Field}}`, cách cài,
    giới hạn hiện tại). Chạy lệnh zip đóng gói (đã có trong SPEC.md → Commands), cài thử file
    `.ankiaddon` vào profile test để xác nhận hoạt động giống hệt symlink.
  - **Acceptance criteria:**
    - [ ] README tồn tại, đúng nội dung thực tế đã build.
    - [ ] File `.ankiaddon` cài lại được, hoạt động đúng.
  - **Verification:**
    - [ ] Manual: cài `.ankiaddon` vào profile `IFE-Test`, test lại flow edit+save cơ bản.
  - **Dependencies:** Task 7, Task 8
  - **Files likely touched:** `inline-field-editor/README.md`
  - **Estimated scope:** XS

### Checkpoint: Complete
- [ ] Toàn bộ Success Criteria trong SPEC.md đạt.
- [ ] `pytest inline-field-editor/tests` pass 100%.
- [ ] README xong, `.ankiaddon` cài thử OK.
- [ ] Đề xuất commit message cho user xác nhận (theo Git workflow trong CLAUDE.md) — không tự
  `git commit`/`push` trừ khi đang chạy dưới `/autopilot`.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Cơ chế field filter kiểu cũ (`{{edit:Field}}`) có thể không còn hoạt động đúng ở bản Anki hiện tại (template engine đã chuyển sang Rust backend) | High | Verify sớm nhất ở Task 2, trước khi code bất kỳ phần nào khác. Nếu không khả thi, dừng và báo user để đổi kiến trúc (vd JS tự chèn `contenteditable` dựa trên field có class riêng thay vì cú pháp `edit:`) — đây là thay đổi kiến trúc, không tự ý quyết định. |
| `document.execCommand` (Task 7) đã deprecated, có thể bị chặn trong Qt WebEngine bundle của Anki | Medium | Test sớm trong Task 7; có phương án dự phòng dùng Selection/Range API thủ công nếu cần. |
| Bridge message (`pycmd`) đụng namespace với add-on khác đã cài trên máy (Review Heatmap + 1 add-on khác) | Low | Prefix `ife:` cho mọi message (đã chốt trong SPEC.md Code Style). |
| Test thủ công lỡ tay đụng vào profile Anki thật (`User 1`) làm hỏng dữ liệu học thật | Medium | Task 1 tạo riêng profile `IFE-Test` — mọi bước manual verify trong plan này đều ghi rõ chạy trên profile test, không phải `User 1`. |

## Open Questions

- Tất cả Open Questions kỹ thuật trong SPEC.md sẽ được trả lời dứt điểm ở Task 2 (verify API) —
  không còn open question mới phát sinh ở bước planning này ngoài rủi ro đã liệt kê ở trên.
