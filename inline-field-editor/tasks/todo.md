# Todo: Inline Field Editor

Chi tiết đầy đủ từng task (acceptance criteria, verification, files): xem [plan.md](./plan.md).

## Phase 0: Foundation & Verification
- [x] Task 1: Tạo Anki profile test riêng (`IFE-Test`) — không dùng `User 1` thật
- [x] Task 2: Verify Anki API thật (update note, field filter hook, webview bridge hook) — ghi vào `docs/api-notes.md`
- [x] Task 3: Add-on skeleton (`manifest.json` + `__init__.py`) load sạch trong Anki thật

**Checkpoint 0:** API đã verify, skeleton load được → review với user trước khi tiếp tục.

## Phase 1: Vertical slice — edit + save end-to-end
- [ ] Task 4: Field filter render `{{edit:Field}}` → `<span data-ife-field contenteditable>`
- [ ] Task 5: JS blur → `pycmd` → Python lưu vào note
- [ ] Task 6: Xác nhận edit không ảnh hưởng scheduling/interval

**Checkpoint 1:** Vertical slice cốt lõi hoạt động thật → review với user trước Phase 2.

## Phase 2: Formatting + an toàn dữ liệu
- [ ] Task 7: Ctrl+B/I/U trong vùng editable, không đụng phím tắt review gốc
- [ ] Task 8: Fail-safe khi lưu lỗi + sanitize HTML (`<script>`, `on*=`)

**Checkpoint 2:** `pytest` pass 100%, format + fail-safe verify thủ công OK.

## Phase 3: Polish
- [ ] Task 9: CSS outline hover/focus cho vùng editable
- [ ] Task 10: README add-on + đóng gói + cài thử `.ankiaddon`

**Checkpoint cuối:** Toàn bộ Success Criteria trong [SPEC.md](../SPEC.md) đạt, sẵn sàng đề xuất commit.
