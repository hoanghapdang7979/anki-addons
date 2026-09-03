# Implementation Plan: Essential Words CN→VI Translator

> Đặt trong `tools/essential-words-translate/tasks/plan.md` — cùng quy ước với các add-on trong
> repo (mỗi project con tự quản lý plan/task riêng), dù đây không phải add-on.

## Overview

Dựa trên [SPEC.md](../SPEC.md): dịch ~58,400 đoạn text tiếng Trung (~1.27 triệu ký tự) trong
file từ điển 3600 từ sang tiếng Việt bằng Google Cloud Translation API, ghi ra file JSON mới,
giữ nguyên cấu trúc + mọi field tiếng Anh. Tách logic thuần (extract/rebuild JSON) khỏi phần gọi
API thật, có cache/checkpoint để không dịch lại khi chạy lại, và có **hard gate bắt buộc** giữa
chạy thử mẫu nhỏ và chạy full (tốn phí thật ~20-25 USD, cần verify giá tại thời điểm chạy).

## Architecture Decisions

- **Dependency injection cho `translate_fn`** — `translator.py` (logic thuần) nhận 1 hàm
  `translate_fn(list[str]) -> list[str]` thay vì tự gọi Google API, để test được toàn bộ logic
  extract/rebuild mà không cần network/API key/tốn phí. Chỉ `gcloud_client.py` chạm
  `google.cloud.translate` thật.
- **Cache theo unique string, không theo vị trí** — dedupe trước khi gọi API (giảm ~12% request
  theo phân tích thực tế ở `/spec`), cache key = string gốc, value = bản dịch. Cache ghi ra disk
  sau **mỗi batch** (không đợi xong hết) để resume được nếu crash/dừng giữa chừng — quan trọng vì
  đây là chi phí thật, không được dịch lại từ đầu chỉ vì lỗi mạng ở batch thứ 400.
- **2 task tách biệt rõ ràng cho "chạy thử" và "chạy full"** (Task 6 vs Task 7) — Task 7 là task
  duy nhất trong toàn bộ plan này **không được tự động chạy dưới `/build auto`** dù đang autonomous
  mode, vì tốn phí thật không hoàn lại được và cần user xác nhận đã xem kết quả mẫu ở Task 6 trước.
  Đúng tinh thần "high-risk/irreversible" trong quy trình `/build auto`.
- **Không dùng `google-cloud-translate` client library nếu setup phức tạp hơn cần thiết** — quyết
  định cụ thể dùng client library chính thức hay REST API thuần qua `requests` sẽ chốt ở Task 3
  (bất kỳ cách nào cũng phải qua interface `translate_batch(strings, credentials_path) ->
  list[str]` giống nhau, không ảnh hưởng tới các task khác).

## Task List

### Phase 0: Foundation

- [x] **Task 1: Venv + verify Google Cloud credentials hoạt động** — DONE. Key ban đầu (copy từ
  Downloads) chưa bật Cloud Translation API trên project (`gen-lang-client-0358626728`, service
  account tạo trước đó cho mục đích khác, tên `text-to-speed@...`) — lỗi 403, user tự bật qua
  link Google trả về, retry thành công. Verify bằng câu dịch thật ("你好，谢谢你" →
  "Chào bạn, cảm ơn bạn."), đúng dấu tiếng Việt (kiểm tra qua file UTF-8, không nhìn qua console
  Windows vì console cp1252 hiển thị sai ký tự có dấu, không phải lỗi dữ liệu).
  - **Description:** Venv riêng (`tools/essential-words-translate/.venv`), cài
    `google-cloud-translate` + `pytest`. Chạy lệnh smoke-test trong SETUP.md (`client.translate('你好', ...)`) để xác nhận key thật hoạt động trước khi viết code phụ thuộc vào nó.
  - **Acceptance criteria:**
    - [ ] Lệnh smoke-test trong SETUP.md chạy thành công, in ra bản dịch tiếng Việt hợp lý.
  - **Verification:**
    - [ ] Manual: user đã hoàn thành SETUP.md (project + billing + API + service account key),
      chạy lệnh smoke-test, xác nhận kết quả.
  - **Dependencies:** None — nhưng **chặn cứng mọi task khác trong Phase 2-3** (không có
    credentials thật thì không verify được `gcloud_client.py`).
  - **Files likely touched:** none (chỉ setup venv + chạy lệnh có sẵn trong SETUP.md)
  - **Estimated scope:** XS

