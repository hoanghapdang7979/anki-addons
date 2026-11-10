# Spec: Tree Card Generator (add-on `tree-card-generator`)

> Spec cho 1 add-on cụ thể trong repo nhiều-add-on `anki-addons` — đặt tại
> `tree-card-generator/SPEC.md`, cùng quy ước với các add-on khác trong repo.

## Objective

Dán 1 đoạn text dạng cây ASCII (dùng ký tự `├──`/`│`/`└──` để thể hiện cấp bậc, mỗi dòng có thể
có tiền tố `[hh:mm:ss]`) vào 1 popup dialog trong Editor của Anki, bấm **Generate** → add-on parse
cây, tạo ra 1 khối HTML **tự chứa** (chỉ dùng inline `style="..."` + `<details>`/`<summary>` thuần
HTML5, **không** `<style>`/`<script>` — xem lý do ở mục "Đổi kiến trúc lúc build" bên dưới) hiển
thị dạng cây có thể bấm mở/thu gọn từng nhánh — và **ghi thẳng vào field đang focus** của note
đang sửa trong Editor (không qua clipboard/paste — xem lý do ở "Đổi kiến trúc lúc build" #2).

### ⚠️ Đổi kiến trúc lúc build (Task 5/6) — quan trọng, đọc trước khi sửa `tree_renderer.py`/`dialog.py`

**Vòng 1 — `<style>`+`<script>` bị strip khi paste.** Spec ban đầu chọn custom JS cho mở/thu gọn
và nhúng CSS trong 1 khối `<style>`. Test thật (user paste thử) phát hiện: Anki/Qt WebEngine strip
bỏ hoàn toàn `<style>` và `<script>` khi paste rich-HTML vào field — `<div>` sống sót nhưng mọi
màu/thụt lề/thu gọn đều mất (dán ra "chỉ văn bản phẳng").

**Vòng 2 — inline `style` + `<details>`/`<summary>` CŨNG bị strip khi paste.** Đổi sang inline
`style="..."` + `<details>`/`<summary>` thuần (không `<script>`, trình duyệt tự xử lý mở/thu gọn).
Tưởng sẽ sống sót qua paste vì không có lý do để strip attribute `style` hay thẻ ngữ nghĩa
`<details>` — **nhưng test thật với đúng HTML source lấy qua Ctrl+Shift+X sau khi paste cho thấy
KHÔNG đúng**: `<details>`/`<summary>` bị bóc hoàn toàn (nội dung bẹt vào parent), và các CSS layout
(`margin`/`padding`/`background`/`cursor`/`border-radius`) cũng bị strip khỏi inline style — chỉ
`color` (dạng `rgb(...)`) và thẻ `<div>`/`<span>` sống sót. Đây là sanitize ở tầng
Chromium/Qt WebEngine paste-into-contenteditable (gọi qua
`self.triggerPageAction(QWebEnginePage.WebAction.Paste)` trong `aqt/editor.py`), **không phải ở
Python** — không sửa được bằng cách đổi HTML/CSS, bất kể thẻ/attribute nào chọn.

**Vòng 3 — bỏ clipboard/paste hoàn toàn, ghi thẳng vào field.** Vì paste-sanitizer strip cả 2
vòng thử trước, không còn cách nào giữ được `<details>`/layout style qua đường paste. Chuyển sang
ghi thẳng vào `note.fields[...]` của note đang mở trong Editor rồi refresh hiển thị — sanitize chỉ
áp dụng lúc paste, không áp dụng cho field content đã có sẵn/được set trực tiếp qua Python. UX đổi:
user phải **click vào field muốn điền TRƯỚC**, rồi bấm nút Tree Card, dán text, bấm Generate — HTML
xuất hiện ngay trong field đó, không cần Ctrl+V. Xem "Tech Stack" và "Code Style" bên dưới cho API
cụ thể (`editor.note`, `editor.last_field_index`, `editor.addMode`,
`aqt.operations.note.update_note`, `editor.loadNote()`).

**Bài học phụ, quan trọng cho lần sau:** venv dev (`tree-card-generator/.venv`) ban đầu cài
`aqt`/`anki` bản mới nhất available lúc đó (`26.9`, mới hơn bản Anki thật user cài, `25.9.4`) —
khiến 2 lần pre-verify "đọc code xác nhận API tồn tại" đều **sai** (`editor.nid`/`reload_note()` là
API của bản 26.9, không tồn tại trong 25.9.4 — traceback thật `AttributeError: 'Editor' object has
no attribute 'nid'`). Từ nay: venv dev phải **pin đúng version Anki thật user đang chạy**
(`requirements.txt`: `aqt==25.9.4`, `anki==25.9.4`), không cài "latest" mặc định — đọc source
trong venv chỉ đáng tin nếu venv cùng version với Anki thật.

**User:** chỉ Dang (cá nhân).

**Input mẫu** (xem tin nhắn `/spec` gốc để có ví dụ đầy đủ):
```
THE 7-11-4 BLUEPRINT & PHÁT TRIỂN BẢN THÂN (DANIEL PRIESTLEY)
│
├── 1. CHUYỂN DỊCH TƯ DUY THỜI ĐẠI (MINDSET SHIFT)
│   ├── [00:03:04] Từ Kỷ nguyên Công nghiệp ➔ Kỷ nguyên Kỹ thuật số (Digital Age)
│   │   ├── Bẫy cũ: ...
│   │   └── Luật chơi mới: ...
│   └── ...
└── 6. NỀN TẢNG PHÁT TRIỂN NỘI TẠI (LIFE & HEALTH FOUNDATIONS)
    └── ...
```

**Output:** dòng đầu tiên = tiêu đề gốc. Mỗi node **có node con** → render thành `<details>` +
`<summary>` (bấm vào `<summary>` để mở/thu gọn — hành vi native của trình duyệt, không cần JS).
Node **không có con** (lá) → render thành 1 dòng bullet đơn giản. Node có tiền tố `[hh:mm:ss]` →
tách riêng phần timestamp hiển thị như 1 nhãn nhỏ trước label.

**Ghi thẳng vào field, không qua clipboard/paste** (xem "Đổi kiến trúc lúc build" vòng 3) — dùng
`editor.note.fields[editor.last_field_index] = html`, persist qua
`aqt.operations.note.update_note(...)` (chỉ khi không phải Add Cards — xem Code Style), rồi
`editor.loadNote(focusTo=...)` để refresh hiển thị. Không dùng API đã `@deprecated`
(`setFormat('inserthtml', ...)`).

**Success = xong khi:** click vào field muốn điền, bấm nút Tree Card, dán đúng mẫu cây, bấm
Generate → HTML xuất hiện thẳng trong field đó (không cần Ctrl+V) → thấy đúng cấu trúc cây, bấm
vào tiêu đề mở/thu gọn được từng nhánh.

## Tech Stack

- Python + PyQt6 (qua `aqt.qt`, re-export chuẩn của Anki) cho dialog — `QDialog` +
  `QPlainTextEdit` (nhập text tree) + `QPushButton` (Generate).
- `aqt.gui_hooks.editor_did_init_buttons` — hook thêm nút vào toolbar Editor, signature
  `(buttons: list[str], editor) -> None`, gọi `editor.addButton(...)`. `__init__.py` truyền chính
  `editor` (không chỉ `editor.parentWindow`) vào `TreeDialog` để dialog truy cập được
  `note`/`last_field_index`/`addMode`/`widget`.
- **Ghi thẳng vào field** (đã verify thật trong Anki 25.9.4, xem "Đổi kiến trúc lúc build" vòng 3):
  `editor.note: Note | None`, `editor.last_field_index: int | None`, `editor.addMode: bool` (true
  trong Add Cards — note chưa có id, chưa lưu vào collection, chỉ tồn tại trong bộ nhớ Editor tới
  khi user bấm "Add"), `aqt.operations.note.update_note(parent=editor.widget,
  note=note).run_in_background(initiator=editor)` (chỉ gọi khi `not editor.addMode` — gọi
  `mw.col.update_note()` trực tiếp trong Add Cards sẽ crash `NotFoundError: No such note: '0'`),
  `editor.loadNote(focusTo=field_index)` để refresh hiển thị (không có `reload_note()` trong
  25.9.4). Tham khảo `Editor._onHtmlEdit()` trong `aqt/editor.py` — logic Ctrl+Shift+X dùng đúng
  pattern này.
- Logic parse + render (`tree_parser.py`, `tree_renderer.py`) hoàn toàn thuần Python, không
  `import aqt` — test bằng `pytest`, không cần Anki thật.
- Venv riêng (`tree-card-generator/.venv`), **pin đúng version Anki thật đang cài**
  (`requirements.txt`: `aqt==25.9.4`, `anki==25.9.4`) — không cài "latest", tránh lặp lại bug
  API-mismatch (`editor.nid`/`reload_note()` chỉ tồn tại ở bản dev mới hơn, không có trong
  25.9.4).

## Commands

```bash
cd tree-card-generator
python -m venv .venv
.venv/Scripts/pip install pytest
.venv/Scripts/pip install -r requirements.txt   # pin đúng version Anki thật (aqt==25.9.4, anki==25.9.4)

# Test — chạy từ trong tests/ (cùng lý do đã ghi ở các add-on khác: tên thư mục có dấu gạch
# ngang khiến pytest's Package-collection vỡ relative import nếu chạy từ repo root)
cd tests
../.venv/Scripts/python -m pytest . -v

# Cài để test thủ công trong Anki thật — Junction (máy không có quyền admin cho symbolic link)
New-Item -ItemType Junction `
  -Path "$env:APPDATA\Anki2\addons21\tree-card-generator" `
  -Target "C:\Users\Client\Desktop\anki-addons\tree-card-generator"
# Restart Anki, test trên profile IFE-Test (đã có sẵn), không dùng profile thật.

# Đóng gói .ankiaddon
cd tree-card-generator
zip -r ../tree-card-generator.ankiaddon . -x "__pycache__/*" "meta.json" "tests/*" ".venv/*"
```

## Project Structure

```
tree-card-generator/
  manifest.json           # name, package "tree-card-generator", mod
  __init__.py               # đăng ký editor_did_init_buttons, mở TreeDialog(editor, ...) khi bấm nút
  dialog.py                  # QDialog UI (PyQt6) — nhập text, bấm Generate, ghi thẳng vào field
                             #   đang focus qua editor.note/last_field_index/addMode.
                             #   Không unit test (UI code) — verify tay trong Anki thật.
  tree_parser.py              # parse_tree(text: str) -> TreeNode — logic thuần
  tree_renderer.py             # render_html(root: TreeNode) -> str — logic thuần, chỉ dùng
                             #   inline style="..." + <details>/<summary>, KHÔNG <style>/<script>
  requirements.txt            # pin aqt/anki đúng version Anki thật đang cài
  tests/
    conftest.py
    test_tree_parser.py
    test_tree_renderer.py
```

## Code Style

```python
from dataclasses import dataclass, field


@dataclass
class TreeNode:
    label: str
    timestamp: str | None = None
    children: list["TreeNode"] = field(default_factory=list)


def parse_tree(text: str) -> TreeNode:
    """Parse ASCII tree text (├──/│/└── connectors, 4-char indent per level)
    into a TreeNode. First non-empty line becomes the root's label.
    """
    ...


def render_html(root: TreeNode) -> str:
    """Render a TreeNode using only inline style="..." attributes and
    native <details>/<summary> (no <style>/<script> - see "Đổi kiến trúc
    lúc build" in Objective) - a node with children becomes a
    <details>/<summary> pair, a leaf node becomes a plain bullet.
    """
    ...
```

- **Depth = độ dài phần prefix trước `├──`/`└──` chia 4, cộng 1** (mỗi cấp thụt lề đúng 4 ký tự:
  `"│   "` hoặc `"    "` cho cấp cha còn/hết sibling, cộng thêm 4 ký tự của chính marker
  `"├── "`/`"└── "`). Dòng chỉ chứa `"│"` (dòng trống ngăn cách) → bỏ qua, không tạo node.
- **Escape HTML entities** trong mọi label trước khi nhúng vào output (`html.escape()`) — tránh
  vỡ markup hoặc XSS nếu text tree chứa `<`, `>`, `&`.
- **Tách timestamp**: label bắt đầu bằng `[hh:mm:ss] ` (regex `^\[\d{2}:\d{2}:\d{2}\]\s*`) → tách
  ra `TreeNode.timestamp`, phần còn lại là `label`.
- `dialog.py` là nơi duy nhất chạm `aqt`/PyQt — `tree_parser.py`/`tree_renderer.py` không import
  gì từ `aqt`.

## Testing Strategy

- **Unit test** (`pytest`, không cần Anki thật):
  - `parse_tree()`: cây 1 cấp, cây nhiều cấp lồng nhau, dòng trống `"│"` bị bỏ qua đúng, node
    cuối dùng `└──` vs node giữa dùng `├──` cho ra cùng cấu trúc cha-con đúng, tách timestamp
    `[00:03:04]` đúng, label không có timestamp giữ nguyên, label chứa `<`/`&` được giữ nguyên ở
    bước parse (escape làm ở bước render, không phải parse).
  - `render_html()`: node có con → render thành `<details>`/`<summary>` (mặc định thu gọn — không
    có attribute `open`, hành vi native, không cần class/JS riêng); node lá → render bullet,
    không có `<details>`; label chứa `<script>` hay `&` → escape đúng trong output; output
    **không chứa** `<style>`/`<script>`/`onclick` nào — chỉ inline `style="..."`.
- **Không unit test `dialog.py`** (UI code, cần Qt event loop) — verify tay: mở Anki, click vào
  field muốn điền, bấm nút, dán text mẫu, bấm Generate, xác nhận HTML xuất hiện thẳng trong field
  đó (không cần Ctrl+V) + click mở/đóng đúng. Yêu cầu bằng chứng cụ thể khi verify (HTML source
  qua Ctrl+Shift+X hoặc screenshot), không chỉ câu trả lời "đúng/sai" — bài học từ 1 lần user xác
  nhận nhầm giữa 2 vòng đổi kiến trúc (xem tasks/plan.md Task 5).

## Boundaries

- **Luôn làm:**
  - Escape HTML entities trong mọi label trước khi render — không bao giờ nhúng text thô của
    user thẳng vào HTML output.
  - HTML output phải tự chứa hoàn toàn bằng inline `style="..."` + `<details>`/`<summary>` —
    **không** dùng `<style>`/`<script>` (bị Anki strip khi paste — vẫn giữ giới hạn này dù không
    còn qua paste nữa, để không phụ thuộc setup Card Template riêng của note type).
  - Ghi vào field đang focus qua `editor.note.fields[...]` + persist đúng theo `editor.addMode`
    (xem Tech Stack) — không gọi `mw.col.update_note()` trực tiếp vô điều kiện (crash trong Add
    Cards vì note chưa có id).
  - Venv dev pin đúng version `aqt`/`anki` với Anki thật user đang cài (`requirements.txt`).
- **Hỏi trước:**
  - Đổi cú pháp tree input hỗ trợ (ngoài `├──`/`│`/`└──` với thụt lề 4 ký tự) — vd hỗ trợ tab
    thay vì space, hoặc ký tự khác.
  - Thêm preview trực tiếp trong dialog trước khi ghi vào field (ngoài scope v1, đã chốt ở
    `/spec`).
  - Quay lại cơ chế clipboard/paste (đã bỏ ở vòng 3) nếu sau này có lý do mới.
- **Không bao giờ:**
  - Dựa vào API Editor đã đánh dấu `@deprecated` (`setFormat`, `inserthtml`, các hàm trong mục
    "Legacy editing routines" của `aqt/editor.py`) để chèn field.
  - Tự ý đọc/sửa field khác ngoài field mà user đã click vào trước khi bấm nút Tree Card.
  - Nhúng JS/CSS phụ thuộc thư viện ngoài (CDN, npm package) — giữ tự chứa 100%, không cần
    internet để hiển thị đúng.
  - Dùng `<style>` hoặc `<script>` dưới bất kỳ hình thức nào trong `render_html()`.
  - Cài "latest" `aqt`/`anki` vào venv dev mà không kiểm tra version Anki thật user đang chạy.

## Success Criteria

- Click vào field muốn điền, dán đúng mẫu cây (6 section cấp 1, có cấp 2 với timestamp, cấp 3 là
  bullet lá), bấm Generate → HTML xuất hiện thẳng trong field đó, đúng cấu trúc lồng nhau khớp
  input — không cần Ctrl+V.
- Bấm vào tiêu đề section (cấp có con) → mở/thu gọn đúng nhánh đó, không ảnh hưởng nhánh khác
  (đã xác nhận thật qua HTML source Ctrl+Shift+X — `open=""` phản ánh đúng trạng thái đã bấm).
- Label chứa ký tự đặc biệt (`<`, `&`, `"`) không làm vỡ layout/markup.
- Hoạt động đúng cả trong Add Cards (note chưa có id) và khi sửa note đã tồn tại (Browse) — không
  crash `NotFoundError`.
- `pytest tree-card-generator/tests` (chạy đúng cách — xem Commands) pass 100%.

## Open Questions

1. **Trạng thái mặc định lúc mới dán** — giả định các section **thu gọn hết** (collapsed), đúng
   tinh thần "bấm để mở từng nhánh" trong tên gọi ban đầu bạn mô tả. Xác nhận lại nếu muốn mặc
   định mở sẵn (expanded) thay vì thu gọn.
2. **Tên add-on tạm `tree-card-generator`** — đổi tên khác nếu muốn.
3. ~~`QMimeData.setHtml()` + paste vào Anki Editor~~ — **đã bỏ hoàn toàn** (xem "Đổi kiến trúc lúc
   build" vòng 1-3). Đã chốt: ghi thẳng vào field, không qua clipboard/paste.
