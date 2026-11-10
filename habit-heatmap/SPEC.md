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

## v2 — Giao diện kiểu Review Heatmap, note theo ngày, tooltip  *(phần này ưu tiên hơn v1 khi mâu thuẫn)*

> Yêu cầu của user (sau khi sync v1 đã chạy ổn): *"heatmap hiển thị giống add-on Review Heatmap; khi
> check today cho phép ghi thêm note; có tooltip khi chỉ vào các cell, hiển thị thông tin note và
> thông tin ngày."* Đã hỏi và chốt 4 điểm (mục v2.1). Tham chiếu giao diện: Review Heatmap
> (ID 1771074083, đã đọc source: Cal-HeatMap/d3, ô 10px, gap 2px, không bo góc, tuần bắt đầu thứ
> Hai, nhãn năm, nút ‹ ○ ›, tooltip div riêng).

### v2.1 Quyết định đã chốt (user xác nhận)

1. **Giao diện lấy cả 4 phần:** (a) ô vuông nhỏ sát nhau; (b) nhãn năm + nút điều hướng ‹ ○ ›;
   (c) dòng thống kê tô màu; (d) bảng màu theo **chủ đề** + độ đậm theo **streak**.
2. **Luồng note:** bấm **Check today = tick ngay, không hỏi gì**. Có nút nhỏ **Note** cạnh nút
   Check để thêm/sửa note của hôm nay bất cứ lúc nào trong ngày.
3. **Giới hạn note: 500 ký tự** (user đã được báo: tối đa ~180 KB/habit/năm nếu note mọi ngày, sync
   nặng hơn; thực tế thường nhỏ hơn nhiều).
4. **Tooltip hiện:** ngày đầy đủ + thứ, **trạng thái ngày**, **nội dung note**. (Không hiện vị trí
   trong chuỗi.)
5. Đồng bộ v1 đã được user xác nhận hoạt động ổn → **Task 12 của v1 đóng**.
6. **Xác nhận mặc định:** độ đậm theo streak 5 mức + chấm góc cho ô có note; một thanh điều hướng
   dùng chung.
7. **Đổi quy tắc note (user):** note **quá khứ vẫn thêm mới được** (để giải thích vì sao hôm đó
   Missed). Tick vẫn chỉ hôm nay.
8. **Kéo thả đổi thứ tự habit** trong phần cài đặt (Tools → Habit Heatmap...), thứ tự = **mức ưu
   tiên** (trên cùng = ưu tiên cao nhất, cũng là thứ tự hiện trên màn hình deck).

### v2.2 Thiết kế

**Lưới = năm lịch, không còn cửa sổ trượt 53 tuần.** Cột = tuần (thứ Hai đầu tuần), từ tuần chứa
1/1 đến tuần chứa 31/12 (53 hoặc 54 cột); ô ngoài năm không vẽ. Hiện **cả ngày tương lai** của năm
(tô xám đậm hơn, như ảnh Review Heatmap) thay vì ẩn. Ô là vuông cố định ~10px, gap 2px, không bo
góc, lưới canh giữa, `max-width` ≈ cột×12px và **co theo bề rộng** khi cửa sổ hẹp.

**Trạng thái ngày** (hàm thuần `day_status`, dùng cho cả màu ô lẫn tooltip):

| Điều kiện | Trạng thái | Màu ô |
|---|---|---|
| `ngày > hôm nay` | Upcoming | xám đậm (rgba 128,128,128,0.40) |
| `ngày == hôm nay`, đã tick | Done (today) | màu theme + viền |
| `ngày == hôm nay`, chưa tick | Today - not done yet | xám nhạt + viền |
| `ngày < ngày tạo habit` | Not started | xám rất nhạt (0.10) |
| quá khứ, đã tick | Done | màu theme theo streak |
| quá khứ, chưa tick | Missed | xám nhạt (0.22) |

