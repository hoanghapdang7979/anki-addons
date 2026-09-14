# Spec: Tree Card Generator (add-on `tree-card-generator`)

> Spec cho 1 add-on cụ thể trong repo nhiều-add-on `anki-addons` — đặt tại
> `tree-card-generator/SPEC.md`, cùng quy ước với các add-on khác trong repo.

## Objective

Dán 1 đoạn text dạng cây ASCII (dùng ký tự `├──`/`│`/`└──` để thể hiện cấp bậc, mỗi dòng có thể
có tiền tố `[hh:mm:ss]`) vào 1 popup dialog trong Editor của Anki, bấm **Generate** → add-on parse
cây và tạo ra 1 khối HTML **tự chứa** (chỉ dùng inline `style="..."` + `<details>`/`<summary>`
thuần HTML5, **không** `<style>`/`<script>` — xem lý do ở mục "Đổi kiến trúc lúc build" bên dưới)
hiển thị dạng cây có thể bấm mở/thu gọn từng nhánh — copy thẳng vào clipboard (dạng rich HTML),
user tự `Ctrl+V` dán vào field bất kỳ của note đang sửa.

### ⚠️ Đổi kiến trúc lúc build (Task 5/6) — quan trọng, đọc trước khi sửa `tree_renderer.py`

Spec ban đầu chọn **custom JS** cho việc mở/thu gọn (xem lịch sử hỏi ở `/spec`) và nhúng CSS
trong 1 khối `<style>`. Test thật trong Anki (user paste thử) phát hiện: **Anki/Qt WebEngine
strip bỏ hoàn toàn `<style>` và `<script>` khi paste rich-HTML vào field** — cấu trúc `<div>`
sống sót nhưng mọi màu sắc/thụt lề/hành vi thu gọn đều mất, y hệt hiện tượng user báo cáo (dán
ra "chỉvăn bản phẳng"). Đây là giới hạn thật của cơ chế paste, không phải bug sửa được bằng cách
viết CSS/JS khác đi.

**Đã đổi sang:** inline `style="..."` trên từng thẻ (không có khối `<style>` nào cả) + native
`<details>`/`<summary>` HTML5 cho mở/thu gọn (không cần `<script>` nào cả — trình duyệt tự xử lý,
mặc định thu gọn khi không có attribute `open`). Cả 2 thứ này **sống sót qua paste** vì paste-
sanitizer không có lý do để strip attribute `style` hay thẻ ngữ nghĩa `<details>`. Mục "Code Style"
và "Testing Strategy" bên dưới đã cập nhật theo kiến trúc mới này.

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

**Không tự động chèn vào field** — ban đầu định làm thế nhưng phát hiện cơ chế chèn HTML vào
field đang focus của Editor dựa trên API đã bị đánh dấu **deprecated**
(`setFormat('inserthtml', ...)` chỉ còn trong `aqt/editor_legacy.py`, Anki hiện tại dùng
`NewEditor` viết lại bằng Svelte không có API tương đương lộ ra ngoài). Thay vào đó: **copy HTML
vào clipboard** (dùng `QMimeData.setHtml()`, không phải plain text) — Anki xử lý paste rich-HTML
từ clipboard theo cơ chế chuẩn của Qt, không phụ thuộc phiên bản editor nội bộ, bền hơn nhiều.

**Success = xong khi:** dán đúng mẫu cây → bấm Generate → clipboard chứa HTML → dán (Ctrl+V) vào
1 field bất kỳ trong Anki → thấy đúng cấu trúc cây, bấm vào tiêu đề mở/thu gọn được từng nhánh.

## Tech Stack

- Python + PyQt6 (qua `aqt.qt`, re-export chuẩn của Anki) cho dialog — `QDialog` +
  `QPlainTextEdit` (nhập text tree) + `QPushButton` (Generate & Copy).
- `aqt.gui_hooks.editor_did_init_buttons` — hook thêm nút vào toolbar Editor (đã verify tồn tại
  trong `aqt` 26.8.1, signature `(buttons: list[str], editor) -> None`, gọi
  `editor.addButton(...)`).
- Copy vào clipboard qua `QMimeData.setHtml()` + `QApplication.clipboard().setMimeData()` —
  **chưa verify thật trong Anki** (chỉ verify hook tồn tại), cần test tay ở task đầu tiên của
  plan trước khi code phần còn lại.
- Logic parse + render (`tree_parser.py`, `tree_renderer.py`) hoàn toàn thuần Python, không
  `import aqt` — test bằng `pytest`, không cần Anki thật.
