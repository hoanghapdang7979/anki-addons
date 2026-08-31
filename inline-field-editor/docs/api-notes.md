# API notes — verified against `aqt`/`anki` 26.8.1

> Nguồn: package `aqt`/`anki` cài thật vào `.venv/` (`pip show aqt` → `Version: 26.8.1`), đọc
> trực tiếp source trong `.venv/Lib/site-packages/`. Không dựa vào trí nhớ training data — trả
> lời dứt điểm 3 Open Question trong [SPEC.md](../SPEC.md), theo yêu cầu Task 2 trong
> [tasks/plan.md](../tasks/plan.md).

## (a) Lưu note: `Collection.update_note()`

Xác nhận: **không phải** `note.flush()` (API cũ đã bỏ) — dùng
`Collection.update_note(note, skip_undo_entry=False) -> OpChanges`.

`.venv/Lib/site-packages/anki/collection.py:514-516`:

```python
def update_note(self, note: Note, skip_undo_entry: bool = False) -> OpChanges:
    """Save note changes to database."""
    return self.update_notes([note], skip_undo_entry=skip_undo_entry)
```

Lấy note theo id: `Collection.get_note(id: NoteId) -> Note` — `anki/collection.py:503-504`.
Set field: `note["FieldName"] = new_html` (Note hỗ trợ dict-like access, field name phải khớp
đúng tên field của note type).

→ Flow lưu trong `editor_hook.py`: `note = mw.col.get_note(note_id)`;
`note[field_name] = new_html`; `mw.col.update_note(note)`.

## (b) Field filter cho cú pháp `{{edit:Field}}`

Xác nhận: cơ chế **field filter** vẫn hoạt động đúng như spec giả định — đăng ký qua
`anki.hooks.field_filter`.

Đăng ký (`.venv/Lib/site-packages/anki/hooks.py`, docstring ở đầu module xử lý field filter):

```python
from anki import hooks
hooks.field_filter.append(myfunc)
```

Callback signature — `.venv/Lib/site-packages/anki/hooks_gen.py:224-238`
(`class _FieldFilterFilter`, instance `field_filter = _FieldFilterFilter()` tại dòng 241):

```python
def __call__(
    self,
    field_text: str,
    field_name: str,
    filter_name: str,
    ctx: anki.template.TemplateRenderContext,
) -> str: ...
```

Được gọi từ `.venv/Lib/site-packages/anki/template.py:328-331`, lặp qua từng filter trong
`node.filters` (list[str], `template.py:52`) của mỗi field node trong template:

```python
for filter_name in node.filters:
    field_text = hooks.field_filter(field_text, node.field_name, filter_name, ctx)
```

→ Với `{{edit:Front}}`: `field_name="Front"`, `filter_name="edit"`. Callback của add-on nhận
`field_text` = nội dung field gốc (đã render), trả về HTML mới (span wrapper) nếu
`filter_name == "edit"`, nếu không thì trả về `field_text` không đổi (để không đụng field
filter khác nếu có nhiều filter chồng nhau, vd `{{edit:cloze:Front}}` — ngoài scope hiện tại
nhưng cần trả nguyên vẹn nếu `filter_name != "edit"`).

## (c) Inject JS/CSS vào reviewer webview + nhận message ngược từ JS

Xác nhận: cả 2 hook đều tồn tại và đúng như spec giả định, định nghĩa thật ở
`.venv/Lib/site-packages/_aqt/hooks.py` (re-export qua `aqt/gui_hooks.py` →
`from _aqt.hooks import *`).

**Inject CSS/JS** — `webview_will_set_content` (`_aqt/hooks.py:5736-5797`), docstring có sẵn ví
dụ dùng đúng cho reviewer:

```python
def on_webview_will_set_content(web_content: WebContent, context):
    if not isinstance(context, aqt.reviewer.Reviewer):
        return  # chỉ áp dụng cho màn hình review
    addon_package = mw.addonManager.addonFromModule(__name__)
    web_content.css.append(f"/_addons/{addon_package}/web/inline_edit.css")
    web_content.js.append(f"/_addons/{addon_package}/web/inline_edit.js")
```

→ File tĩnh trong thư mục `web/` của add-on được Anki tự serve tại
`/_addons/<package>/web/...` — không cần route/server riêng. Đúng khớp cấu trúc
`inline-field-editor/web/inline_edit.js` + `.css` đã định trong SPEC.md.

**Nhận message từ JS (`pycmd()`)** — `webview_did_receive_js_message`
(`_aqt/hooks.py:5671-5733`):

```python
def on_webview_did_receive_js_message(
    handled: tuple[bool, Any], message: str, context: Any
) -> tuple[bool, Any]:
    if not message.startswith("ife:"):
        return handled  # không phải message của add-on này, bỏ qua
    # xử lý, trả (True, result) để báo "đã xử lý, đừng đưa cho handler khác"
    ...
    return (True, None)
```

`context` là instance được truyền vào `set_bridge_command()` — dùng để kiểm tra đang ở đúng màn
hình reviewer nếu cần (tương tự cách check ở `webview_will_set_content`).

## Kết luận cho Task 3-5

Không phát hiện rủi ro nào trong "Risks" của plan (field filter method vẫn khả dụng ở bản
26.8.1) — kiến trúc trong SPEC.md/plan.md giữ nguyên, không cần đổi hướng. Có thể triển khai
thẳng Task 3 (skeleton) → Task 4 (field filter) → Task 5 (bridge message) theo đúng plan.
