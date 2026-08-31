# Spec: Inline Field Editor (add-on `inline-field-editor`)

> Đây là spec cho **1 add-on cụ thể** trong repo nhiều-add-on `anki-addons` — đặt trong
> `inline-field-editor/SPEC.md` (không phải root repo), theo đúng quy ước "mỗi add-on 1 folder
> riêng" trong [CLAUDE.md](../CLAUDE.md) — vì repo sẽ có nhiều add-on, mỗi cái cần spec riêng.

## Objective

Add-on cho phép sửa nội dung field của note **ngay trong màn hình review** (câu hỏi hoặc câu
trả lời), không cần mở cửa sổ Editor/Browser riêng — lấy cảm hứng từ add-on
["Edit Field During Review"](https://ankiweb.net/shared/info/1020366288), nhưng scope hẹp hơn:
chỉ giữ lại cơ chế cốt lõi (inline edit qua template + auto-save), bỏ các tính năng phức tạp
(cloze editor, chèn ảnh/LaTeX, config UI đa note-type) mà bản gốc có.

**User:** chỉ Dang (cá nhân), dùng cho deck của mình. Không nhắm tới publish AnkiWeb.

**Vấn đề cần giải quyết:** khi review gặp lỗi chính tả/nội dung cần sửa nhỏ trong 1 field, hiện
phải thoát review → mở Browser → tìm note → sửa → quay lại review, làm gãy flow học. Add-on này
cho sửa tại chỗ, mất focus (blur) khỏi field là tự lưu, không làm gián đoạn lịch ôn tập của card.

**Success = xong khi:** đánh dấu 1 field bằng `{{edit:FieldName}}` trong template, lúc review
field đó hiện ra như 1 vùng có thể click-and-type ngay trong nội dung card, gõ xong click ra
ngoài là nội dung được lưu vào note thật — mà không ảnh hưởng gì tới trạng thái scheduling của
card đang review.

## Tech Stack

- Python (bám theo interpreter Anki bundle sẵn — xem "Open Questions" về version cụ thể)
- `aqt` (`gui_hooks`) cho phần tích hợp UI/reviewer; `anki` (`Note`, `Collection`) cho phần cập
  nhật dữ liệu — theo đúng ranh giới `aqt` vs `anki` đã nêu trong CLAUDE.md.
- JS/CSS thuần (vanilla), inject trực tiếp vào reviewer webview qua hook — **không** dựng build
  pipeline TypeScript/webpack như bản gốc, vì scope nhỏ (chỉ cần contenteditable + vài phím tắt
  format), tránh over-engineering cho use case cá nhân.
- `pytest` cho phần logic Python thuần (không đụng `aqt`).

## Commands

```bash
# Test (phần logic thuần, không cần Anki thật chạy) — PHẢI chạy với cwd bên trong tests/,
# không phải "pytest inline-field-editor/tests" từ repo root (xem lưu ý bên dưới).
cd inline-field-editor/tests
../.venv/Scripts/python -m pytest . -v

# Cài venv riêng để chạy test / đọc source anki-aqt thật (không dùng để chạy Anki)
cd inline-field-editor
python -m venv .venv
.venv/Scripts/pip install aqt pytest

# Cài để test thủ công trong Anki thật (Windows) — máy không có quyền admin nên dùng Junction
# thay vì symbolic link (New-Item -ItemType SymbolicLink báo "Administrator privilege required")
New-Item -ItemType Junction `
  -Path "$env:APPDATA\Anki2\addons21\inline-field-editor" `
  -Target "C:\Users\Client\Desktop\anki-addons\inline-field-editor"
# Restart Anki sau khi tạo junction, rồi Tools → Add-ons → View Files để xác nhận đúng thư mục.
# addons21/ dùng chung cho MỌI profile — chỉ profile IFE-Test mới dùng để test thao tác thật.

# Đóng gói .ankiaddon (khi cần chia sẻ/backup, không phải bước bắt buộc cho dùng cá nhân)
cd inline-field-editor
zip -r ../inline-field-editor.ankiaddon . -x "__pycache__/*" "meta.json" "tests/*" ".venv/*"
```

> **Lưu ý về lệnh test:** tên thư mục add-on có dấu gạch ngang (`inline-field-editor`) — hợp lệ
> với cách Anki tự import add-on (dùng `importlib.import_module()` với string thô, không qua cú
> pháp `import` nên không cần định danh Python hợp lệ), nhưng **không hợp lệ** với cơ chế
> "Package" collection của pytest khi bạn truyền đường dẫn dạng `pytest inline-field-editor/tests`
> — pytest cố coi `inline-field-editor` là 1 Python package (vì có `__init__.py`) rồi import nó
> theo tên thư mục, vốn không phải định danh hợp lệ (`isidentifier()` = False vì dấu `-`), dẫn tới
> lỗi `attempted relative import with no known parent package`. Cách né: `cd` vào `tests/` trước
> rồi chạy `pytest .` — khi đó pytest không còn lý do đi ngược lên thư mục cha có `__init__.py`.

Lint/format: **TBD** — repo chưa setup `ruff`/`black`. Đề xuất thêm `ruff` (format + lint 1 tool)
khi bắt đầu implement, nhưng không block spec này.

## Project Structure

```
inline-field-editor/
  manifest.json          # name, package (string local-only, vd "inline-field-editor"), mod
  __init__.py             # entry point — đăng ký hook, import module con
  editor_hook.py           # logic Python: parse {{edit:Field}} ra field name, xử lý message
                            #   "save field" từ JS, gọi Collection API để lưu vào note
  web/
    inline_edit.js          # vanilla JS: bắt DOM {{edit:Field}} render ra, gắn contenteditable,
                              #   xử lý blur → gửi nội dung mới qua bridge (pycmd)
    inline_edit.css          # style nhẹ cho vùng editable (outline khi hover/focus)
  tests/
    test_template_parse.py   # test hàm parse "{{edit:Field}}" trong template string, không
                               #   import aqt
    test_html_sanitize.py     # test hàm làm sạch HTML trước khi lưu (nếu có bước sanitize)
```

## Code Style

- Type hint cho public function. Ví dụ hàm tách tên field từ cú pháp `{{edit:Field}}`:

  ```python
  import re

  EDIT_FIELD_PATTERN = re.compile(r"\{\{edit:([^}]+)\}\}")

  def extract_editable_field_names(template: str) -> list[str]:
      """Return field names marked with {{edit:FieldName}} in a card template."""
      return EDIT_FIELD_PATTERN.findall(template)
  ```

- Module xử lý logic thuần (`editor_hook.py` phần parse/sanitize) **không** `import aqt` —
  chỉ phần đăng ký hook trong `__init__.py` mới chạm `aqt`. Giữ đúng boundary data-vs-UI trong
  CLAUDE.md.
- Không `print()` — dùng `logging` cho debug nội bộ.
- JS: không dùng framework ngoài, `pycmd()` là kênh giao tiếp duy nhất về Python, đặt tên message
  có prefix rõ ràng (vd `"ife:save:<fieldName>"`) để tránh đụng bridge command của add-on khác.

## Testing Strategy

- **Unit test** (`pytest`, không cần Anki thật): hàm parse `{{edit:Field}}` từ template string,
  hàm sanitize HTML input trước khi ghi vào field (loại `<script>`, giữ format tag cơ bản).
- **Manual verify trong Anki thật** (bắt buộc trước khi coi task xong — theo CLAUDE.md "Testing
  standards" và autopilot self-verify): field đánh dấu `{{edit:...}}` hiện đúng như vùng edit
  được; gõ + click ra ngoài lưu đúng vào note (kiểm tra lại trong Browser); review tiếp card đó
  không bị coi là "đã trả lời"/không đổi interval; field KHÔNG đánh dấu `{{edit:...}}` không bị
  đổi thành editable.
- Không cần golden dataset hay coverage target hình thức — scope nhỏ, cá nhân dùng, ưu tiên test
  đúng behavior thật hơn là % coverage.

## Boundaries

- **Luôn làm:**
  - Auto-save khi blur không được làm mất nội dung cũ nếu có lỗi khi lưu (fail-safe: giữ nguyên
    field cũ, không ghi đè bằng rỗng/lỗi).
  - Việc lưu field qua add-on này không được trigger `answerCard`/đổi scheduling của card đang
    review — đây là bug nghiêm trọng nếu xảy ra, phải test kỹ trước khi coi feature xong.
  - Chỉ field có `{{edit:FieldName}}` tường minh trong template mới thành editable — field khác
    giữ nguyên hành vi render bình thường.
- **Hỏi trước:**
  - Đổi cú pháp đánh dấu field (nếu muốn khác `{{edit:Field}}` của bản gốc).
  - Bất kỳ thao tác nào sửa template của note type **thật** đang dùng trong collection cá nhân
    (vd tự động chèn `{{edit:...}}` vào template có sẵn) — chỉ làm khi user tự tay sửa hoặc xác
    nhận rõ ràng, vì đây là thay đổi khó undo qua UI thường.
  - Thêm bất kỳ format/tính năng nào ngoài bold/italic/underline (vd ảnh, cloze, LaTeX) — ngoài
    scope đã chốt, cần user xác nhận muốn mở rộng trước khi làm.
- **Không bao giờ:**
  - Đọc/ghi trực tiếp lên file `.anki2`/`collection.media` thật của user ngoài qua Collection API
    chính thức của Anki (đúng hard-stop đã có trong `autopilot.md`).
  - Tự cài/symlink add-on vào `addons21/` thật mà chưa được yêu cầu tường minh trong phiên làm
    việc đó.
  - Lưu HTML chưa qua bước làm sạch tối thiểu (chặn `<script>`) vào field.

## Success Criteria

- Đánh dấu 1 field trong template bằng `{{edit:FieldName}}` → lúc review, field đó hiện dạng
  editable ngay trong nội dung card (không cần thao tác thêm để "vào chế độ edit").
- Gõ nội dung mới, click ra ngoài field (blur) → mở lại note trong Browser thấy field đã cập
  nhật đúng nội dung mới.
- Ctrl+B / Ctrl+I / Ctrl+U hoạt động đúng (bold/italic/underline) khi đang focus trong field
  editable.
- Trả lời/next card sau khi edit field không bị coi là đã "Again/Good/..." ngoài ý muốn — interval
  của card không đổi do việc edit.
- Field không đánh dấu `{{edit:...}}` vẫn hiển thị y hệt hành vi Anki gốc (không editable, không
  đổi style).
- `pytest inline-field-editor/tests` pass 100%.

## Open Questions

1. **Target Anki version / API cụ thể** — Anki 24.x/25.x dùng Rust backend, cách lưu note đã đổi
   qua các bản (`note.flush()` cũ vs `col.update_note(note)` mới). Cần verify bằng cách kiểm tra
   version Anki + package `anki`/`aqt` đang cài trên máy trước khi code phần lưu note, không
   assume theo trí nhớ training data (đúng nguyên tắc CS5 trong CLAUDE.md).
2. **Tên add-on** — tạm đặt `inline-field-editor`. Xác nhận lại tên này hay đổi tên khác trước
   khi tạo `manifest.json`.
3. **Cú pháp bridge message** (`pycmd`) — cần kiểm tra cơ chế `webview_did_receive_js_message`
   hook hiện tại của `aqt.gui_hooks` (tên hook/API có thể đã đổi giữa các bản Anki) trước khi
   implement, không giả định tên hook từ trí nhớ.
4. **Có cần chặn edit khi đang ở màn hình Answer (sau khi đã bấm Show Answer) hay cho edit cả 2
   phía Question/Answer?** — mặc định giả sử cho edit cả 2 phía (đơn giản nhất), nêu ở đây để
   xác nhận lại.
