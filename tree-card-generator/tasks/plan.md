# Implementation Plan: Tree Card Generator

> Đặt trong `tree-card-generator/tasks/plan.md` — cùng quy ước với các add-on khác trong repo.

## Overview

Dựa trên [SPEC.md](../SPEC.md): dán text tree ASCII vào popup dialog trong Editor, bấm Generate
→ parse thành cây → render HTML tự chứa (CSS+JS nhúng sẵn, section có con thì click mở/thu gọn
được) → copy vào clipboard dạng rich-HTML, user tự dán vào field. Rủi ro kỹ thuật lớn nhất
(`QMimeData.setHtml()` paste vào Anki Editor có hoạt động không) **chưa verify** — phải xác nhận
sớm nhất có thể (Task 2) trước khi đầu tư code parser/renderer, vì nếu cơ chế này không hoạt
động thì cả kiến trúc "copy clipboard" phải bàn lại từ đầu.

## Architecture Decisions

- **Verify rủi ro cao nhất trước tiên (Task 2), trước cả parser/renderer** — khác thứ tự thông
  thường (thường làm logic thuần trước) vì đây là "Risk-First Slicing": nếu `QMimeData.setHtml()`
  không paste đúng vào `NewEditor`, toàn bộ hướng "copy clipboard" (đã chốt ở `/spec` sau khi phát
  hiện API cũ deprecated) phải xem lại — phát hiện sớm rẻ hơn nhiều so với phát hiện ở Task 6.
- **Tách `dialog.py` (UI, không test) khỏi `tree_parser.py`/`tree_renderer.py` (logic thuần, TDD)**
  — đúng pattern đã dùng xuyên suốt các add-on khác trong repo.
- **Task verify clipboard dùng 1 nút tạm thời/script test riêng**, không phải dialog thật —
  tránh code 2 lần (nếu verify xong thấy cơ chế khác đi thì chỉ bỏ đoạn test nhỏ, không phải
  refactor cả dialog).

## Task List

### Phase 0: Foundation & rủi ro kỹ thuật cao nhất

- [x] **Task 1: Venv + add-on skeleton load sạch trong Anki thật** — DONE, user xác nhận.
  - **Description:** Venv riêng, cài `pytest` + `aqt`. `manifest.json` + `__init__.py` tối
    thiểu (log "Tree Card Generator loaded"), Junction vào `addons21/`.
  - **Acceptance criteria:**
    - [ ] Add-on hiện trong Tools → Add-ons, enabled, không traceback.
  - **Verification:**
    - [ ] Tự giả lập `importlib.import_module('tree-card-generator')` qua `addons21/` trước.
    - [ ] Manual: user restart Anki, xác nhận trong Tools → Add-ons.
  - **Dependencies:** None
  - **Files likely touched:** `tree-card-generator/manifest.json`,
    `tree-card-generator/__init__.py`
  - **Estimated scope:** XS

- [x] **Task 2: Verify `QMimeData.setHtml()` paste vào Anki Editor hoạt động đúng** — DONE,
  **GO**. User xác nhận: bấm nút test → Ctrl+V ra đúng "**test bold**" in đậm + "red text" màu
  đỏ (render thật). Kiến trúc "copy clipboard" trong SPEC.md đã được xác nhận khả thi — an toàn
  để tiếp tục Phase 1.
  - **Description:** Thêm tạm 1 nút test vào Editor toolbar (qua `editor_did_init_buttons`) chỉ
    để copy 1 đoạn HTML đơn giản cố định (vd `"<b>test bold</b><br><span
    style='color:red'>red text</span>"`) vào clipboard qua `QMimeData.setHtml()` +
    `mw.app.clipboard().setMimeData()`. Đây là rủi ro kỹ thuật lớn nhất trong toàn bộ plan — verify
    TRƯỚC khi viết parser/renderer.
  - **Acceptance criteria:**
    - [ ] Bấm nút test → dán (Ctrl+V) vào 1 field trong Anki thật → hiển thị đúng "**test bold**"
      in đậm và "red text" màu đỏ (render thật, không phải text thô `<b>test bold</b>`).
  - **Verification:**
    - [ ] Manual bắt buộc (không thể tự động hoá — cần Anki thật + user paste tay).
    - [ ] Nếu KHÔNG hoạt động: dừng lại, báo user, bàn phương án khác trước khi làm tiếp Phase 1
      (vd thử `text/html` mime type khác cách, hoặc quay lại cân nhắc chèn field trực tiếp).
  - **Dependencies:** Task 1
  - **Files likely touched:** tạm thời trong `tree-card-generator/__init__.py` (sẽ dọn/thay
    bằng code thật ở Task 5)
  - **Estimated scope:** XS