**Theme + độ đậm theo streak.** 5 theme: `lime`, `olive`, `ice`, `magenta`, `flame` (tên theo Review
Heatmap), mỗi theme 5 mức đậm dần. Mức của một ô **Done** = độ dài đoạn tick liên tiếp kết thúc
tại ngày đó: `1 ngày → L1`, `2–3 → L2`, `4–6 → L3`, `7–13 → L4`, `≥14 → L5`. Ô có note có **chấm nhỏ**
ở góc (không làm đậm màu, để màu chỉ mang một nghĩa là streak). `Habit.color` chuyển nghĩa thành
**tên theme**; giá trị hex cũ của v1 được ánh xạ về theme theo thứ tự `PALETTE` cũ, không lọt
thì `lime` — **không ghi lại dữ liệu để migrate**, chỉ đổi cách đọc.

**Điều hướng.** Một thanh `‹ ○ ›` **dùng chung, đặt trên các khối** (như Review Heatmap), điều
khiển năm đang xem cho mọi habit. `‹` năm trước, `›` năm sau, `○` về năm hiện tại. Giới hạn: không
vượt quá năm hiện tại; không lùi quá năm tạo habit sớm nhất (nút mờ ở biên). Năm đang xem chỉ lưu
**trong bộ nhớ** (mặc định năm hiện tại mỗi lần mở Anki). Khi xem năm **không phải hiện tại**: ẩn
nút Check today / Note của hôm nay; **không** tick được; ô quá khứ vẫn bấm để thêm/sửa note. **Nhãn năm** hiện dưới lưới (chữ nhỏ, xám, canh giữa).

**Dòng thống kê tô màu, canh giữa:** `Current streak: N days   Longest streak: N days   Days done:
N (P%)`; nhãn chữ thường, **giá trị đậm và tô màu theme (mức đậm nhất)**. Thống kê luôn tính trên
toàn bộ lịch sử của habit (không phụ thuộc năm đang xem); `P%` giữ nghĩa v1 (từ ngày tạo đến hôm
nay).

**Note theo ngày.**
- Gắn với **ngày**, **độc lập với tick** (một ngày Missed vẫn có thể có note giải thích).
- Thêm/sửa/xoá được note của **hôm nay và mọi ngày quá khứ từ ngày tạo habit trở đi** (kể cả năm
  cũ khi đang xem năm khác). **Không** có note cho ngày tương lai hoặc ngày trước khi tạo habit.
  *(Mặc định tôi chọn: "thêm mới" cũng gồm sửa/xoá note đã có của ngày quá khứ — hạn chế lại nếu
  muốn note quá khứ chỉ viết một lần.)*
- Cách mở: **hôm nay** — nút **Note** ("Add note"/"Edit note") cạnh nút Check, luôn hiện khi xem
  năm hiện tại (không còn phụ thuộc đã tick hay chưa). **Ngày quá khứ** — **bấm vào ô** của ngày
  đó (con trỏ `pointer` ở các ô hợp lệ; ô hôm nay vẫn là tick/bỏ tick như v1).
- Hộp nhập nhiều dòng của Qt; text **không** đi qua JS/`pycmd`. Lệnh bridge:
  `habitheatmap:note:<habit_id>:<YYYY-MM-DD>`. Khác `toggle` (không mang ngày), lệnh này **có ngày**
  nên Python **kiểm chặt**: ISO hợp lệ, `ngày tạo habit <= ngày <= hôm nay` (hôm nay tính phía
  Python), habit tồn tại và chưa lưu trữ; sai → từ chối + tooltip Anki. Tick vẫn **không bao giờ**
  nhận ngày từ giao diện.
- Chuẩn hoá: bỏ khoảng trắng đầu/cuối, `\r\n` → `\n`, bỏ ký tự điều khiển, **cắt ở 500 ký tự** (báo
  bằng tooltip Anki "Note shortened to 500 characters"). Nội dung rỗng = xoá note.
- Bỏ tick **giữ nguyên note**.
- Lưu: key `habitHeatmap.n.<habit_id>` = `{"<date ordinal>": "text", ...}`. Chặn ghi thêm nếu JSON
  của key vượt **200 000 ký tự** (báo lỗi, không crash).
- Đồng bộ: thêm `notes`/`base_notes` vào shadow, gộp 3 chiều **theo từng ngày** (`merge_notes`:
  bên nào đổi so với base thì lấy bên đó; cả hai đổi thì remote thắng), cùng cơ chế `usn`/sync
  nối tiếp như bitmap. "Delete forever" xoá cả key note.

