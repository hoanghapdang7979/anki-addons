# Spec: Essential Words CN→VI Translator

> Đây **không phải Anki add-on** (không có `manifest.json`/`__init__.py`, không load vào Anki)
> — là 1 script chuẩn bị dữ liệu, đặt trong `tools/` (khác `<ten-addon>/` per CLAUDE.md) vì repo
> này vốn dành cho add-on. Kết quả (file JSON đã dịch) có thể dùng làm input cho 1 add-on import
> sau này, nhưng đó là việc ngoài scope hiện tại (đã xác nhận ở bước hỏi).

## Objective

Dịch toàn bộ nội dung tiếng Trung trong file từ điển
`C:\Users\Client\Downloads\Essential Words (副本).json` (3600 từ, ~58,400 đoạn text, ~1.27
triệu ký tự — bao gồm cả phần `etymology` từ nguyên) sang tiếng Việt, dùng **Google Cloud
Translation API**, ghi ra **file JSON mới** (không đụng file gốc trong Downloads) — giữ nguyên
cấu trúc, chỉ thay nội dung các field chứa tiếng Trung.

**User:** chỉ Dang (cá nhân).

**Field cần dịch** (xem cấu trúc đầy đủ đã phân tích trước đó):
- `trans[].cn`
- `sentences[].cn`
- `phrases[].cn`
- `synos[].cn`
- `relWords.rels[].words[].cn`
- `etymology[].d`
- `etymology[].t` — **chỉ phần sau dấu `:`** nếu có tiếng Trung (format `"<word>:<nghĩa tiếng
  Trung hoặc rỗng>"`, vd `"agree:同意"` → dịch phần `"同意"`, giữ nguyên `"agree:"`; nếu không có
  ký tự tiếng Trung sau `:` thì giữ nguyên cả `t`, không gọi API).

**Field KHÔNG đụng vào** (đã là tiếng Anh, giữ nguyên 100%): `word`, `phonetic0`, `phonetic1`,
`trans[].pos`, `sentences[].c`, `phrases[].c`, `synos[].pos`, `synos[].ws[]`, `relWords.root`,
`relWords.rels[].pos`, `relWords.rels[].words[].c`.