### Checkpoint: Foundation & rủi ro kỹ thuật
- [ ] Skeleton load sạch.
- [ ] **Cơ chế clipboard đã verify hoạt động đúng trong Anki thật** — đây là go/no-go cho toàn bộ
  kiến trúc đã chốt ở SPEC.md. Nếu fail, dừng lại bàn phương án khác trước khi sang Phase 1.

### Phase 1: Core logic — parser + renderer (pure, TDD)

- [x] **Task 3: `tree_parser.py` — `parse_tree()` (TDD)** — DONE, 11/11 test pass ngay lần đầu,
  kể cả 5 test dùng chính cây mẫu đầy đủ thật (fixture `tests/fixtures/full_sample_tree.txt`) —
  xác nhận công thức `depth = len(prefix)/4 + 1` đúng trên dữ liệu thật, không chỉ case tối giản.
  - **Description:** Parse text tree ASCII (`├──`/`│`/`└──`, thụt lề 4 ký tự/cấp) thành
    `TreeNode`. Tách timestamp `[hh:mm:ss]` nếu có ở đầu label.
  - **Acceptance criteria:**
    - [ ] Cây 1 cấp, cây nhiều cấp lồng nhau → đúng cấu trúc cha-con theo depth tính từ độ dài
      prefix.
    - [ ] Dòng chỉ có `"│"` (dòng trống ngăn cách giữa các block) → bị bỏ qua, không tạo node
      rỗng.
    - [ ] Node cuối dùng `└──` vs node giữa dùng `├──` → không ảnh hưởng gì tới việc xác định
      cha-con (chỉ ảnh hưởng hiển thị gốc, không phải logic parse).
    - [ ] Label có tiền tố `[00:03:04] ` → tách đúng vào `TreeNode.timestamp`, phần còn lại vào
      `TreeNode.label`; label không có tiền tố này → `timestamp=None`, giữ nguyên label.
    - [ ] Label chứa `<`/`&` → giữ nguyên thô ở bước parse (không escape ở đây — escape là việc
      của `render_html`).
  - **Verification:**
    - [ ] `pytest tree-card-generator/tests` (chạy đúng cách — xem SPEC.md → Commands) pass.
    - [ ] Test riêng với **chính đoạn text tree mẫu đầy đủ** trong SPEC.md (6 section cấp 1,
      nhiều cấp 2/3) → verify đúng tổng số node, đúng cấu trúc, không chỉ test case nhỏ tự bịa.
  - **Dependencies:** None (song song Task 1-2 được — không cần Anki/credentials)
  - **Files likely touched:** `tree-card-generator/tree_parser.py`,
    `tree-card-generator/tests/conftest.py`, `tree-card-generator/tests/test_tree_parser.py`
  - **Estimated scope:** M

