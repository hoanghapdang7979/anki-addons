# Spec: Habit Checklist (add-on `habit-checklist`)

> Spec cho 1 add-on cụ thể trong repo nhiều-add-on `anki-addons` — đặt tại
> `habit-checklist/SPEC.md`, cùng quy ước với [auto-date-field/SPEC.md](../auto-date-field/SPEC.md)
> và [inline-field-editor/SPEC.md](../inline-field-editor/SPEC.md).

## Objective

Tự động điền danh sách habit (đọc từ `config.json`) vào 1 field chỉ định của note type
**Diary** (đã có sẵn, không phải add-on tự tạo), ngay khi note mới được tạo — mỗi habit là 1
dòng dạng `[ ] Tên habit`, để tick hoàn thành bằng cách tự gõ đè `[ ]` → `[x]` ngay trong Editor
bình thường của Anki, và có thể gõ thêm ghi chú tự do ngay sau tên habit trên cùng dòng (vd
`[x] Exercise — chạy 30 phút`).

**User:** chỉ Dang (cá nhân), dùng cho note Diary hàng ngày của mình.

**Trigger:** khi note mới được tạo qua **Add Cards** — giống hệt cơ chế của
`auto-date-field` (hook `add_cards_did_add_note`), không có phím tắt/nút insert thủ công ở
scope này.

**Không có checkbox thật/JS:** tick = tự gõ đè ký tự `[ ]` thành `[x]` trong Editor có sẵn của
Anki. Add-on không can thiệp gì vào việc tick hay ghi chú — chỉ điền checklist ban đầu lúc note
còn trống.

**Field áp dụng:** tên field cố định đọc từ `config.json` (mặc định `"Habits"`) — note type nào
có field trùng tên đó thì tự điền, không có thì bỏ qua im lặng.

**Không ghi đè:** chỉ điền nếu field đang **trống** — giống hệt nguyên tắc của
`auto-date-field`. Field đã có nội dung (kể cả do chính add-on điền từ trước rồi user đã
tick/ghi chú) thì **không bao giờ** đụng vào lại — nếu parse lại và "re-render" sẽ xoá mất tick
+ ghi chú user đã nhập, đây là rủi ro mất dữ liệu cần tránh tuyệt đối.

**Success = xong khi:** thêm 1 note Diary mới có field `"Habits"` trống → sau khi Add, field
chứa đúng danh sách checklist theo thứ tự trong config, mỗi habit 1 dòng dạng `[ ] Tên habit`.

## Tech Stack

- Python thuần + `aqt.gui_hooks.add_cards_did_add_note` — **giống hệt kiến trúc
  `auto-date-field`** (đã verify hook này hoạt động đúng ở add-on đó), không cần JS/webview vì
  tick UX chọn là text thuần.
- `config.json` cho `field_name` + danh sách `habits` — dùng UI Config JSON có sẵn của Anki.
- `pytest` cho phần logic thuần.
- **Không dùng lại code từ `auto-date-field`/`inline-field-editor`** — mỗi add-on tự chứa
  (CLAUDE.md: "không rò rỉ code dùng chung giữa các add-on trừ khi tách `shared/`", chưa cần ở
  quy mô hiện tại dù logic "chỉ điền khi field trống" có lặp lại 1 lần nữa — 3 dòng lặp lại còn
  tốt hơn abstraction sớm).

## Commands

```bash
# Setup venv riêng
cd habit-checklist
python -m venv .venv
.venv/Scripts/pip install pytest aqt

# Test — chạy từ trong tests/ (cùng lý do đã ghi ở 2 add-on trước: tên thư mục có dấu gạch
# ngang khiến pytest's Package-collection vỡ relative import nếu chạy "pytest habit-checklist/tests" từ root)
cd habit-checklist/tests
../.venv/Scripts/python -m pytest . -v

# Cài để test thủ công trong Anki thật (Windows) — Junction, không cần quyền admin
New-Item -ItemType Junction `
  -Path "$env:APPDATA\Anki2\addons21\habit-checklist" `
  -Target "C:\Users\Client\Desktop\anki-addons\habit-checklist"
# Restart Anki. Test trên profile IFE-Test (đã có sẵn), không dùng profile thật.

# Đóng gói .ankiaddon
cd habit-checklist
zip -r ../habit-checklist.ankiaddon . -x "__pycache__/*" "meta.json" "tests/*" ".venv/*"
```

## Project Structure

```
habit-checklist/
  manifest.json          # name, package "habit-checklist", mod
  __init__.py              # đăng ký add_cards_did_add_note, đọc config, gọi checklist.py
  checklist.py              # logic thuần: build_habit_checklist(), apply_checklist_if_empty()
  config.json                # default: {"field_name": "Habits", "habits": []}
  config.md                   # mô tả field_name + habits cho UI Config của Anki
  tests/
    conftest.py                # sys.path insert (giống 2 add-on trước)
    test_checklist.py           # test build_habit_checklist() + apply_checklist_if_empty()
```

## Code Style