- Venv riêng (`tree-card-generator/.venv`), không dùng chung với add-on khác trong repo.

## Commands

```bash
cd tree-card-generator
python -m venv .venv
.venv/Scripts/pip install pytest aqt

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
  __init__.py               # đăng ký editor_did_init_buttons, mở TreeDialog khi bấm nút
  dialog.py                  # QDialog UI (PyQt6) — nhập text, bấm Generate, copy clipboard.
                             #   Không unit test (UI code) — verify tay trong Anki thật.
  tree_parser.py              # parse_tree(text: str) -> TreeNode — logic thuần
  tree_renderer.py             # render_html(root: TreeNode) -> str — logic thuần, chỉ dùng
                             #   inline style="..." + <details>/<summary>, KHÔNG <style>/<script>
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
- **Không unit test `dialog.py`** (UI code, cần Qt event loop) — verify tay: mở Anki, bấm nút,
  dán text mẫu, bấm Generate, dán (Ctrl+V) vào 1 field, xác nhận hiển thị + click mở/đóng đúng.

## Boundaries

- **Luôn làm:**
  - Escape HTML entities trong mọi label trước khi render — không bao giờ nhúng text thô của
    user thẳng vào HTML output.
  - HTML output phải tự chứa hoàn toàn bằng inline `style="..."` + `<details>`/`<summary>` —
    **không** dùng `<style>`/`<script>` (bị Anki strip khi paste, xem "Đổi kiến trúc lúc build")
    — dán được vào field của bất kỳ note type nào mà không cần setup Card Template riêng.
  - Copy vào clipboard dạng rich-HTML (`QMimeData.setHtml()`), không phải plain text escaped —
    nếu không, dán vào Anki sẽ ra text thô `<div>...` thay vì render đẹp.
- **Hỏi trước:**
  - Đổi cú pháp tree input hỗ trợ (ngoài `├──`/`│`/`└──` với thụt lề 4 ký tự) — vd hỗ trợ tab
    thay vì space, hoặc ký tự khác.
  - Thêm preview trực tiếp trong dialog trước khi copy (ngoài scope v1, đã chốt ở `/spec`).
  - Đổi lại sang cơ chế tự động chèn vào field (bỏ clipboard) nếu sau này tìm được API ổn định
    hơn cho `NewEditor`.
- **Không bao giờ:**
  - Dựa vào API Editor đã đánh dấu `@deprecated` (`setFormat`, `inserthtml`, các hàm trong
    `editor_legacy.py`) để tự động chèn field.
  - Tự ý đọc/sửa note hiện tại trong Editor ngoài việc user tự dán bằng tay.
  - Nhúng JS/CSS phụ thuộc thư viện ngoài (CDN, npm package) — giữ tự chứa 100%, không cần
    internet để hiển thị đúng.
  - Dùng `<style>` hoặc `<script>` dưới bất kỳ hình thức nào trong `render_html()` — đã xác nhận
    thật (không phải giả định) là bị Anki strip khi paste, xem "Đổi kiến trúc lúc build".

## Success Criteria

- Dán đúng mẫu cây (6 section cấp 1, có cấp 2 với timestamp, cấp 3 là bullet lá) → bấm Generate
  → clipboard chứa HTML đúng cấu trúc lồng nhau khớp input.
- Dán (Ctrl+V) HTML đó vào 1 field bất kỳ trong Anki (Editor Add/Browse) → hiển thị đúng cấu
  trúc cây, không phải text thô có escape `<div>`.
- Bấm vào tiêu đề section (cấp có con) → mở/thu gọn đúng nhánh đó, không ảnh hưởng nhánh khác.
- Label chứa ký tự đặc biệt (`<`, `&`, `"`) không làm vỡ layout/markup.
- `pytest tree-card-generator/tests` (chạy đúng cách — xem Commands) pass 100%.

## Open Questions

1. **Trạng thái mặc định lúc mới dán** — giả định các section **thu gọn hết** (collapsed), đúng
   tinh thần "bấm để mở từng nhánh" trong tên gọi ban đầu bạn mô tả. Xác nhận lại nếu muốn mặc
   định mở sẵn (expanded) thay vì thu gọn.
2. **Tên add-on tạm `tree-card-generator`** — đổi tên khác nếu muốn.
3. **`QMimeData.setHtml()` + paste vào Anki Editor** — API chuẩn PyQt6, nhiều khả năng hoạt động
   đúng, nhưng chưa test thật trong Anki. Cần verify ở task đầu tiên của `/planning` trước khi
   code phần dialog/renderer, đúng nguyên tắc không giả định API chưa kiểm chứng.
