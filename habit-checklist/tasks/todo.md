# Todo: Habit Checklist

Chi tiết đầy đủ từng task (acceptance criteria, verification, files): xem [plan.md](./plan.md).

## Phase 0: Foundation
- [x] Task 1: Venv + add-on skeleton (`manifest.json` + `__init__.py`) load sạch trong Anki thật

**Checkpoint 0:** Skeleton load được — pre-verify tự động OK, chờ xác nhận thêm bởi user khi restart Anki.

## Phase 1: Core vertical slice — checklist logic + wiring
- [x] Task 2: `checklist.py` — `build_habit_checklist()` + `apply_checklist_if_empty()` (TDD, pytest)
- [ ] Task 3: `config.json` + wiring `__init__.py` (hook `add_cards_did_add_note`, update_note)

**Checkpoint 1:** 4 case (trống/có sẵn/không tồn tại field/tự sửa tick+note giữ nguyên) verify OK trong Anki thật → đạt Success Criteria.

## Phase 2: Polish
- [ ] Task 4: README add-on + đóng gói + cài thử `.ankiaddon`

**Checkpoint cuối:** Toàn bộ Success Criteria trong [SPEC.md](../SPEC.md) đạt, sẵn sàng đề xuất commit.