```python
def build_habit_checklist(habits: list[str]) -> str:
    """Render habits as one "[ ] Name" line per habit, joined by <br>.

    Anki fields are HTML, so <br> (not "\\n") is what actually produces
    separate lines in the Editor/Reviewer.
    """
    return "<br>".join(f"[ ] {habit}" for habit in habits)


def apply_checklist_if_empty(note, field_name: str, checklist_text: str) -> bool:
    """Set note[field_name] = checklist_text if the field exists and is empty.

    Same contract as auto-date-field's apply_date_if_empty (whitespace-only
    counts as empty). Never re-renders over existing content - that would
    wipe out ticks and per-habit notes the user already wrote.
    """
    if field_name not in note:
        return False
    if note[field_name].strip():
        return False
    note[field_name] = checklist_text
    return True
```

- `checklist.py` không `import aqt`/`anki` — `note` là dict-like (duck typing), test bằng
  `dict` thường.
- `__init__.py` là nơi duy nhất chạm `aqt`/`anki` — đọc config, gọi `checklist.py`, và
  `mw.col.update_note(note)` nếu có thay đổi (note đã được Anki lưu *trước khi* hook
  `add_cards_did_add_note` chạy). Import `anki.collection` trước `anki.notes`/`anki.hooks` để
  tránh circular import đã gặp ở 2 add-on trước (xem `auto-date-field/__init__.py`).
- Không `print()` — dùng `logging`.

## Testing Strategy

- **Unit test** (`pytest`, không cần Anki thật):
  - `build_habit_checklist([])` → chuỗi rỗng.
  - `build_habit_checklist(["Exercise"])` → `"[ ] Exercise"`.
  - `build_habit_checklist(["Exercise", "Read"])` → `"[ ] Exercise<br>[ ] Read"` (đúng thứ tự).
  - `apply_checklist_if_empty()`: field trống/chỉ khoảng trắng → set + True; field có nội dung
    thật → không đổi + False; field không tồn tại → không đổi + False.
- **Manual verify trong Anki thật** (bắt buộc, profile test — không dùng profile thật):
  - Note Diary mới, field `"Habits"` trống → sau Add, field đúng checklist theo config.
  - Note Diary mới, field `"Habits"` đã nhập sẵn nội dung (giả lập note cũ đã tick) → giữ
    nguyên sau Add, không bị ghi đè.
  - Note type khác không có field `"Habits"` → Add bình thường, không lỗi.
  - Tự tay sửa `[ ]` → `[x]` + gõ thêm note ngay trong Editor, lưu lại, mở lại note vẫn giữ
    đúng nội dung đã sửa (xác nhận add-on không đụng lại field này sau khi note đã tồn tại).

## Boundaries

- **Luôn làm:**
  - Chỉ điền field khi đang trống (kể cả khoảng trắng thuần) — không bao giờ ghi đè/re-render
    nội dung đã có, dù chỉ 1 phần đã bị user sửa.
  - Note type không có field trùng tên config → bỏ qua im lặng, không crash Add Cards.
- **Hỏi trước:**
  - Đổi tick UX sang checkbox thật/JS (đã cân nhắc và chọn text đơn giản ở bước `/spec` — đổi
    sau này là thay đổi kiến trúc, cần bàn lại).
  - Thêm tính năng tính % hoàn thành / parse ngược nội dung field để thống kê (ngoài scope hiện
    tại, và đọc lại field đã có nội dung đi ngược nguyên tắc "không đụng field đã điền").
  - Đổi default `field_name`/`habits` trong `config.json` sau khi user đã dùng thật.
- **Không bao giờ:**
  - Parse lại nội dung field **đã có** để "re-render" danh sách mới — sẽ xoá mất tick + ghi chú
    user đã nhập, đây là rủi ro mất dữ liệu tuyệt đối không được phép.
  - Tự động sửa note **đã tồn tại từ trước** ngoài đường hook `add_cards_did_add_note` lúc note
    vừa tạo.
  - Đọc/ghi trực tiếp `.anki2`/`collection.media` ngoài qua Collection API (hard-stop chung).
  - Cài/symlink vào `addons21/` hoặc test trên profile có dữ liệu thật mà chưa xác nhận.

## Success Criteria

- Note Diary mới, field `"Habits"` trống → sau Add, field = `"[ ] Habit1<br>[ ] Habit2<br>..."`
  đúng thứ tự trong config.
- Field đã có nội dung khác → giữ nguyên sau Add, không bị ghi đè.
- Note type không có field `"Habits"` → Add bình thường, không lỗi/crash.
- `pytest habit-checklist/tests` (chạy đúng cách — xem Commands) pass 100%.

## Open Questions

1. **Tên field mặc định `"Habits"`** — xác nhận đúng tên field bạn đã tạo trong note type
   Diary, hay tên khác (vd `"HabitList"`, `"Checklist"`...).
2. **Danh sách habit mặc định trong `config.json`** — để `[]` rỗng cho user tự điền qua Config
   dialog, hay điền sẵn vài ví dụ mẫu (vd `["Exercise", "Read", "Meditate"]`) để dễ hình dung
   cách sửa? Mặc định spec này chọn để trống `[]` — sửa lại nếu muốn có sẵn ví dụ.
3. **Cả `auto-date-field` và `habit-checklist` cùng hook vào `add_cards_did_add_note`** — không
   xung đột vì mỗi add-on chỉ đụng field riêng của mình (`Date` vs `Habits`), Anki gọi lần lượt
   từng callback đã đăng ký. Nêu ở đây để xác nhận không có note type nào dùng field `"Habits"`
   cho mục đích khác đã có từ trước.
