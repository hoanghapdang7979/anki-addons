# Spec: Auto Date Field (add-on `auto-date-field`)

> Spec cho 1 add-on cụ thể trong repo nhiều-add-on `anki-addons` — đặt tại
> `auto-date-field/SPEC.md`, cùng quy ước với [inline-field-editor/SPEC.md](../inline-field-editor/SPEC.md)
> (xem [CLAUDE.md](../CLAUDE.md) mục "mỗi add-on 1 folder riêng").

## Objective

Tự động điền ngày hiện tại (định dạng ISO `yyyy-mm-dd`) vào 1 field chỉ định của note, ngay khi
note được tạo — không cần gõ tay ngày mỗi lần thêm note mới (vd để track "ngày học từ này",
"ngày thêm card").

**User:** chỉ Dang (cá nhân), dùng cho deck của mình.

**Trigger:** khi note mới được tạo qua màn hình **Add** (Add Cards dialog) — không áp dụng cho
note đã tồn tại từ trước (không có tính năng backfill hàng loạt ở scope này).

**Field áp dụng:** tên field cố định đọc từ `config.json` (mặc định `"Date"`) — note type nào có
field trùng tên đó thì tự điền, note type không có field đó thì bỏ qua im lặng (không lỗi).

**Không ghi đè:** chỉ điền nếu field đang **trống**. Note tạo từ import/sync mà field đã có sẵn
nội dung thì giữ nguyên, không đụng vào.

**Success = xong khi:** thêm 1 note mới có field `"Date"` (hoặc tên đã cấu hình) → field đó tự
động chứa ngày hôm nay dạng `yyyy-mm-dd` ngay sau khi bấm Add, không cần thao tác gì thêm.

## Tech Stack

- Python thuần + `aqt.gui_hooks` (không cần JS/webview — khác với `inline-field-editor`, add-on
  này không tương tác với reviewer, chỉ hook vào sự kiện "note added").
- `config.json` cho field name — dùng UI Config JSON có sẵn của Anki (Tools → Add-ons → Config),
  không tự dựng dialog cấu hình riêng (Rule 0 Simplicity First — Anki đã có sẵn UI này).
- `pytest` cho phần logic thuần.

## Commands

```bash
# Setup venv riêng (giống inline-field-editor, không dùng chung venv giữa 2 add-on)
cd auto-date-field
python -m venv .venv
.venv/Scripts/pip install pytest

# Test — PHẢI chạy với cwd bên trong tests/, không phải "pytest auto-date-field/tests" từ repo
# root (cùng lý do đã ghi trong inline-field-editor/SPEC.md: tên thư mục add-on có dấu gạch
# ngang, pytest's Package-collection sẽ cố import __init__.py và vỡ relative import).
cd auto-date-field/tests
../.venv/Scripts/python -m pytest . -v

# Cài để test thủ công trong Anki thật (Windows) — dùng Junction, máy không có quyền admin để
# tạo symbolic link (xem inline-field-editor/SPEC.md để biết lý do)
New-Item -ItemType Junction `
  -Path "$env:APPDATA\Anki2\addons21\auto-date-field" `
  -Target "C:\Users\Client\Desktop\anki-addons\auto-date-field"
# Restart Anki sau khi tạo junction. addons21/ dùng chung mọi profile — test trên profile
# IFE-Test (đã có sẵn từ add-on trước) hoặc tạo profile test riêng nếu muốn tách biệt.

# Đóng gói .ankiaddon
cd auto-date-field
zip -r ../auto-date-field.ankiaddon . -x "__pycache__/*" "meta.json" "tests/*" ".venv/*"
```

## Project Structure

```
auto-date-field/
  manifest.json          # name, package "auto-date-field", mod
  __init__.py              # đăng ký gui_hooks.add_cards_did_add_note, đọc config, gọi date_fill
  date_fill.py              # logic thuần: today_iso(), apply_date_if_empty() — không import aqt
  config.json                # default: {"field_name": "Date"}
  config.md                   # mô tả field_name cho UI Config của Anki
  tests/
    conftest.py                # sys.path insert (giống inline-field-editor)
    test_date_fill.py           # test today_iso() + apply_date_if_empty()
```

## Code Style