**Thứ tự habit = mức ưu tiên, kéo thả để đổi.** Trong Tools → Habit Heatmap...: kéo thả các dòng
(`QListWidget` chế độ `InternalMove`) để đổi thứ tự; mỗi dòng có **số ưu tiên** ("1.", "2.", ...)
chỉ đếm habit đang dùng; thả xong **lưu ngay** và màn hình deck cập nhật. Giữ nút Move up/down làm
phương án dùng bàn phím. Màn hình deck vẽ habit đang dùng theo đúng thứ tự này. Habit đã lưu
trữ hiện mờ, không đánh số.
**Thứ tự phải sync được:** `merge_habits` hiện luôn lấy thứ tự của remote nên một lần kéo thả bị
sync đè sẽ mất. Quy tắc mới: nếu thứ tự remote (sau khi lọc các id còn sống) **bằng** thứ tự của
base thì dùng thứ tự **local**; ngược lại dùng thứ tự remote (cả hai cùng đổi → remote thắng như
các trường khác); id mới thêm xếp cuối theo thứ tự xuất hiện.

**Tooltip tuỳ biến** (thay `title` mặc định, giống Review Heatmap). Nội dung:
```
Wednesday, 11 Nov 2026          (đậm)
Done today                      (trạng thái, theo bảng trên)
Ghi chú nhiều dòng của hôm nay  (chỉ khi có note, xuống dòng đúng như đã nhập)
Click to add a note             (chữ mờ; "Click to edit note" nếu đã có; chỉ ở ô hợp lệ)
```
Cách làm: mỗi ô mang `data-day`, `data-status`, `data-note`, `data-noteable`; **một** `<script>` nhỏ, idempotent
(`window.__hhInit`), dùng uỷ quyền sự kiện `mouseover/mouseout` trên `document`, dựng nội dung
bằng `textContent` (**không** `innerHTML` → note không thể chèn HTML/JS), đặt tooltip phía trên ô,
**lật xuống dưới/dịch ngang** khi sát mép, tôn trọng chế độ tối. Mỗi ô vẫn có `title` thuần làm
**phương án dự phòng**: script gỡ `title` khi khởi tạo thành công, nên nếu JS không chạy thì
tooltip mặc định của trình duyệt vẫn hiện (không bao giờ hiện hai tooltip).

**`<style>`/`<script>` giờ được phép** (đổi so với v1): CSP chặn script **chỉ áp dụng cho trang
Editor** (`aqt/mediasrv.py:75-83`, `:822-828`, `PageContext.EDITOR`) — đó là lý do `<style>`/
`<script>` bị loại khi paste ở tree-card-generator. **Màn hình deck không có CSP** [VERIFIED qua
source; còn phải chạy thử trong Anki thật, xem Risk-First]. Giới hạn: đúng **một** khối `<style>` và
**một** khối `<script>` cho cả trang (chèn một lần cho mỗi lần render), mọi class/id có tiền tố
`hh-`, không ghi đè style của Anki hay add-on khác, không phụ thuộc thư viện ngoài (không d3/CDN).

**Bridge.** Thêm `habitheatmap:note:<id>:<YYYY-MM-DD>` và `habitheatmap:nav:<prev|next|today>`; vẫn xử lý trong
`webview_did_receive_js_message`, chỉ khi `context` là `DeckBrowser`, id/tham số được kiểm bằng
regex an toàn, mọi lỗi được bắt (không lọt vào Anki).

### v2.3 Thay đổi code dự kiến

