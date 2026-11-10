# Habit Heatmap

Add-on Anki: trên màn hình danh sách deck, mỗi **habit** là một khối heatmap kiểu GitHub (53 tuần,
mỗi ô một ngày). Khác *Review Heatmap*: không tự cập nhật từ việc ôn thẻ — bạn **tự tick** mỗi
ngày như các app habit-tracker, và dữ liệu đồng bộ theo tài khoản AnkiWeb để không mất chuỗi.

## Cách dùng

1. **Tools → Habit Heatmap...** → **Add** để thêm habit (đặt tên). Khối heatmap hiện ngay dưới bảng
   deck.
2. Bấm **Check today** (hoặc bấm ô hôm nay) để tick. Bấm lại để bỏ tick nhầm.
3. Mỗi khối có dòng thống kê: **Current streak**, **Longest streak**, **Days done** (+ %).
4. Cùng cửa sổ quản lý: đổi tên, đổi màu, lên/xuống, **Archive / Restore**, **Delete forever**.

### Quy tắc tick

- **Chỉ tick được hôm nay.** Ô quá khứ chỉ đọc. "Hôm nay" theo **ngày của Anki** (tôn trọng
  "next day starts at"), không theo đồng hồ hệ thống: 2 giờ sáng vẫn tính là ngày hôm trước nếu
  Anki chưa sang ngày mới. Nút bấm không mang theo ngày nào — Python tự tính, nên không thể tick
  quá khứ qua giao diện.
- **Hôm nay chưa tick không làm đứt chuỗi**: Current streak đếm tới hôm qua cho đến khi qua hết ngày.
- **Archive** ẩn habit khỏi màn hình nhưng **giữ nguyên lịch sử** (khôi phục được). **Delete forever**
  xoá hẳn habit và lịch sử, có hộp xác nhận, không hoàn tác.

## Dữ liệu & đồng bộ

- Lưu trong **collection config** của Anki → đi theo sync AnkiWeb (Anki docs: config được gửi mỗi
  lần sync). Mỗi habit chỉ ~vài trăm byte (bitmap, 1 bit/ngày), vì config không nên phình quá vài KB.
- **Shadow local** (`user_files/shadow-<profile>-<hash>.json`, mỗi profile 1 file) là bản sao lưu
  trên máy. Sau khi mở profile và sau mỗi lần sync, add-on **gộp (union)** config với shadow: tick là
  tập chỉ-tăng nên không mất tick nào. Nhờ vậy nếu một lần sync hoặc "Download from AnkiWeb" ghi
  đè config bằng dữ liệu cũ, tick và habit được khôi phục từ shadow ở lần mở/sync kế tiếp.
- **Add-on không bao giờ tự xoá dữ liệu.** Chỉ "Delete forever" mới xoá (và ghi tombstone để không bị
  khôi phục lại).

### Giới hạn đã biết

- Chỉ chạy trên **Anki desktop**; AnkiDroid/AnkiMobile không hiện heatmap (dữ liệu vẫn đi theo sync).
- Không chặn được việc chỉnh đồng hồ máy để tick ngày khác — công cụ cá nhân, không chống gian lận.
- Bỏ tick hôm nay trên một máy trong lúc máy khác vừa sync tick cùng ngày có thể làm tick "hồi sinh"
  (do union). Hiếm gặp, chấp nhận.
- "Delete forever" trên máy A: nếu máy B còn bản shadow cũ của habit đó, B có thể khôi phục lại
  habit ở lần reconcile kế tiếp.
- Cách Anki **gộp config khi hai máy cùng sửa** (theo từng key hay cả khối) nằm trong backend Rust,
  chưa kiểm chứng — thiết kế shadow + union được làm để đúng với cả hai khả năng.

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

Logic thuần (không import `aqt`): `days`, `bitmap`, `stats`, `render`, `habits`, `store` (nhận
`col` kiểu duck-typing), `shadow`, `reconcile`. Chạm `aqt`: `__init__`, `context`, `deckview`,
`manage_dialog`.
