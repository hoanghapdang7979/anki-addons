# Todo: Tree Card Generator

Chi tiết đầy đủ từng task (acceptance criteria, verification, files): xem [plan.md](./plan.md).

## Phase 0: Foundation & rủi ro kỹ thuật cao nhất
- [x] Task 1: Venv + add-on skeleton load sạch trong Anki thật
- [x] Task 2: Verify `QMimeData.setHtml()` paste vào Anki Editor hoạt động đúng — **GO**, hoạt động đúng

**Checkpoint 0:** Skeleton load được + cơ chế clipboard đã xác nhận hoạt động trong Anki thật. Nếu Task 2 fail → dừng lại bàn phương án khác trước khi làm tiếp.

## Phase 1: Core logic — parser + renderer (pure, TDD)
- [x] Task 3: `tree_parser.py` — `parse_tree()` (test cả case nhỏ lẫn cây mẫu đầy đủ từ SPEC.md)
- [x] Task 4: `tree_renderer.py` — `render_html()` (escape HTML, toggle collapsible; kiến trúc
  đổi từ CSS+JS nhúng sang inline `style` + `<details>`/`<summary>` — xem plan.md Task 5)

**Checkpoint 1:** `pytest` pass 100%, parser+renderer test kỹ với cây mẫu thật.

## Phase 2: UI wiring — ghi thẳng vào field (đã đổi kiến trúc 3 lần, xem plan.md Task 5)
- [x] Task 5: `dialog.py` + wiring `__init__.py` — DONE, ghi thẳng field qua
  `editor.note`/`last_field_index`/`addMode`/`aqt.operations.note.update_note`/`loadNote()`,
  xác nhận bằng HTML source thật (Ctrl+Shift+X)
- [x] Task 6: Manual end-to-end verify đầy đủ với cây mẫu 6 section thật trong Anki — DONE

**Checkpoint 2:** Toàn bộ Success Criteria trong [SPEC.md](../SPEC.md) đạt.

## Phase 3: Polish
- [x] Task 7: README add-on (viết lại, bỏ hướng dẫn Ctrl+V) + đóng gói `.ankiaddon`

**Checkpoint cuối:** Sẵn sàng đề xuất commit (chỉ code, không commit `.venv/`).