| Module | Thay đổi |
|---|---|
| `days.py` | `year_grid(year)` (lưới năm lịch, ô ngoài năm = None), `clamp_year` |
| `themes.py` *(mới)* | 5 theme × 5 mức, `streak_level(run)`, `resolve_theme(color)` (hex cũ → theme) |
| `stats.py` | thêm `streak_runs(ticked)` → độ dài đoạn liên tiếp tại mỗi ngày |
| `notes.py` *(mới)* | `clean_note`, `merge_notes`, `note_day_ok(day, created, today)`, hằng 500/200 000 |
| `render.py` | viết lại: `day_status`, thanh điều hướng, khối habit mới, dữ liệu ô |
| `assets.py` *(mới)* | chuỗi CSS + JS tooltip (thuần, test được bằng đọc chuỗi) |
| `store.py` | `note/set_note(habit, day, text, today)` (kiểm ngày), `delete_data` xoá cả note |
| `shadow.py`, `reconcile.py` | thêm notes vào shadow + gộp 3 chiều |
| `deckview.py` | lệnh `nav`, `note` (parse + kiểm ngày); trạng thái năm đang xem; chèn assets một lần |
| `manage_dialog.py` | chọn theme thay cho chọn hex; **kéo thả đổi thứ tự**, số ưu tiên |
| `merge3.py` | `merge_habits` gộp thứ tự (local nếu remote không đổi so với base) |

### v2.4 Chiến lược test

- **Unit (pytest, không cần Anki):** `year_grid` (năm nhuận, năm 1/1 rơi vào các thứ khác nhau →
  53/54 cột, ô ngoài năm), `streak_level`/`streak_runs` (ranh giới 1/2–3/4–6/7–13/14), `day_status`
  (đủ 6 trạng thái, ranh giới ngày tạo/hôm nay), `resolve_theme` (hex cũ), `clean_note` (cắt 500,
  `\r\n`, ký tự điều khiển, rỗng), `merge_notes` (một bên đổi, cả hai đổi, xoá), store note (hôm
  nay và quá khứ hợp lệ; từ chối ngày tương lai / trước ngày tạo / ISO sai / habit không tồn tại
  hoặc đã lưu trữ; vượt 200 000; giữ khi untick; xoá cùng habit), `merge_habits` thứ tự (local
  reorder khi remote không đổi; remote reorder; cả hai đổi; id mới/xoá chen vào),
  reconcile cho notes, `render` (HTML chỉ ô hôm nay có `onclick`; `data-*` đúng; note bị escape
  trong thuộc tính; có đúng 1 `<style>`/1 `<script>`; nút Check/Note ẩn khi xem năm khác; nút ‹ › mờ
  ở biên; `title` dự phòng), `assets` (JS dùng `textContent`, không `innerHTML`).
- **e2e sync (`e2e/e2e_sync.py`):** thêm kịch bản **đổi thứ tự habit lan sang máy kia** và note — thêm/sửa/xoá note lan hai chiều, hai máy
  sửa note **hai ngày khác nhau** (giữ cả hai), **cùng một ngày** (remote thắng), note qua
  "Download", note còn khi untick.
- **Manual trong Anki thật (profile test, có bằng chứng screenshot):** `<style>`/`<script>` chạy
  được ở màn hình deck; tooltip hiện đúng nội dung và không bị cắt ở mép; chế độ tối; cửa sổ
  hẹp; điều hướng năm; nút Check/Note; chấm note; **bấm ô quá khứ để thêm note**; **kéo thả đổi thứ tự** ở hộp
  cài đặt và thứ tự khối trên màn hình deck đổi theo.

### v2.5 Ranh giới (bổ sung)

- **Luôn làm:** ghi note qua Collection API; Python tự tính "hôm nay" cho tick và để kiểm ngày note; dựng
  tooltip bằng `textContent`; escape mọi note/tên khi đưa vào thuộc tính HTML; ẩn nút
  Check/Note của hôm nay khi xem năm khác.
- **Hỏi trước:** lưu note ngoài collection config (vd note Anki ẩn);
  lịch sử chỉnh sửa note; tăng giới hạn 500 ký tự; thêm thư viện JS ngoài.
- **Không bao giờ:** nhận **ngày cho tick** hoặc **nội dung note** từ JS/`pycmd` (ngày cho note
  thì nhận nhưng phải kiểm chặt như trên); cho note ngày tương lai; dùng `innerHTML` với dữ liệu
  người dùng; thêm CSS/JS chạm ra ngoài vùng `hh-`; tự xoá note.

### v2.6 Tiêu chí hoàn thành (bổ sung)

- Lưới là **năm lịch** với nhãn năm; ô vuông nhỏ sát nhau; ngày tương lai xám đậm; ô hôm nay có
  viền; nhìn cạnh Review Heatmap thấy cùng "phong cách".
