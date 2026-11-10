# Spec: Habit Heatmap (add-on `habit-heatmap`)

> Spec cho 1 add-on mới trong repo nhiều-add-on `anki-addons`, cùng quy ước với
> [tree-card-generator/SPEC.md](../tree-card-generator/SPEC.md) và
> [habit-checklist/SPEC.md](../habit-checklist/SPEC.md). Khác `habit-checklist` (điền list
> `[ ] habit` dạng text vào field Diary): add-on này vẽ heatmap trên màn hình deck, tick bằng
> nút, có đồng bộ.
>
> Chú thích: **[VERIFIED]** = đã đọc source `aqt`/`anki` **25.9.4** (đúng version Anki thật của
> user, venv pin theo `requirements.txt`). **[UNVERIFIED]** = suy luận/chưa test, phải kiểm chứng
> ở task đầu của plan.

## Objective

Trên màn hình danh sách deck (main screen), dưới bảng deck, vẽ **mỗi habit 1 khối heatmap kiểu
GitHub** (cột = tuần, ô = ngày; ô đã tick tô xanh, chưa tick xám), giống phong cách add-on
*Review Heatmap* (ID 1771074083, user đang cài) nhưng:

1. **1 khối = 1 habit** do user tự cấu hình (nhiều habit => nhiều khối).
2. **Không tự cập nhật từ review** — user **tick tay** từng ngày như app habit-tracker (mỗi khối có
   nút "Hôm nay ✓").
3. **Quá ngày không được check**: chỉ ô của **hôm nay** tick/bỏ tick được; mọi ô quá khứ chỉ đọc.
4. **Đồng bộ theo tài khoản** (AnkiWeb) để không mất chuỗi khi đổi máy.

Mỗi khối có dòng thống kê: **Current streak**, **Longest streak**, **Days done** (+ % trong cửa
sổ hiển thị).

**User:** chỉ Dang (cá nhân). Chỉ chạy trên Anki desktop (AnkiDroid/AnkiMobile không hiển thị
heatmap, nhưng dữ liệu vẫn đi theo sync).

## Quyết định kiến trúc quan trọng (đọc trước khi code)

### 1. Lưu dữ liệu ở **collection config**, không phải file của add-on
- `col.get_config(key)` / `col.set_config(key, val)` [VERIFIED `anki/collection.py:910-916`].
  Docstring chính thức: *"The config is currently sent on every sync, so please don't store more
  than a few kilobytes in it"* => config **đi theo sync AnkiWeb**, nhưng **phải giữ nhỏ**.
- Dữ liệu trong `meta.json`/`user_files/`/`config.json` của add-on là **per-device, KHÔNG sync**
  [VERIFIED qua CLAUDE.md repo + cơ chế add-on] — không dùng làm nguồn chính.
- Vì "vài KB": mỗi habit lưu **bitmap** (1 bit/ngày), không lưu list ngày. 3 năm ≈ 137 byte ≈ 190
  ký tự base64 (list số nguyên cùng lượng ≈ 6 KB/habit — vượt khuyến nghị).

### 2. Mô hình dữ liệu (grow-only, dễ merge)
```
config key "habitHeatmap.habits"   -> [{"id": "h_ab12", "name": "Exercise", "color": "#40c463",
                                         "created": <date ordinal>, "archived": false}, ...]
config key "habitHeatmap.d.<id>"   -> {"epoch": <date ordinal>, "bits": "<base64 bitmap>"}
```
- **Khoá ngày = `date.toordinal()`** (ngày lịch theo Anki-day, không phụ thuộc `col.crt`).
- **id habit ổn định** (không dùng tên làm khoá) => đổi tên không mất lịch sử.
- 1 config key / habit để thu hẹp bề mặt xung đột sync.

### 3. "Hôm nay" theo ngày của Anki, không theo đồng hồ hệ thống
- Dùng `mw.col.sched.day_cutoff` (timestamp bắt đầu ngày kế tiếp, tôn trọng "next day starts at")
  [VERIFIED tồn tại `anki/scheduler/base.py:59`; `today` ở `:55` là số ngày từ lúc tạo
  collection, **không** dùng làm khoá vì phụ thuộc `crt`].
