# Todo: Tree Card Generator

Chi tiết đầy đủ từng task (acceptance criteria, verification, files): xem [plan.md](./plan.md).

## Phase 0: Foundation & rủi ro kỹ thuật cao nhất
- [x] Task 1: Venv + add-on skeleton load sạch trong Anki thật
- [x] Task 2: Verify `QMimeData.setHtml()` paste vào Anki Editor hoạt động đúng — **GO**, hoạt động đúng

**Checkpoint 0:** Skeleton load được + cơ chế clipboard đã xác nhận hoạt động trong Anki thật. Nếu Task 2 fail → dừng lại bàn phương án khác trước khi làm tiếp.

## Phase 1: Core logic — parser + renderer (pure, TDD)
- [x] Task 3: `tree_parser.py` — `parse_tree()` (test cả case nhỏ lẫn cây mẫu đầy đủ từ SPEC.md)
- [x] Task 4: `tree_renderer.py` — `render_html()` (escape HTML, toggle collapsible, tự chứa CSS+JS)

**Checkpoint 1:** `pytest` pass 100%, parser+renderer test kỹ với cây mẫu thật.

## Phase 2: UI wiring — dialog thật + copy clipboard
- [ ] Task 5: `dialog.py` + wiring `__init__.py` (thay đoạn test tạm ở Task 2 bằng dialog thật)
- [ ] Task 6: Manual end-to-end verify đầy đủ với cây mẫu 6 section thật trong Anki

**Checkpoint 2:** Toàn bộ Success Criteria trong [SPEC.md](../SPEC.md) đạt.

## Phase 3: Polish
- [ ] Task 7: README add-on + đóng gói + cài thử `.ankiaddon`

**Checkpoint cuối:** Sẵn sàng đề xuất commit (chỉ code, không commit `.venv/`).