- Bấm Check today **tick ngay không hỏi**; nút Note mở hộp nhập, lưu được, mở lại thấy note cũ; note
  quá 500 ký tự bị cắt và có báo.
- **Bấm một ô ngày quá khứ** (kể cả ở năm khác) mở hộp note và lưu được; ngày tương lai / trước ngày
  tạo không mở; tick quá khứ vẫn **không thể**.
- Kéo thả trong Tools → Habit Heatmap... đổi thứ tự ngay, có số ưu tiên, màn hình deck theo thứ tự
  đó, và thứ tự **đồng bộ** sang máy kia.
- Rê chuột vào **bất kỳ ô nào** hiện tooltip đúng: ngày + thứ, trạng thái (đủ 6 loại), note nếu có.
- Độ đậm ô Done đổi theo độ dài chuỗi; ô có note có chấm; đổi theme trong Tools → Habit Heatmap
  có hiệu lực ngay.
- `‹ ○ ›` đổi năm đúng, không tick được ở năm khác, không vượt biên; thống kê không đổi theo năm đang xem.
- Note đồng bộ giữa hai máy (kể cả sửa hai ngày khác nhau cùng lúc); e2e mới + toàn bộ test cũ pass.

### v2.7 Risk-First (làm trước khi viết phần còn lại)

1. **Spike trong Anki thật:** chèn 1 khối `<style>` + 1 `<script>` + vài ô có `data-*` vào màn hình
   deck, kiểm tra script chạy, tooltip hiện khi rê chuột, đúng ở chế độ tối và cửa sổ hẹp. Nếu
   **không** chạy được → phương án dự phòng đã có sẵn: dùng `title` mặc định (bỏ tooltip tuỳ biến),
   phần còn lại của v2 không đổi.
2. Kích thước thật của dữ liệu note (500 ký tự × nhiều ngày) và thời gian sync — đo bằng e2e với
   server cục bộ.

### v2.8 Mặc định tôi đã chọn thay user (đổi lại nếu không hợp)

- "Thêm mới note quá khứ" gồm cả **sửa/xoá** note đã có của ngày quá khứ.
- Note không cần đã tick; nút Note của hôm nay luôn hiện ở năm hiện tại.
- Bấm ô quá khứ = mở note; bấm ô hôm nay = tick/bỏ tick (như v1).
- Kéo thả giữ cả nút Move up/down; habit đã lưu trữ không đánh số ưu tiên.
- Nhãn giao diện tiếng Anh, ngày dạng `Wednesday, 11 Nov 2026`; không có nhãn tháng trên lưới.

### v2.9 Kết quả xác minh khi xây (autopilot)

- **Unit:** 308 test pass (thuần Python, không cần Anki).
- **Giao diện thật trong Chromium** (cùng engine với QtWebEngine của Anki): lưới năm, 4 theme, màu
  đậm dần theo streak, chấm note, ô hôm nay có viền, ngày tương lai xám đậm, tooltip (ngày, trạng
  thái, note nhiều dòng, dòng gợi ý) và `<script>` idempotent chạy đúng.
- **Mô phỏng với `aqt` 25.9.4 + Qt thật (offscreen), 31 bước:** kéo thả thật qua model của
  `QListWidget` (`moveRow` → `rowsMoved`) lưu đúng thứ tự và đánh số lại; lệnh `toggle/note/nav` qua hook
  thật; ngày tương lai / trước ngày tạo / ISO sai / habit lạ / lệnh dị dạng đều bị từ chối; huỷ hộp
  thoại giữ nguyên note; note > 500 ký tự bị cắt + báo; điều hướng năm bị kẹp ở biên; xoá hẳn xoá cả
  key note; lỗi render/lệnh không lọt ra ngoài.
- **e2e sync 27/27** (collection thật + `anki.syncserver` cục bộ): gồm note và thứ tự habit. e2e
  bắt được một lỗi: khi chưa có `base` (sync lần đầu), điều kiện "thứ tự remote không đổi" luôn đúng
  một cách vô nghĩa nên máy kia giữ thứ tự cũ rồi đẩy ngược lại → sửa: chưa có `base` thì tin thứ tự
  remote.