### Checkpoint: Foundation
- [ ] Credentials xác nhận hoạt động — chưa có thì dừng lại, không sang Phase 1.

### Phase 1: Core logic (pure, TDD — không cần credentials)

- [x] **Task 2: `translator.py` — extract + rebuild logic (TDD)** — DONE, 9/9 test pass ngay
  lần đầu. Thiết kế dùng chung 1 hàm `_collect_slots()` (danh sách cặp chuỗi-gốc + setter) cho
  cả extract và rebuild, tránh 2 hàm phải tự đi bộ cây JSON riêng rồi dễ lệch thứ tự với nhau.
  - **Description:** Viết `extract_translatable_strings(data) -> list[str]` và
    `rebuild_json(data, translate_fn) -> list[dict]` theo đúng snippet trong SPEC.md → Code
    Style. Xử lý đúng case đặc biệt `etymology[].t` (chỉ dịch phần sau `:` nếu có ký tự Hán, giữ
    nguyên phần còn lại).
  - **Acceptance criteria:**
    - [ ] `extract_translatable_strings()` trả đúng danh sách string từ mọi field đã liệt kê
      trong SPEC.md → Objective, đúng thứ tự, KHÔNG lẫn field tiếng Anh.
    - [ ] `rebuild_json()` với `translate_fn` giả (vd `lambda ss: ["[VI]" + s for s in ss]`) →
      field tiếng Trung đổi đúng, field tiếng Anh (`word`, `phonetic0/1`, `.c`, `.pos`, `.ws`,
      `.root`) giữ nguyên y hệt object gốc (so sánh bằng `==`, không chỉ nhìn qua).
    - [ ] `etymology[].t` case `"agree:同意"` → chỉ phần `"同意"` qua `translate_fn`, giữ nguyên
      `"agree:"`; case `"agree:"` (không có Hán) → giữ nguyên 100%, không gọi `translate_fn`.
  - **Verification:**
    - [ ] `pytest tools/essential-words-translate/tests` (chạy từ trong `tests/`, cùng lý do tên
      thư mục có dấu gạch ngang đã gặp ở các add-on khác) pass 100%.
  - **Dependencies:** None (song song Task 1 được — không cần credentials).
  - **Files likely touched:** `tools/essential-words-translate/translator.py`,
    `tools/essential-words-translate/tests/conftest.py`,
    `tools/essential-words-translate/tests/test_translator.py`
  - **Estimated scope:** M

### Checkpoint: Core logic
- [ ] Logic extract/rebuild đã test kỹ, đặc biệt case `etymology.t` — đây là phần dễ sai nhất vì
  format lẫn tiếng Anh + tiếng Trung trong cùng 1 string.

### Phase 2: API wrapper + cache (cần credentials thật cho phần verify, không cần cho unit test)

- [x] **Task 3: `gcloud_client.py` — wrapper gọi Google Cloud Translation API** — DONE, 7 test
  mock pass + verify tay 2 string với API thật ("你好","谢谢" → "Xin chào","Cảm ơn", đúng thứ
  tự). Batch theo cả max-count (100) và max-chars (4500) để an toàn với giới hạn API thật (không
  chốt cứng theo 1 con số duy nhất chưa verify).
  - **Description:** Hàm `translate_batch(strings: list[str], credentials_path: str) ->
    list[str]` — gọi Google Cloud Translation API (batch nhiều string/request theo giới hạn của
    API), có retry + backoff khi lỗi tạm thời (rate limit, network).
  - **Acceptance criteria:**
    - [ ] Unit test mock `google.cloud.translate` client — verify gọi đúng tham số
      (source='zh', target='vi'), verify retry logic khi mock trả lỗi rồi thành công.
    - [ ] **Không có test nào gọi API thật** (đúng Boundaries trong SPEC.md).
  - **Verification:**
    - [ ] `pytest` pass 100% (chỉ mock, không tốn phí).
    - [ ] Manual (dùng credentials thật từ Task 1): gọi `translate_batch(["你好", "谢谢"],
      ...)` trực tiếp, xác nhận trả đúng 2 bản dịch tiếng Việt — bài test tay nhỏ, gần như miễn
      phí (2 string), KHÔNG phải chạy full.
  - **Dependencies:** Task 1 (cần credentials thật cho phần manual verify, không cần cho unit test)
  - **Files likely touched:** `tools/essential-words-translate/gcloud_client.py`,
    `tools/essential-words-translate/tests/test_gcloud_client.py`
  - **Estimated scope:** S

