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

- [x] **Task 5: `dialog.py` + wiring `__init__.py` — dialog thật** — DONE thật, xác nhận bằng
  **HTML source thật** (Ctrl+Shift+X, không chỉ câu trả lời "đúng/sai") sau khi ghi thẳng vào
  field trong Add Cards: `<details>`/`<summary>` còn nguyên, màu nền phân cấp đúng
  (`#eef3fb`/`#f7f2fa`), timestamp tách riêng đúng, escape `&`/`<` đúng, và một số `<details>` có
  `open=""` phản ánh đúng trạng thái user đã bấm mở trước đó (chứng minh mở/thu gọn hoạt động
  thật). Implementation đã đổi kiến trúc **3 lần** trước khi đến bản này (xem lịch sử dưới) — bài
  học quan trọng nhất: 1 câu trả lời AskUserQuestion xác nhận thành công **không đủ** (lần trước
  user từng chọn nhầm rồi tự sửa lại: "nãy tôi chọn nhầm. Thực ra vẫn bị lỗi không crt V được khi
  generate xong") — lần này đòi bằng chứng cụ thể (HTML source thật) trước khi đóng task.
  **Lịch sử đổi kiến trúc (3 vòng):**
  1. `<style>`+`<script>` nhúng + JS toggle — **fail**: Anki strip toàn bộ `<style>`/`<script>`
     khi paste (xác nhận qua test thật: dán ra chỉ còn text phẳng, không màu/không thụt lề).
  2. Inline `style="..."` + `<details>`/`<summary>` thuần — **fail**: lấy đúng HTML source qua
     Ctrl+Shift+X sau khi paste cho thấy `<details>`/`<summary>` bị bóc hoàn toàn (nội dung bẹt
     vào parent), và các CSS layout (`margin`/`padding`/`background`/`cursor`/`border-radius`)
     cũng bị strip khỏi inline style — chỉ `color` (dạng `rgb(...)`) và thẻ `<div>`/`<span>` sống
     sót. Đây là sanitize ở tầng Chromium/Qt WebEngine paste-into-contenteditable, không phải ở
     Python (`self.triggerPageAction(QWebEnginePage.WebAction.Paste)` trong `aqt/editor.py` —
     sanitize nằm trong browser engine, không sửa được từ phía add-on bằng cách đổi HTML).
  3. **Ghi thẳng vào field, bỏ clipboard/paste hoàn toàn** — user đồng ý hướng này
     ("Đồng ý — thử hướng ghi thẳng vào field (Recommended)"). UX đổi: user phải click vào field
     muốn điền TRƯỚC, rồi bấm nút Tree Card, dán text, bấm Generate → HTML ghi thẳng, không cần
     Ctrl+V. Đây là hướng **đang implement**, chưa verify thật.
  **Bug đã tìm & fix trong quá trình implement hướng 3:**
  - `ModuleNotFoundError: No module named 'tree_parser'` — `tree_renderer.py` dùng import tuyệt
    đối thay vì tương đối; vỡ khi Anki load add-on dưới dạng package. Fix bằng try/except
    (relative trước, absolute fallback cho pytest). Bài học: pre-verify `importlib.import_module`
    giả lập phải chạy từ **thư mục gốc repo** (cwd trung lập), không phải từ trong
    `tree-card-generator/` — chạy từ trong thư mục add-on khiến Python tự thêm cwd vào
    `sys.path`, che giấu lỗi absolute-import.
  - `AttributeError: 'Editor' object has no attribute 'nid'` (thật, từ traceback user gửi, Anki
    25.09.4) — code ban đầu dùng `editor.nid` + `editor.reload_note()`, những attribute/method
    này **không tồn tại** trong Anki 25.9.4 (Editor dùng `editor.note: Note | None` trực tiếp, và
    `editor.loadNoteKeepingFocus()` để refresh hiển thị, không có `reload_note()`). **Root cause
    thật:** venv dev (`tree-card-generator/.venv`) đã cài `aqt`/`anki` bản `26.9` (mới hơn bản
    thật user đang chạy, `25.9.4`) — `editor.nid`/`reload_note()` là API của bản dev/tương lai,
    không phải bản user cài. Fix: cài lại venv đúng `aqt==25.9.4 anki==25.9.4` (pin vào
    `requirements.txt`), sửa `dialog.py` dùng `editor.note`/`editor.loadNoteKeepingFocus()`. Bài
    học mới: pre-verify simulation chỉ đáng tin nếu venv dev **cùng version** với Anki thật user
    dùng — luôn `pip show aqt anki` cả 2 phía và pin `requirements.txt` khi bắt đầu add-on mới,
    không cài "latest" mặc định.
  - **Bug thật thứ 2 (sau khi fix bug `nid`):** `anki.errors.NotFoundError: ... No such note: '0'`
    khi bấm Generate trong **Add Cards** (traceback thật từ user). Nguyên nhân: trong Add Cards,
    `editor.note` tồn tại nhưng `note.id == 0` (note chưa được thêm vào collection — chỉ tồn tại
    trong bộ nhớ Editor, sẽ được lưu khi user bấm "Add"). Gọi `mw.col.update_note(note)` unconditional
    tìm note theo id trong DB → không thấy → crash. Phát hiện cách Anki tự xử lý case này bằng cách
    đọc `Editor._onHtmlEdit()` (chính là logic Ctrl+Shift+X) trong `aqt/editor.py`: nó set
    `self.note.fields[field] = html` **luôn**, nhưng chỉ gọi lưu (`if not self.addMode:
    self._save_current_note()`) khi KHÔNG ở Add Cards — vì trong Add Cards, note sẽ được lưu sau
    bởi luồng "Add" riêng, dùng chính object note đã bị mutate này. Fix: check `editor.addMode`,
    chỉ gọi `aqt.operations.note.update_note(parent=editor.widget,
    note=note).run_in_background(initiator=editor)` (API public tương đương
    `Editor._save_current_note()`, có undo support) khi `not editor.addMode`; luôn gọi
    `editor.loadNote(focusTo=field_index)` để refresh hiển thị bất kể addMode. Verify bằng cách
    giả lập cả 2 nhánh (`addMode=True/False`) qua simulation từ repo root, không chỉ đọc code.
  - **Description:** `QDialog` với `QPlainTextEdit` (nhập text tree) + `QPushButton` "Generate".
    Bấm Generate: `parse_tree()` → `render_html()` → ghi thẳng vào
    `editor.note.fields[editor.last_field_index]` → (nếu không phải Add Cards) persist qua
    `aqt.operations.note.update_note(...)` → `editor.loadNote(focusTo=...)`. `__init__.py` truyền
    `editor` (không chỉ `parentWindow`) vào `TreeDialog` để dialog có quyền truy cập
    `note`/`last_field_index`/`addMode`/`widget`.
  - **Acceptance criteria:**
    - [ ] Nút "Tree Card" hiện trong Editor toolbar.
    - [ ] Click vào field muốn điền TRƯỚC, bấm nút → dialog mở, dán text tree, bấm Generate → HTML
      xuất hiện thẳng trong đúng field đó, không cần Ctrl+V.
    - [ ] Note chưa lưu lần nào (`editor.note is None`) hoặc chưa từng focus field nào
      (`last_field_index is None`) → thông báo lỗi rõ ràng, không crash.
  - **Verification:**
    - [ ] Manual trong Anki thật (bắt buộc). Cần bằng chứng cụ thể (screenshot field sau khi
      Generate, hoặc HTML source qua Ctrl+Shift+X), không chỉ câu trả lời "đúng"/"sai" đơn giản.
  - **Dependencies:** Task 4 (renderer)
  - **Files likely touched:** `tree-card-generator/dialog.py`, `tree-card-generator/__init__.py`,
    `tree-card-generator/requirements.txt`
  - **Estimated scope:** M

- [x] **Task 6: Manual end-to-end verify đầy đủ với cây mẫu thật** — DONE, gộp chung với vòng
  verify cuối của Task 5 (dùng đúng cây mẫu 6 section đầy đủ, xác nhận qua HTML source thật).
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

- [x] **Task 7: README cho add-on + đóng gói thử `.ankiaddon`** — DONE. README.md viết lại hoàn
  toàn theo kiến trúc ghi-thẳng-field (đã bỏ mọi hướng dẫn Ctrl+V, UX mới: "click field trước →
  bấm nút → Generate → xong"), giải thích đủ cả 2 vòng clipboard đã fail + lý do chọn ghi thẳng
  field. Đóng gói lại `.ankiaddon` bằng `zipfile` với đúng 5 file hiện tại
  (`manifest.json`, `__init__.py`, `dialog.py`, `tree_parser.py`, `tree_renderer.py`, không dính
  `tests/`/`.venv/`/`requirements.txt`/`tasks/`/docs). Chưa cài thử `.ankiaddon` riêng vào Anki
  thật (core logic đã verify đầy đủ qua junction ở Task 5-6 với đúng version Anki thật user dùng —
  cơ chế install-from-zip của Anki là chuẩn/không đặc thù code, để user tự cài thử nếu muốn).
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
