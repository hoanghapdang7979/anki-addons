# Todo: Auto Date Field

Chi tiết đầy đủ từng task (acceptance criteria, verification, files): xem [plan.md](./plan.md).

## Phase 0: Foundation
- [x] Task 1: Venv + add-on skeleton (`manifest.json` + `__init__.py`) load sạch trong Anki thật

**Checkpoint 0:** Skeleton load được, xác nhận bởi user.

## Phase 1: Core vertical slice — date logic + wiring
- [x] Task 2: `date_fill.py` — `today_iso()` + `apply_date_if_empty()` (TDD, pytest)
- [ ] Task 3: `config.json` + wiring `__init__.py` (hook `add_cards_did_add_note`, update_note)

**Checkpoint 1:** 3 case (field trống/có sẵn/không tồn tại) verify OK trong Anki thật → đạt Success Criteria.

## Phase 2: Polish
- [ ] Task 4: README add-on + đóng gói + cài thử `.ankiaddon`

**Checkpoint cuối:** Toàn bộ Success Criteria trong [SPEC.md](../SPEC.md) đạt, sẵn sàng đề xuất commit.