- [x] **Task 4: Cache/checkpoint module** — DONE, 8/8 test pass, bao gồm test khẳng định rõ
  "update() trả về là dữ liệu đã nằm trên disk" (không đợi tới cuối job mới flush) — đúng yêu cầu
  bảo vệ chi phí thật quan trọng nhất trong toàn bộ plan.
  - **Description:** Module quản lý cache dịch (string gốc → bản dịch), đọc/ghi ra file JSON
    trong `cache/`. Hàm nhận danh sách unique string cần dịch, trả về những string CHƯA có trong
    cache, sau khi dịch xong (dù chỉ 1 phần) thì ghi cache ngay — không đợi hết toàn bộ job.
  - **Acceptance criteria:**
    - [ ] Cache load đúng từ file cũ nếu có, string đã có trong cache không bị dịch lại (verify
      bằng cách đưa `translate_fn` giả có đếm số lần gọi, xác nhận không gọi cho string đã cache).
    - [ ] Cache ghi ra disk sau mỗi batch (không phải chỉ ghi 1 lần ở cuối) — verify bằng cách mô
      phỏng lỗi giữa chừng (raise exception ở batch thứ 2), xác nhận cache batch 1 vẫn được lưu.
  - **Verification:**
    - [ ] `pytest` pass 100%, dùng file cache tạm trong thư mục test (không đụng
      `cache/` thật).
  - **Dependencies:** None (logic thuần, không cần credentials)
  - **Files likely touched:** `tools/essential-words-translate/cache_store.py`,
    `tools/essential-words-translate/tests/test_cache_store.py`
  - **Estimated scope:** S

### Checkpoint: API + cache
- [ ] `gcloud_client.py` verify gọi API thật thành công (2 string, gần miễn phí).
- [ ] Cache module resumable đã test kỹ (đây là thứ bảo vệ user khỏi mất tiền nếu job full bị lỗi
  giữa chừng — mức độ quan trọng cao).

### Phase 3: CLI + chạy thật (có cổng chặn rõ ràng giữa thử và full)

- [x] **Task 5: `translate.py` — CLI orchestration** — DONE, 6 test tích hợp mock hoàn toàn +
  6 test cho `gcloud_client.translate_chunks` (hàm mới, thêm khi làm task này). Phát hiện lúc
  implement: `translate_batch()` (Task 3) trả kết quả 1 lần sau khi dịch xong TOÀN BỘ input —
  nếu gọi thẳng với hàng chục nghìn string, lỗi ở batch giữa chừng sẽ làm mất các batch trước đó
  chưa kịp cache. Thêm `translate_chunks()` cạnh nó (không sửa `translate_batch()` đã test/commit
  — giờ nó chỉ là wrapper gọi `translate_chunks()` không callback), cho phép `translate.py`
  checkpoint cache sau MỖI chunk qua callback `on_chunk_done`.
  - **Description:** Ghép `translator.py` + `gcloud_client.py` + `cache_store.py` thành CLI:
    đọc input JSON → extract unique string cần dịch → check cache → dịch phần chưa cache (qua
    `gcloud_client.translate_batch`, batch theo giới hạn API) → cập nhật cache → `rebuild_json`
    → ghi output JSON. Args: `--input`, `--output`, `--credentials`, `--limit` (giới hạn số
    **word entry** xử lý, để chạy thử rẻ).
  - **Acceptance criteria:**
    - [ ] `--limit 10` chỉ xử lý 10 word entry đầu, không đọc/dịch phần còn lại của file 3600 từ.
    - [ ] Không có `--limit` → xử lý toàn bộ (dùng cẩn thận — đây là lúc tốn phí thật).
    - [ ] Log tiến độ rõ ràng (vd "đã dịch 1200/51452 unique string") qua `logging`, không
      `print()`.
  - **Verification:**
    - [ ] Chưa chạy thật ở task này (để dành Task 6) — chỉ verify bằng cách chạy với
      `translate_fn`/`gcloud_client` đã mock hoàn toàn trong 1 integration test nội bộ (không
      gọi API thật, không tốn phí) để xác nhận toàn bộ pipeline nối đúng.
  - **Dependencies:** Task 2, Task 3, Task 4
  - **Files likely touched:** `tools/essential-words-translate/translate.py`
  - **Estimated scope:** M

