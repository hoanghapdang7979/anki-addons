# Habit Heatmap

Add-on Anki: trên màn hình danh sách deck, mỗi **habit** là một khối heatmap kiểu *Review Heatmap*
(lưới **năm lịch**, ô vuông nhỏ sát nhau, tuần bắt đầu thứ Hai). Khác Review Heatmap: không tự cập
nhật từ việc ôn thẻ — bạn **tự tick** mỗi ngày như các app habit-tracker, có thể **ghi note** cho
từng ngày, rê chuột vào ô để xem **tooltip**, và dữ liệu đồng bộ theo tài khoản AnkiWeb để không
mất chuỗi.

## Cách dùng

1. **Tools → Habit Heatmap...** → **Add** để thêm habit (đặt tên). Khối heatmap hiện ngay dưới bảng
   deck.
2. Bấm **Check today** (hoặc bấm ô hôm nay) để tick — tick ngay, không hỏi gì. Bấm lại để bỏ tick nhầm.
3. **Note:** bấm nút **Add note / Edit note** cạnh nút Check để ghi chú cho hôm nay. Muốn ghi chú
   cho **một ngày đã qua** (vd giải thích vì sao hôm đó Missed) thì **bấm vào ô của ngày đó**. Tối đa
   500 ký tự, để trống rồi lưu = xoá note. Ô có note hiện một **chấm nhỏ** ở góc.
4. **Tooltip:** rê chuột vào bất kỳ ô nào để xem ngày đầy đủ + thứ, trạng thái
   (`Done` / `Done today` / `Today - not done yet` / `Missed` / `Not started` / `Upcoming`) và note
   của ngày đó.
5. **‹ ○ ›** phía trên các khối: xem năm trước / về năm hiện tại / năm sau. Hai mũi tên **luôn bấm
   được** (từ năm 2000 đến 2100), kể cả khi mọi habit mới tạo năm nay. Năm khác chỉ để xem (không
   tick được); năm tương lai toàn ô Upcoming; vẫn thêm được note cho các ngày đã qua từ ngày tạo habit.
6. Mỗi khối có dòng thống kê tô màu: **Current streak**, **Longest streak**, **Days done** (+ %).
7. Trong **Tools → Habit Heatmap...**: đổi tên, **chọn theme màu** (12 theme: lime, olive, ice, magenta,
   flame, teal, purple, crimson, gold, indigo, rose, slate; hộp chọn tô đúng màu từng theme), **kéo thả để đổi thứ tự** (thứ tự = mức ưu tiên, trên cùng = cao nhất, có đánh số;
   cũng là thứ tự các khối trên màn hình deck), **Archive / Restore**, **Delete forever**.

### Quy tắc

- **Tick chỉ hôm nay.** Ô quá khứ không tick được. "Hôm nay" theo **ngày của Anki** (tôn trọng
  "next day starts at"), không theo đồng hồ hệ thống: 2 giờ sáng vẫn tính là ngày hôm trước nếu
  Anki chưa sang ngày mới. Lệnh tick không mang theo ngày nào — Python tự tính.
- **Note** thêm/sửa/xoá được cho hôm nay và mọi ngày quá khứ **từ ngày tạo habit** trở đi (không có
  cho ngày tương lai). Note độc lập với tick; bỏ tick **giữ nguyên** note. Lệnh note có kèm ngày
  nhưng Python kiểm chặt (ISO hợp lệ, trong khoảng [ngày tạo, hôm nay], habit còn dùng); nội dung
  note luôn nhập qua hộp thoại của Qt, không đi qua trang web.
- **Màu ô Done** đậm dần theo độ dài chuỗi tick liên tiếp kết thúc tại ngày đó: 1 / 2–3 / 4–6 /
  7–13 / từ 14 ngày. Ô xám: Missed (nhạt), Not started (rất nhạt), Upcoming (đậm hơn).
- **Hôm nay chưa tick không làm đứt chuỗi**: Current streak đếm tới hôm qua cho đến khi qua hết ngày.
- **Archive** ẩn habit khỏi màn hình nhưng **giữ nguyên lịch sử và note** (khôi phục được).
  **Delete forever** xoá hẳn habit, lịch sử và note, có hộp xác nhận, không hoàn tác.

## Dữ liệu & đồng bộ