- [x] **Task 4: `tree_renderer.py` — `render_html()` (TDD)** — DONE, 9/9 test mới pass (20/20
  tổng). 2 test ban đầu fail vì bug trong chính TEST (CSS tĩnh luôn chứa selector `.tcg-node`/
  `.tcg-timestamp` nên assert "not in toàn bộ output" sai — sửa lại chỉ check phần body trước
  `<style>`). Cũng gặp 1 lần nghi ngờ encoding sai cho ký tự "–"/"▸"/"▾" do console Windows hiện
  `�` — verify lại bằng cách ghi UTF-8 ra file, xác nhận dữ liệu đúng, chỉ là lỗi hiển thị quen
  thuộc của phiên này, không phải bug thật.
  - **Description:** Render `TreeNode` thành HTML tự chứa: node có `children` → section có
    tiêu đề clickable (JS toggle class ẩn/hiện container con) + mặc định thu gọn (xem SPEC.md Open
    Question #1 — giả định collapsed); node lá → bullet đơn giản. Escape HTML entities cho mọi
    label/timestamp.
  - **Acceptance criteria:**
    - [ ] Output có đúng 1 khối `<style>` và 1 khối `<script>`, không phụ thuộc file/CDN ngoài.
    - [ ] Node có con → có phần tử clickable (vd có `onclick`/class riêng) + container con có
      class "thu gọn mặc định" (vd `display:none` hoặc class `collapsed`); node lá → không có gì
      để click, chỉ hiển thị bullet.
    - [ ] Label/timestamp chứa `<script>alert(1)</script>` hoặc `&` → escape đúng trong output
      (dùng `html.escape()`), không làm vỡ markup.
    - [ ] Render thử **cây mẫu đầy đủ từ SPEC.md** (qua `parse_tree()` của Task 3) → output HTML
      hợp lệ (parse lại được bằng 1 HTML parser đơn giản trong test để xác nhận không vỡ cấu
      trúc, vd đếm số thẻ mở/đóng khớp nhau).
  - **Verification:**
    - [ ] `pytest tree-card-generator/tests` pass 100%.
  - **Dependencies:** Task 3 (dùng chung `TreeNode`, và test tích hợp parse→render cây mẫu đầy
    đủ)
  - **Files likely touched:** `tree-card-generator/tree_renderer.py`,
    `tree-card-generator/tests/test_tree_renderer.py`
  - **Estimated scope:** M

### Checkpoint: Core logic
- [ ] Parser + renderer test kỹ với cả case nhỏ tự bịa lẫn cây mẫu đầy đủ thật từ SPEC.md.
- [ ] `pytest` pass 100%, chưa cần Anki thật cho phase này.

### Phase 2: UI wiring — dialog thật + copy clipboard

- [ ] **Task 5: `dialog.py` + wiring `__init__.py` — dialog thật, thay đoạn test tạm ở Task 2**
  - **Description:** `QDialog` với `QPlainTextEdit` (nhập text tree) + `QPushButton` "Generate &
    Copy". Bấm Generate: `parse_tree()` → `render_html()` → copy vào clipboard qua cơ chế đã
    verify ở Task 2 (không phải đoạn test cố định nữa, mà HTML thật từ renderer). `__init__.py`
    đăng ký nút mở dialog qua `editor_did_init_buttons` (xoá đoạn nút test tạm của Task 2).
  - **Acceptance criteria:**
    - [ ] Nút "Tree Card" (hoặc tên tương tự) hiện trong Editor toolbar.
    - [ ] Bấm nút → dialog mở, có ô nhập text + nút Generate & Copy.
    - [ ] Dán text tree mẫu từ SPEC.md vào ô nhập, bấm Generate → clipboard chứa HTML đúng (dán
      thử ra 1 field thấy đúng cấu trúc, khớp với những gì Task 3-4 đã test).
  - **Verification:**
    - [ ] Manual trong Anki thật (bắt buộc — đây là vertical slice hoàn chỉnh của cả plan).
  - **Dependencies:** Task 2 (cơ chế clipboard đã verify), Task 4 (renderer)
  - **Files likely touched:** `tree-card-generator/dialog.py`, `tree-card-generator/__init__.py`
  - **Estimated scope:** M

- [ ] **Task 6: Manual end-to-end verify đầy đủ với cây mẫu thật**
  - **Description:** Dùng đúng đoạn text tree đầy đủ 6 section trong SPEC.md (không phải bản rút
    gọn), test toàn bộ flow trong Anki thật (profile `IFE-Test`).
  - **Acceptance criteria:**
    - [ ] Cả 6 section cấp 1 hiển thị đúng, thu gọn mặc định.
    - [ ] Bấm mở 1 section → chỉ section đó mở, các section khác không bị ảnh hưởng.
    - [ ] Mở tiếp section con (cấp 2, có timestamp) → hiển thị đúng timestamp + label tách riêng.
    - [ ] Cấp lá (cấp 3) hiển thị bullet, không có gì để bấm.
    - [ ] Test 1 label có ký tự đặc biệt (thêm thủ công `<test>` vào 1 dòng text tree) → không
      vỡ layout.
  - **Verification:**
    - [ ] Manual, checklist đầy đủ ở Acceptance criteria — profile test, không dùng profile thật.
  - **Dependencies:** Task 5
  - **Files likely touched:** none
  - **Estimated scope:** S

### Checkpoint: UI hoàn chỉnh
- [ ] Toàn bộ Success Criteria trong SPEC.md đạt.
- [ ] Review với user trước khi sang Phase 3 (polish, không bắt buộc phải làm ngay).

### Phase 3: Polish

- [ ] **Task 7: README cho add-on + đóng gói thử `.ankiaddon`**
  - **Description:** Viết `tree-card-generator/README.md` (cách dùng, cú pháp tree input được hỗ
    trợ, giới hạn hiện tại — vd không hỗ trợ tab, chỉ ASCII connector chuẩn). Đóng gói + cài thử.
  - **Acceptance criteria:**
    - [ ] README tồn tại, đúng nội dung thực tế.
    - [ ] File `.ankiaddon` cài lại được, hoạt động đúng.
  - **Verification:**
    - [ ] Manual: cài `.ankiaddon`, test lại flow cơ bản.
  - **Dependencies:** Task 6
  - **Files likely touched:** `tree-card-generator/README.md`
  - **Estimated scope:** XS

### Checkpoint: Complete
- [ ] Toàn bộ Success Criteria trong SPEC.md đạt, README xong.
- [ ] Đề xuất commit — chỉ commit code (không commit `.venv/`, output test tay nếu có).

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| `QMimeData.setHtml()` không paste đúng vào `NewEditor` (Svelte-based, có thể xử lý paste khác biệt) | **High** — nếu fail, toàn bộ kiến trúc "copy clipboard" đã chốt ở `/spec` phải bàn lại | Verify NGAY ở Task 2, trước khi đầu tư code parser/renderer — risk-first slicing, phát hiện sớm rẻ hơn nhiều. |
| Parser tính sai depth khi text tree có thụt lề không đúng bội số 4 (vd user tự gõ tay, lỡ tay thêm/bớt space) | Medium | Task 3 test với **chính cây mẫu đầy đủ thật** (copy nguyên văn từ SPEC.md), không chỉ test case tối giản tự bịa — bắt lỗi thực tế sớm. |
| Label chứa HTML đặc biệt phá vỡ output (XSS-like, dù chỉ dùng cá nhân vẫn nên làm đúng) | Low-Medium | `html.escape()` bắt buộc, có test riêng cho case này ở cả Task 3 (giữ nguyên lúc parse) và Task 4 (escape lúc render). |
| Test thủ công lỡ đụng profile Anki thật (`User 1`) | Medium | Dùng profile test `IFE-Test` — không test trên `User 1`. |

## Open Questions

- Không phát sinh thêm ở bước planning — 3 Open Question trong SPEC.md (trạng thái mặc định
  collapsed/expanded, tên add-on, verify clipboard) sẽ được xác nhận/giải quyết ở Task 2 (verify)
  và trong lúc thực hiện Task 4-6.