- **Chưa xác nhận trong Anki thật:** `<style>`/`<script>` chạy ở màn hình deck, tooltip ở chế độ tối
  / cửa sổ hẹp, kéo thả bằng chuột thật. Cần user restart Anki (Task V2-10).

---

## v1 — Quyết định kiến trúc quan trọng (đọc trước khi code)

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

### 4. Đồng bộ & chống mất chuỗi  *(viết lại sau khi đo trên Anki thật — xem `e2e/e2e_sync.py`)*

**Hành vi thật của sync config, đo bằng 2 collection thật + `anki.syncserver` cục bộ [VERIFIED]:**
- Config đi theo sync, nhưng **Anki thay cả khối config** theo bên "mới hơn": khi hai máy cùng sửa
  trước lúc sync, máy sync sau **mất thay đổi chưa sync** (cả key khác của add-on khác trong khối).
- Một thay đổi chỉ thắng nếu **không máy nào khác sync (kể cả sync không đổi gì) kể từ lúc nó được
  ghi**. `mtime` chỉ chính xác tới giây.
- Mỗi dòng config có `usn`: `-1` ngay sau khi ghi, `>= 0` sau sync thành công, **vẫn `-1` nếu sync
  lỗi**. Đây là cách biết một giá trị đã thật sự được đồng bộ.
- Hook `sync_did_finish` **vẫn chạy khi sync lỗi** (`aqt/sync.py:115`), nên không dùng nó để suy
  ra "đã sync xong".

**Hệ quả với bản đầu (union):** union chỉ thêm, không có khái niệm "bỏ" → bỏ tick không bao giờ
lan sang máy kia và bị hồi sinh. Đã bỏ.

**Thiết kế hiện tại — gộp 3 chiều (`merge3.py`, `reconcile.py`):**
- Shadow local (`user_files/shadow-<profile>-<hash>.json`, **mỗi profile 1 file** vì `user_files/` dùng
  chung mọi profile) giữ `local` (máy này vừa ghi gì) và `base` (giá trị cuối cùng **đã xác nhận
  sync**, tức `usn != -1`).
- Sau mỗi sync / khi mở profile: `kết quả = (L ∩ R) ∪ (L − B) ∪ (R − B)` cho tick (thêm từ bên nào
  cũng giữ, bỏ từ bên nào cũng lan); habit list gộp theo id (bên kia xoá thì xoá, đổi tên/lưu trữ
  bên kia thì nhận, cả hai sửa thì bản remote thắng).
- `base` chỉ tiến lên khi giá trị đã `usn != -1` và merge không phải ghi gì → sync lỗi không làm
  `base` sai.
- **Sync nối tiếp tự động**: nếu merge phải ghi lại config thì add-on sync thêm 1 lần ngay sau 1.5s
  (`mw.on_sync_button_clicked()`), vì không có nó bản gộp dễ bị máy kia đè lại (đo: 4/15 kịch bản
  hỏng nếu thiếu). Giới hạn tối thiểu 60s giữa 2 lần để không bao giờ lặp vô hạn.
- **Không tự xoá dữ liệu**: key `d.<id>` không còn habit chỉ bị bỏ qua. "Delete forever" xoá và
  lan sang máy khác qua merge (không còn tombstone).
- Máy mới "Download from AnkiWeb": shadow rỗng → nhận nguyên dữ liệu remote. Thay đổi chưa sync
  trên máy hiện tại bị Download đè vẫn được khôi phục từ shadow.
- Bỏ tick hôm nay: cho phép và **lan được** (khác bản đầu).

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
   **collection config** (`habitHeatmap.habits`) để đi theo sync. Không dùng `config.json`. *(v2: `Habit.color` giờ là tên theme.)*
2. **Bỏ tick hôm nay:** **cho phép**. Giới hạn đã biết (union có thể hồi sinh tick đã bỏ nếu máy
   khác vừa sync tick cùng ngày) được chấp nhận.
3. **Cửa sổ hiển thị:** **53 tuần** (đủ 1 năm, như ảnh tham chiếu), cố định ở v1. *(v2: thay bằng năm lịch có điều hướng ‹ ○ ›.)*
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