- Ngày Anki hiện tại = `date.fromtimestamp(day_cutoff - 86400)` [UNVERIFIED ngữ nghĩa — chứng
  minh: 02:00 ngày 2/1 với cutoff 04:00 => `cutoff-86400` = 04:00 ngày 1/1 => ngày 1/1 (đúng, Anki
  chưa sang ngày); 05:00 ngày 2/1 => cutoff 04:00 ngày 3/1 => 2/1]. Hàm này là **logic thuần**
  (nhận timestamp), test được bằng pytest không cần Anki.
- **Chống tick ngày khác:** JS chỉ gửi `habitheatmap:toggle:<habit_id>`, **không gửi ngày**.
  Python tự tính "hôm nay" => UI/JS không thể tick quá khứ. Nút "Hôm nay" disable nếu ngày đã đổi
  khi trang chưa render lại (re-validate phía Python mỗi lần).
- Giới hạn thành thật: đổi đồng hồ máy vẫn có thể lách (không có cách chặn tuyệt đối offline);
  mức chấp nhận: dự án cá nhân.

### 4. Đồng bộ & chống mất chuỗi
- **Nguồn đồng bộ = AnkiWeb sẵn có** (không dựng server riêng). User cần bật sync AnkiWeb.
- Cơ chế merge của config khi **sync thường** (per-key theo mtime hay cả khối?) nằm trong Rust
  backend, **không đọc được từ Python** => **[UNVERIFIED]**; phải test 2 profile/2 máy (Risk #2).
- Rủi ro thật: 2 máy cùng tick *offline* rồi sync => 1 bên có thể ghi đè bên kia. Giảm thiểu:
  - **Shadow copy local** (`user_files/shadow-<tên profile>-<hash>.json`) lưu habit + bitmap + tombstone
    mỗi lần tick/sửa. **Mỗi profile 1 file riêng** vì `user_files/` dùng chung cho mọi profile trên máy
    (nếu chung 1 file thì tick của profile này lẫn sang profile kia dù không sync).
  - Trong hook `sync_did_finish` (và `profile_did_open`) [VERIFIED hook tồn tại,
    `aqt/main.py:1107` gọi sau sync xong, ngay trước `self.reset()`]: đọc config, **OR bitmap với
    shadow**, nếu khác thì `set_config` lại + cập nhật shadow. Tick là tập tăng-dần nên union
    không mất tick nào.
  - Shadow cũng là **backup** khi user chọn "Download from AnkiWeb" (full sync ghi đè cả
    collection): lần mở profile kế tiếp add-on union lại từ shadow.
- Bỏ tick **hôm nay**: cho phép (tránh bấm nhầm). Giới hạn đã biết: nếu máy khác vừa sync tick
  cùng ngày thì union có thể "hồi sinh" tick đã bỏ — chấp nhận (đã chốt, xem "Quyết định đã chốt").
- Khi bỏ tick hôm nay, phải bỏ bit ở **cả config lẫn shadow**, nếu không union tức thì hồi sinh
  chính tick vừa bỏ.

### 5. UI trên màn hình deck
- Hook `gui_hooks.deck_browser_will_render_content(deck_browser, content)` [VERIFIED tồn tại;
  `aqt/deckbrowser.py:187`], `DeckBrowserContent` có `tree` + `stats` (str HTML)
  [VERIFIED `aqt/deckbrowser.py:48-56`] => **nối thêm HTML vào `content.stats`**.
- Click ô "Hôm nay": `onclick='pycmd("habitheatmap:toggle:<id>")'`; nhận bằng
  `gui_hooks.webview_did_receive_js_message(handled, message, context)` [VERIFIED tồn tại;
  `aqt/webview.py:800`]; kiểm `isinstance(context, DeckBrowser)`, xử lý rồi
  `mw.deckBrowser.refresh()`.
- HTML + CSS **inline thuần** (bài học tree-card-generator: không dựa `<style>`/`<script>` ngoài
  luồng; ở deck browser `stdHtml` render được CSS nhưng giữ inline cho tự chứa và không đụng CSS của
  Review Heatmap).
- Cùng tồn tại với Review Heatmap: cả hai nối vào `content.stats`; thứ tự theo thứ tự load add-on
  [UNVERIFIED] — kiểm tra bằng mắt ở Risk #1.

## Tech Stack

- Python + `aqt.gui_hooks` (deck_browser_will_render_content, webview_did_receive_js_message,
  sync_did_finish, profile_did_open). Không JS riêng, không server, không network.
- `pytest` cho logic thuần. **Venv riêng pin** `aqt==25.9.4 anki==25.9.4` (`requirements.txt`) —
  bài học: venv bản 26.9 từng khiến `editor.nid`/`reload_note()` "tồn tại" trong dev nhưng không
  có trong Anki thật 25.9.4.
- Tách pure-logic vs aqt (quy ước repo).

## Commands

```bash
cd habit-heatmap
python -m venv .venv
.venv/Scripts/pip install pytest
.venv/Scripts/pip install -r requirements.txt     # aqt==25.9.4 anki==25.9.4

cd tests
../.venv/Scripts/python -m pytest . -v

# Cài thử trong Anki thật (Junction, không cần admin) — chỉ profile test IFE-Test
New-Item -ItemType Junction -Path "$env:APPDATA\Anki2\addons21\habit-heatmap" `
  -Target "C:\Users\Client\Desktop\anki-addons\habit-heatmap"
```

## Project Structure

```
habit-heatmap/
  manifest.json            # name, package "habit-heatmap", mod
  __init__.py                # đăng ký hook, nối vào các module bên dưới (chỉ file này + ui/store chạm aqt)
  days.py                     # thuần: anki_today(day_cutoff) -> date; week grid; mapping ô <-> ngày
  bitmap.py                    # thuần: encode/decode bitmap base64, set_bit, union (OR)
  stats.py                      # thuần: current_streak, longest_streak, days_done, pct
  render.py                      # thuần: build_block_html(habit, bits, today) -> str (inline style)
  store.py                        # aqt: đọc/ghi config + shadow, union khi sync
  manage_dialog.py                 # aqt: QDialog thêm/sửa/xoá/lưu trữ habit
  requirements.txt
  tests/ conftest.py test_days.py test_bitmap.py test_stats.py test_render.py
```
Mỗi file <~300 dòng; không `print()` (dùng `logging`).

## Code Style (chữ ký chính)

```python
def anki_today(day_cutoff: int) -> date:
    """Calendar date of the *current Anki day* (respects next-day-starts-at)."""

def toggle_today(bits: bytes, epoch: int, today: date) -> bytes:
    """Flip only today's bit. No date parameter other than `today` is ever accepted
    from the UI layer, so past days cannot be changed through this path."""

def current_streak(ticked: set[int], today_ordinal: int) -> int:
    """Consecutive ticked days ending today if today is ticked, else ending yesterday
    (an unticked *today* does not break the streak yet)."""
```

## Testing Strategy

- **Unit (pytest, không cần Anki):**
  - `anki_today`: ranh giới rollover (cutoff 04:00; 03:59 vs 04:01), DST, đổi năm.
  - `bitmap`: encode/decode roundtrip, tăng epoch/độ dài, `union` giao hoán + idempotent.
  - `stats`: streak hôm nay chưa tick, streak đứt giữa chừng, longest, ngày tương lai bị bỏ.
  - `toggle_today`: chỉ đổi bit hôm nay; không API nào nhận ngày tuỳ ý (test bằng chữ ký).
  - `render`: số ô đúng = tuần×7, ô quá khứ **không** có `onclick`, chỉ ô hôm nay có; escape tên
    habit (`html.escape`).
  - Kích thước: 5 năm × 10 habit, mỗi key < 1 KB.
- **Manual trong Anki thật (profile `IFE-Test`, yêu cầu bằng chứng cụ thể — screenshot hoặc
  `col.get_config` dump — không chỉ "đúng/sai", bài học tree-card-generator).**

## Boundaries

- **Luôn làm:** chỉ ghi qua Collection API (`get_config/set_config`); validate "hôm nay" phía
  Python; union-merge, không bao giờ ghi đè bitmap bằng bản ít bit hơn; pin version aqt/anki.
- **Hỏi trước:** đổi nơi lưu (ra ngoài collection config); cho sửa quá khứ ("backfill");
  thêm server/cloud riêng; hiển thị trên AnkiDroid.
- **Không bao giờ:** đọc/ghi `.anki2` trực tiếp; đụng collection/profile thật khi chưa xác nhận
  (test trên `IFE-Test`); sửa file của add-on khác (kể cả Review Heatmap); lưu >vài KB vào config;
  tin tick từ JS mang theo ngày.

## Success Criteria

- Mỗi habit đã cấu hình hiện 1 khối heatmap ở màn hình deck, cùng Review Heatmap không vỡ layout.
- Bấm "Hôm nay" tick/bỏ tick đúng habit; ô quá khứ không tương tác được; sau 04:00 (rollover) ô
  hôm nay chuyển sang ngày mới đúng.
- Streak/Days done đúng so với dữ liệu thử có biết trước.
- Đóng/mở Anki và **sync sang profile/máy thứ 2**: ticks còn nguyên; thử tick offline ở 2 nơi
  rồi sync => cả hai tick đều còn (nhờ union).
- `pytest habit-heatmap/tests` pass 100%.

## Risk-First (làm trước)

1. **Task đầu — vertical slice nhỏ nhất:** 1 habit cố định, render 1 khối vào `content.stats`,
   bấm "Hôm nay" qua `pycmd` -> `set_config` -> refresh. Chứng minh hook + bridge + persist hoạt
   động ở 25.9.4, và nhìn layout cạnh Review Heatmap.
2. **Task thứ hai — chứng minh sync:** 2 profile cùng tài khoản AnkiWeb (hoặc 2 máy); xem config
   có sync và merge ra sao khi cùng tick offline. **Cần user chủ động chạy sync AnkiWeb** (tác
   động tài khoản thật — tôi không tự làm).

## Quyết định đã chốt (user xác nhận)

1. **Cấu hình habit:** dialog riêng trong add-on (menu Tools), danh sách habit lưu trong
   **collection config** (`habitHeatmap.habits`) để đi theo sync. Không dùng `config.json`.
2. **Bỏ tick hôm nay:** **cho phép**. Giới hạn đã biết (union có thể hồi sinh tick đã bỏ nếu máy
   khác vừa sync tick cùng ngày) được chấp nhận.
3. **Cửa sổ hiển thị:** **53 tuần** (đủ 1 năm, như ảnh tham chiếu), cố định ở v1.
4. **Habit không dùng nữa:** mặc định **Lưu trữ** (ẩn khỏi màn hình deck, **giữ nguyên lịch sử**,
   có thể khôi phục). Ngoài ra có action **Xoá hẳn** (dialog xác nhận, ghi rõ "không hoàn tác"):
   xoá `habitHeatmap.d.<id>`, xoá khỏi `habitHeatmap.habits` **và xoá luôn entry trong shadow** —
   nếu không, bước union sau sync sẽ hồi sinh dữ liệu vừa xoá — shadow lưu thêm **tombstone** (id đã
   xoá có chủ đích) để union không khôi phục lại. **Không có dọn mồ côi tự động** (đổi so với bản
   đầu): dữ liệu `d.<id>` không còn trong `habits` chỉ bị bỏ qua khi render, không bao giờ bị xoá,
   vì danh sách habit cũ/stale đến qua sync không được phép làm mất lịch sử. Chỉ "Xoá hẳn" mới xoá.
5. **Habit hằng ngày** (v1): không có lịch tuỳ chỉnh theo tuần (chưa làm, hỏi lại nếu cần).

## Open Questions còn lại

- Màu mỗi habit: bảng màu cố định chọn trong dialog (mặc định) hay nhập mã hex tự do?
- Thứ tự các khối: theo thứ tự tạo; có cần nút lên/xuống trong dialog không (mặc định: có)?
