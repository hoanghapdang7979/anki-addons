# Todo: Essential Words CN→VI Translator

Chi tiết đầy đủ từng task (acceptance criteria, verification, files): xem [plan.md](./plan.md).

## Phase 0: Foundation
- [x] Task 1: Venv + verify Google Cloud credentials hoạt động (cần [SETUP.md](../SETUP.md) đã xong)

**Checkpoint 0:** Credentials xác nhận hoạt động.

## Phase 1: Core logic (pure, TDD)
- [ ] Task 2: `translator.py` — `extract_translatable_strings()` + `rebuild_json()` (đặc biệt case `etymology.t`)

**Checkpoint 1:** Logic extract/rebuild test kỹ, nhất là `etymology.t`.

## Phase 2: API wrapper + cache
- [ ] Task 3: `gcloud_client.py` — `translate_batch()` (mock trong test, verify tay 2 string với API thật)
- [ ] Task 4: `cache_store.py` — cache/checkpoint resumable

**Checkpoint 2:** API wrapper verify OK, cache module test kỹ khả năng resume.

## Phase 3: CLI + chạy thật
- [ ] Task 5: `translate.py` — CLI ghép toàn bộ pipeline
- [ ] Task 6: Chạy thử `--limit 10` với API thật, user tự đọc + xác nhận chất lượng

**🛑 HARD GATE — không tự động chạy tiếp dưới `/build auto`:** cần user xác nhận RIÊNG, rõ ràng
bằng lời, đồng ý tốn phí thật trước khi sang Task 7.

- [ ] Task 7: Chạy full translation job (**TỐN PHÍ THẬT** ~20-25 USD ước tính, verify giá lại trước khi chạy)
- [ ] Task 8: Validate output đầy đủ (đếm item, quét ký tự Hán sót, diff field tiếng Anh, checksum file gốc)

**Checkpoint cuối:** Toàn bộ Success Criteria trong [SPEC.md](../SPEC.md) đạt, chỉ commit code (không commit `output/`/`cache/`/`secrets/`).