**Thay thế tại chỗ, không giữ song song:** field `cn`/`d` sau khi dịch chứa tiếng Việt (không
thêm field mới `vi` bên cạnh) — **key name giữ nguyên** (`cn`, `d`, `t`) dù nội dung giờ là tiếng
Việt, để không đổi structure/schema của file (xem Open Questions #1 nếu muốn đổi tên key).

**Success = xong khi:** có 1 file JSON mới, cùng structure/số lượng item với file gốc, mọi field
tiếng Trung đã thành tiếng Việt, mọi field tiếng Anh giữ nguyên y hệt, file gốc trong Downloads
không bị đụng tới.

## Tech Stack

- Python + Google Cloud Translation API (`google-cloud-translate` v3 client library, hoặc REST
  API qua `requests` nếu không muốn thêm dependency nặng — quyết định cụ thể ở bước `/planning`).
- Venv riêng cho tool này (`tools/essential-words-translate/.venv`), không dùng chung venv với
  bất kỳ add-on nào.
- Không cần `aqt`/`anki` — tool này không liên quan gì tới Anki runtime.
- `pytest` cho phần logic thuần (extract/reinsert), **mock hoàn toàn lời gọi API thật trong
  test** — không gọi Google API thật trong test suite (tốn phí, cần network, non-deterministic).

## Commands

```bash
cd tools/essential-words-translate
python -m venv .venv
.venv/Scripts/pip install google-cloud-translate pytest

# Test (logic thuần, mock API — không tốn phí, không cần API key)
cd tests
../.venv/Scripts/python -m pytest . -v

# Chạy thử trên 1 mẫu nhỏ trước (bắt buộc — xem Boundaries "Hỏi trước")
../.venv/Scripts/python translate.py --input "C:\Users\Client\Downloads\Essential Words (副本).json" --output ./output/sample.json --limit 10 --credentials ./secrets/gcloud-key.json

# Chạy full (chỉ sau khi user xác nhận kết quả mẫu OK)
../.venv/Scripts/python translate.py --input "C:\Users\Client\Downloads\Essential Words (副本).json" --output ./output/essential-words-vi.json --credentials ./secrets/gcloud-key.json
```

## Project Structure

```
tools/essential-words-translate/
  SPEC.md
  translate.py              # CLI: đọc input JSON, extract strings cần dịch, gọi API
                              #   (có cache/checkpoint), reinsert kết quả, ghi output JSON
  translator.py               # logic thuần: extract_translatable_strings(), rebuild_json()
                              #   — không import google-cloud-translate trực tiếp, nhận 1
                              #   hàm translate_fn(list[str]) -> list[str] để dễ mock trong test
  gcloud_client.py             # wrapper mỏng gọi Google Cloud Translation API thật (batch,
                              #   retry, rate-limit) — KHÔNG test bằng API thật, chỉ test bằng
                              #   cách mock ở tests
  secrets/                     # gitignored — chứa service account key JSON của Google Cloud
  output/                       # gitignored — file JSON đã dịch (có thể nặng, không commit)
  cache/                         # gitignored — checkpoint cache (string gốc -> đã dịch), để
                              #   resume nếu chạy giữa chừng bị lỗi/dừng, không dịch lại từ đầu
  tests/
    conftest.py
    test_translator.py         # test extract/rebuild logic với translate_fn giả (mock)
```

## Code Style

```python
from typing import Callable

def extract_translatable_strings(data: list[dict]) -> list[str]:
    """Walk the word-entry list and collect every Chinese string to translate.

    Order matters - rebuild_json() re-walks in the same order to map
    translations back by position (paired with the unique-string cache by
    the caller, not here - this function only knows "what needs translating
    in what order", not deduplication).
    """
    ...


def rebuild_json(
    data: list[dict], translate_fn: Callable[[list[str]], list[str]]
) -> list[dict]:
    """Return a new structure with every field in TRANSLATABLE_FIELDS replaced
    by its translation (via translate_fn), everything else untouched.

    translate_fn takes a batch of unique strings and returns their
    translations in the same order - this is the only seam that touches the
    network, so tests pass in a fake translate_fn and never hit Google's API.
    """
    ...
```

- `translator.py` không import `google.cloud.translate` — nhận `translate_fn` như tham số
  (dependency injection đơn giản), giữ đúng nguyên tắc "logic thuần tách khỏi I/O ngoài" đã dùng
  xuyên suốt các add-on trong repo.
- `gcloud_client.py` là nơi DUY NHẤT import `google.cloud.translate`, chỉ có 1 hàm public dạng
  `translate_batch(strings: list[str], api_key_path: str) -> list[str]` khớp signature
  `translate_fn` ở trên.
- Không `print()` cho log tiến độ — dùng `logging` với progress rõ ràng (vd "đã dịch
  1200/51452 unique strings").

## Testing Strategy

- **Unit test** (`pytest`, không gọi API thật): `extract_translatable_strings()` với input giả
  nhỏ (2-3 word entry) → đúng danh sách string theo đúng thứ tự; `rebuild_json()` với
  `translate_fn` giả (vd trả về `"[VI] " + s`) → xác nhận field tiếng Trung được thay đúng, field
  tiếng Anh (`word`, `phonetic0`, `c`, `pos`, `ws`, `root`...) giữ nguyên y hệt object gốc;
  `etymology[].t` case có tiếng Trung sau `:` vs case không có → xử lý đúng như mô tả ở Objective.
- **Không test `gcloud_client.py` bằng API thật** — nếu cần xác nhận wrapper gọi đúng API, mock
  `google.cloud.translate` client trong test, không phát request thật (tốn phí, cần network).
- **Manual verify** (bắt buộc trước khi chạy full): chạy `--limit 10`, đọc thủ công output JSON,
  xác nhận bản dịch tiếng Việt hợp lý, cấu trúc JSON hợp lệ, field tiếng Anh không bị đụng.

## Boundaries

- **Luôn làm:**
  - Không bao giờ ghi đè file gốc trong `Downloads/` — luôn ghi ra file mới trong `output/`.
  - Cache/checkpoint kết quả dịch theo từng batch (string gốc → bản dịch) — nếu script dừng
    giữa chừng (lỗi mạng, Ctrl+C, hết quota), lần chạy sau **không dịch lại** string đã có trong
    cache (tốn phí thật, phải tránh dịch trùng).
  - Dedupe string trước khi gọi API (giảm ~12% số request theo phân tích thực tế) — dịch 1 lần
    cho mỗi unique string, áp dụng lại cho mọi chỗ string đó xuất hiện.
  - Nếu API dịch lỗi/trả rỗng cho 1 string cụ thể → log rõ ràng string nào lỗi, **không** âm thầm
    giữ nguyên tiếng Trung rồi coi như đã xong (dễ lọt sót, người dùng tưởng đã dịch hết).
  - `secrets/`, `output/`, `cache/` đã có trong `.gitignore` chung của repo (`.env`/`secrets/`
    đã match `secrets/`; `output/`/`cache/` cần thêm — xem Open Questions).
- **Hỏi trước:**
  - Chạy full 51,452 unique string (tốn phí thật trên tài khoản Google Cloud của user) — **bắt
    buộc** chạy `--limit 10` xác nhận chất lượng dịch + format đúng trước, user xác nhận rõ ràng
    mới chạy full. Đây là hard-stop, không tự động chuyển từ sample sang full.
  - Đổi tên key (`cn` → `vi` chẳng hạn) thay vì giữ nguyên tên key như đã chốt ở Objective.
- **Không bao giờ:**
  - Hardcode API key/service account credentials trong code — chỉ đọc từ file trong `secrets/`
    (đã gitignore) hoặc biến môi trường, không commit dưới bất kỳ hình thức nào.
  - Sửa/xoá file gốc `Essential Words (副本).json` trong Downloads.
  - Đụng vào bất kỳ field tiếng Anh nào đã liệt kê ở Objective — chỉ field tiếng Trung mới bị
    thay.

## Success Criteria

- File output JSON có đúng 3600 item, cấu trúc/key giống hệt file gốc. ✅ Đạt (Task 8).
- Mọi field tiếng Trung đã liệt kê chứa tiếng Việt, không còn ký tự Hán nào sót lại (verify bằng
  script quét unicode range). **Đạt gần như hoàn toàn, có ngoại lệ đã được user chấp nhận tường
  minh** (xem "Kết quả thực tế" bên dưới) — không phải oversight, không cần fix thêm.
- Mọi field tiếng Anh giữ nguyên 100% so với file gốc (diff bằng script). ✅ Đạt (Task 8).
- File gốc trong `Downloads/` không có thay đổi gì (checksum trước/sau giống nhau). ✅ Đạt.
- `pytest tools/essential-words-translate/tests` pass 100%. ✅ Đạt (36/36).

### Kết quả thực tế (Task 8 — validate)

`validate_output.py` báo **70/51,005 unique string vẫn còn ký tự Hán** sau khi chạy full — đã
điều tra kỹ và phân loại, user xác nhận chấp nhận, không coi là lỗi cần fix thêm:

- **13 field**: tag chuyên ngành ngắn dạng `[计]`/`[自]`/`[建]`/`[流]`/`[仪]`/`[宝]`/`[交]` trong
  `synos.cn` — Google Translate nhất quán không dịch các tag ngoặc vuông 1 ký tự này.
- **~57 field**: thành ngữ/từ tiếng Trung được trích dẫn có chủ đích trong đoạn `etymology.d` đã
  dịch tiếng Việt (giống trích Latin trong từ điển từ nguyên tiếng Anh) — hành vi hợp lý của
  Google Translate, không phải lỗi.
- **1 lỗi dịch thật đã fix thủ công**: `lick.trans[0].cn` — Google Translate trả về gần như y
  nguyên bản gốc (kể cả sau khi retry, không phải lỗi thoáng qua) → dịch tay trực tiếp (câu định
  nghĩa từ điển đơn giản), cập nhật vào cache, không tốn thêm phí API.

`validate_output.py` vẫn trả exit code 1 (FAIL theo tiêu chí chữ nghĩa "0 ký tự Hán") — đây là
hành vi ĐÚNG của script (báo cáo sự thật khách quan), không phải bug. Quyết định chấp nhận 70
field còn lại là quyết định sản phẩm của user, ghi lại ở đây để người đọc sau không hiểu nhầm là
việc chưa xong.

## Open Questions

1. ~~Giữ tên key `cn`/`d`/`t` hay đổi tên~~ — **đã chốt: giữ nguyên tên key** (user xác nhận).
2. ~~Google Cloud credentials chưa có~~ — **đã có hướng dẫn tạo**, xem [SETUP.md](./SETUP.md).
   User tự thực hiện (tạo project, bật billing, bật API, tạo service account key) — tôi không có
   quyền tạo tài khoản/nhập thông tin thanh toán.
3. ~~`.gitignore` cần thêm output/cache~~ — **đã thêm** vào `.gitignore` chung của repo.
4. **Chi phí ước tính ~20-25 USD** cho ~1.27 triệu ký tự theo giá Google Cloud Translation API
   hiện hành — vẫn cần verify giá thật tại thời điểm chạy (giá có thể đổi), không chốt cứng theo
   trí nhớ training data. Xem thêm ghi chú chi phí trong SETUP.md.