- Lưu trong **collection config** của Anki → đi theo sync AnkiWeb: danh sách habit (kèm thứ tự), một
  bitmap tick mỗi habit (1 bit/ngày, vài trăm byte) và một key note mỗi habit (tối đa 500 ký tự /
  note, tối đa 200 000 ký tự / habit; vượt thì báo và không ghi).
- Anki sync config bằng cách **thay cả khối** theo máy "mới hơn", nên nếu hai máy cùng sửa trước
  khi sync, máy sync sau có thể mất thay đổi. Add-on giữ **bản shadow riêng mỗi profile**
  (`user_files/shadow-<profile>-<hash>.json`) gồm "bản trên máy này" và "bản gốc đã xác nhận sync",
  rồi **gộp 3 chiều** sau mỗi sync: tick/note thêm từ bên nào cũng giữ, **bỏ tick / xoá note từ bên
  nào cũng lan sang máy kia**, đổi tên / lưu trữ / xoá / **đổi thứ tự** habit cũng lan. Note được gộp
  **theo từng ngày**; cùng một ngày sửa ở cả hai máy thì bản của máy sync trước thắng.
- Nếu phải ghi lại bản gộp, add-on **tự sync thêm một lần** ngay sau đó để đẩy nó lên (tối đa 1 lần
  / 60 giây).
- Đã kiểm chứng bằng `e2e/e2e_sync.py` (collection thật + server sync cục bộ của Anki): tick/bỏ
  tick/note hai chiều, hai máy cùng sửa offline, sync lỗi, máy mới Download, Download đè lên thay
  đổi chưa sync, đổi tên/lưu trữ/xoá habit, đổi thứ tự — 27/27.
- **Add-on không bao giờ tự xoá dữ liệu.** Chỉ "Delete forever" mới xoá.

### Giao diện & tooltip

- Màn hình deck của Anki không có Content-Security-Policy (chỉ trang Editor có), nên add-on chèn
  đúng **một** khối `<style>` và **một** khối `<script>` (mọi class có tiền tố `hh-`). Tooltip dựng
  bằng `textContent` nên note không thể chèn HTML/JS. Mỗi ô vẫn có `title` thuần làm **phương án
  dự phòng**: script gỡ `title` khi chạy được; nếu JS không chạy thì tooltip mặc định của trình
  duyệt vẫn hiện.

### Giới hạn đã biết

- Chỉ chạy trên **Anki desktop**; AnkiDroid/AnkiMobile không hiện heatmap (dữ liệu vẫn đi theo sync).
- Không chặn được việc chỉnh đồng hồ máy để tick ngày khác — công cụ cá nhân, không chống gian lận.
- Khi hai máy cùng thay đổi, cần 2 lần sync (add-on tự làm lần thứ hai) mới thấy hai máy giống nhau.
- Hai máy cùng sửa **một habit** (đổi tên khác nhau) hoặc cùng đổi thứ tự: bản của máy sync trước thắng.
- Anki gọi `sync_did_finish` cả khi sync lỗi; add-on đã tính tới, nhưng thay đổi vẫn chỉ tới máy
  kia khi một lần sync thật sự thành công.
- Giao diện bằng tiếng Anh; không có nhãn tháng trên lưới (Review Heatmap chế độ năm cũng không có).

## Dev

Xem [SPEC.md](./SPEC.md) và [tasks/plan.md](./tasks/plan.md).

```bash
cd habit-heatmap
python -m venv .venv
.venv/Scripts/pip install pytest
.venv/Scripts/pip install -r requirements.txt   # aqt==25.9.4 anki==25.9.4 (đúng bản Anki đang dùng)

# Chạy từ trong tests/ (tên thư mục có dấu gạch ngang + __init__.py làm pytest vỡ import nếu chạy từ gốc)
cd tests
../.venv/Scripts/python -m pytest . -v
```

Logic thuần (không import `aqt`): `days`, `bitmap`, `stats`, `themes`, `notes`, `render`, `assets`,
`habits`, `merge3`, `store` (nhận `col` kiểu duck-typing), `shadow`, `reconcile`. Chạm `aqt`:
`__init__`, `context`, `deckview`, `manage_dialog`. Kiểm sync end-to-end: xem đầu file
`e2e/e2e_sync.py`.