- [x] **Task 6: Chạy thử `--limit 10` với API thật** — DONE. Phát hiện + fix 1 bug chất lượng
  lúc review: dấu ngoặc kép trong bản dịch bị encode thành `&quot;` (Google API mặc định
  `format="html"` khi không truyền `format_`) — thêm `format_="text"` tường minh trong
  `gcloud_client.py` (có test regression riêng), xoá cache cũ dính lỗi, dịch lại 175 string
  (chi phí không đáng kể). Output cuối: JSON hợp lệ, 10 item, bản dịch tự nhiên, field tiếng Anh
  giữ nguyên 100%, `etymology.t` xử lý đúng cả 2 case. Cũng sửa log message gây hiểu lầm
  ("already cached" gộp chung cả duplicate-trong-batch) — giờ tách rõ unique/duplicate.
  - **Description:** Chạy CLI thật với `--limit 10` (10 word entry ≈ vài trăm ký tự, chi phí gần
    như bằng 0), đọc thủ công output, đánh giá chất lượng bản dịch.
  - **Acceptance criteria:**
    - [ ] Output JSON hợp lệ, đúng cấu trúc, 10 item.
    - [ ] Bản dịch tiếng Việt đọc được, hợp lý (không cần hoàn hảo — đây là máy dịch, nhưng phải
      đủ dùng được, không lỗi be bét/rỗng).
    - [ ] Field tiếng Anh trong 10 item này giữ nguyên y hệt file gốc.
  - **Verification:**
    - [ ] Manual — user tự đọc output, xác nhận **rõ ràng bằng lời** là chất lượng OK trước khi
      cho phép sang Task 7.
  - **Dependencies:** Task 5
  - **Files likely touched:** none (chỉ chạy CLI, output vào `output/sample.json` đã gitignore)
  - **Estimated scope:** XS

### Checkpoint: Trước khi chạy full — HARD GATE
- [ ] User đã xác nhận rõ ràng (không phải suy luận từ ngữ cảnh) đồng ý chạy full, biết rõ sẽ
  tốn phí thật (~20-25 USD ước tính, cần verify giá tại console.cloud.google.com/billing lúc
  chạy vì giá có thể đổi).
- [ ] **Tuyệt đối không tự động chạy Task 7 dưới `/build auto`** — kể cả khi toàn bộ plan này
  được approve 1 lần ở đầu autonomous run, Task 7 vẫn cần 1 xác nhận RIÊNG, tách biệt, ngay
  trước khi chạy — đúng nguyên tắc high-risk/irreversible-cost trong quy trình build.