```python
from datetime import date


def today_iso(today: date | None = None) -> str:
    """Return today's date as YYYY-MM-DD. Pass `today` explicitly in tests."""
    return (today or date.today()).isoformat()


def apply_date_if_empty(note, field_name: str, date_str: str) -> bool:
    """Set note[field_name] = date_str if the field exists and is empty.

    Returns True if the note was changed (caller must persist it), False
    otherwise. `note` only needs dict-like __contains__/__getitem__/
    __setitem__ - works with anki.notes.Note or a plain dict in tests.
    """
    if field_name not in note:
        return False
    if note[field_name].strip():
        return False
    note[field_name] = date_str
    return True
```

- `date_fill.py` không `import aqt`/`anki` — nhận `note` như một dict-like object (duck typing),
  test bằng `dict` thường, không cần mock `anki.notes.Note`.
- `__init__.py` là nơi duy nhất chạm `aqt`: đọc `mw.addonManager.getConfig(__name__)`, gọi
  `date_fill.apply_date_if_empty`, và nếu có thay đổi thì `mw.col.update_note(note)` (note đã
  được Anki lưu vào DB *trước khi* hook `add_cards_did_add_note` chạy, nên phải tự
  `update_note` lại để field mới được ghi xuống — không tự động lưu).
- Không `print()` — dùng `logging`.

## Testing Strategy

- **Unit test** (`pytest`, không cần Anki thật): `today_iso()` với `today` truyền vào tường
  minh (không phụ thuộc đồng hồ hệ thống lúc test); `apply_date_if_empty()` với field trống/có
  sẵn nội dung/field không tồn tại trong note — dùng `dict` giả lập note.
- **Manual verify trong Anki thật** (bắt buộc trước khi coi task xong): thêm note mới có field
  `"Date"` trống → field tự điền đúng ngày hôm nay sau khi Add; note có field `"Date"` đã có sẵn
  nội dung (nhập tay trước khi Add) → giữ nguyên, không bị ghi đè; note type không có field
  `"Date"` → Add bình thường, không lỗi/crash.

## Boundaries

- **Luôn làm:**
  - Chỉ điền field khi đang trống — không bao giờ ghi đè nội dung đã có (kể cả khoảng trắng
    thuần cũng tính là "trống" sau `.strip()`).
  - Note type không có field trùng tên config → bỏ qua im lặng, không raise lỗi làm crash Add
    Cards dialog của user.
- **Hỏi trước:**
  - Thêm tính năng backfill ngày cho note **đã tồn tại từ trước** (ngoài scope hiện tại — chỉ
    note mới tạo từ nay trở đi).
  - Đổi default field name trong `config.json` sau khi user đã bắt đầu dùng thật (đổi default
    không ảnh hưởng note cũ, nhưng có thể gây nhầm nếu user không biết).
- **Không bao giờ:**
  - Tự động sửa field ở note **đã tồn tại** ngoài đường hook `add_cards_did_add_note` (không
    quét toàn bộ collection để "điền bù" ngày cho note cũ).
  - Đọc/ghi trực tiếp `.anki2`/`collection.media` ngoài qua Collection API chính thức (đúng
    hard-stop trong `autopilot.md`).
  - Cài/symlink vào `addons21/` thật hoặc chạy trên profile có dữ liệu thật mà chưa xác nhận —
    dùng profile test (`IFE-Test` hoặc tương đương).

## Success Criteria

- Thêm note mới (note type có field `"Date"`, đang trống) qua Add Cards → sau khi bấm Add, mở
  Browse tìm lại note đó thấy field `"Date"` = ngày hôm nay dạng `2026-09-03`.
- Note có field `"Date"` đã nhập sẵn nội dung khác trước khi Add → giữ nguyên sau khi Add, không
  bị ghi đè.
- Note type không có field `"Date"` → Add Cards hoạt động bình thường, không lỗi/crash, không có
  gì bị điền.
- `pytest auto-date-field/tests` (chạy đúng cách — xem Commands) pass 100%.

## Open Questions

1. **Tên field mặc định `"Date"`** — xác nhận lại tên này có đúng field bạn định dùng không
   (hay tên khác như `"DateAdded"`, `"Ngày"`...). Đổi trong `config.json` sau khi cài cũng được,
   không cần chốt cứng ngay bây giờ.
2. **Xung đột add-on khác** — không phát hiện add-on nào đã cài (Review Heatmap, AnkiConnect,
   Edit Field During Review gốc — mã 1020366288) có hook vào `add_cards_did_add_note` hay field
   name `"Date"` cụ thể, nhưng chưa verify 100%. Nếu user có note type nào đã dùng field tên
   `"Date"` cho mục đích khác, cần xác nhận trước khi bật add-on cho note type đó.