- [ ] **Task 7: Chạy full translation job (TỐN PHÍ THẬT — cần xác nhận riêng)**
  - **Description:** Chạy CLI không giới hạn (`--input ... --output
    output/essential-words-vi.json --credentials secrets/gcloud-key.json`), xử lý toàn bộ 51,452
    unique string. Có thể mất thời gian đáng kể (phụ thuộc rate limit API) — chạy
    `run_in_background` nếu dùng qua Claude Code, theo dõi log tiến độ.
  - **Acceptance criteria:**
    - [ ] Job chạy xong không lỗi, hoặc nếu có lỗi giữa chừng thì cache đã lưu đủ để resume mà
      không dịch lại từ đầu.
    - [ ] File output có đủ 3600 item.
  - **Verification:**
    - [ ] Theo dõi log tiến độ trong lúc chạy, không chỉ chờ xong mới kiểm tra.
  - **Dependencies:** Task 6 (đã xác nhận chất lượng mẫu) + **xác nhận riêng của user cho task
    này cụ thể**
  - **Files likely touched:** none (output vào `output/essential-words-vi.json`, gitignore)
  - **Estimated scope:** S (code không đổi gì so với Task 5, chỉ là 1 lần chạy job lớn)

- [ ] **Task 8: Validate output đầy đủ**
  - **Description:** Script kiểm tra: (a) số item đúng 3600, (b) không còn ký tự Hán nào sót lại
    trong các field đã liệt kê phải dịch (quét unicode range `一`-`鿿`), (c) mọi field
    tiếng Anh giữ nguyên y hệt file gốc (diff từng field), (d) file gốc trong Downloads không đổi
    (so checksum trước/sau).
  - **Acceptance criteria:**
    - [ ] Cả 4 kiểm tra ở Description đều pass, in ra báo cáo rõ ràng (bao nhiêu item OK, có
      item nào còn sót Hán không — liệt kê cụ thể nếu có).
  - **Verification:**
    - [ ] Chạy script validate, xem output — nếu có item sót Hán, liệt kê rõ ra để user biết cần
      xử lý thủ công phần nào (không âm thầm bỏ qua).
  - **Dependencies:** Task 7
  - **Files likely touched:** `tools/essential-words-translate/validate_output.py`
  - **Estimated scope:** S

### Checkpoint: Complete
- [ ] Toàn bộ Success Criteria trong SPEC.md đạt, validate script (Task 8) pass sạch.
- [ ] Đề xuất commit — nhưng **chỉ commit code** (`translator.py`, `gcloud_client.py`,
  `cache_store.py`, `translate.py`, `validate_output.py`, tests) — `output/`, `cache/`,
  `secrets/` đã gitignore, không commit dữ liệu/key.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Job full bị lỗi giữa chừng (network, rate limit, credit hết) phải dịch lại từ đầu, tốn phí 2 lần | High | Cache ghi ra disk sau MỖI batch (Task 4), không đợi xong hết — resume từ chỗ dừng, không dịch lại string đã cache. |
| Chất lượng dịch máy không tốt cho thuật ngữ/thành ngữ trong etymology | Medium | Task 6 bắt buộc human review mẫu trước khi chạy full — nếu chất lượng tệ, dừng lại bàn cách khác (đổi API, hoặc bỏ etymology) trước khi tốn phí cho 1.27 triệu ký tự. |
| Chi phí thực tế cao hơn ước tính (giá API đổi, hoặc tính sai số ký tự) | Medium | SETUP.md đã nhắc verify giá thật tại console.cloud.google.com/billing trước Task 7; khuyến nghị user tự đặt budget alert trong Google Cloud Console (việc này user tự làm, ngoài scope code). |
| `etymology[].t` parse sai (dịch nhầm phần tên từ tiếng Anh, hoặc bỏ sót phần tiếng Trung) | Medium | Task 2 có test case cụ thể cho cả 2 dạng (`"agree:同意"` và `"agree:"`) — không chỉ test chung chung "có nội dung/không có nội dung". |
| Google Cloud Translation API rate limit khi gửi 51,452 string liên tục | Low-Medium | `gcloud_client.py` (Task 3) có retry + backoff; batch size theo giới hạn API chính thức (verify limit thật lúc implement, không đoán). |

## Open Questions

- Không phát sinh thêm ở bước planning — các Open Question trong SPEC.md đã chốt 3/4, còn lại
  (giá thật) sẽ verify ngay trước Task 7 (checkpoint hard gate).
