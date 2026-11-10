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

- Lưu trong **collection config** của Anki → đi theo sync AnkiWeb. Mỗi habit chỉ vài trăm byte
  (bitmap, 1 bit/ngày), vì config không nên phình quá vài KB.
- Anki sync config bằng cách **thay cả khối** theo máy "mới hơn", nên nếu hai máy cùng sửa trước
  khi sync, máy sync sau có thể mất thay đổi. Add-on giữ **bản shadow riêng mỗi profile**
  (`user_files/shadow-<profile>-<hash>.json`) gồm "bản trên máy này" và "bản gốc đã xác nhận sync",
  rồi **gộp 3 chiều** sau mỗi sync: tick thêm từ bên nào cũng giữ, **tick bỏ từ bên nào cũng lan
  sang máy kia**, đổi tên/lưu trữ/xoá habit cũng lan.
- Nếu phải ghi lại bản gộp, add-on **tự sync thêm một lần** ngay sau đó để đẩy nó lên (tối đa 1 lần
  / 60 giây).
- Đã kiểm chứng bằng `e2e/e2e_sync.py` (collection thật + server sync cục bộ của Anki): thêm/bỏ
  tick hai chiều, hai máy cùng tick offline, một bên bỏ một bên thêm, sync lỗi, máy mới Download,
  đổi tên/lưu trữ/xoá habit, và Download đè lên tick chưa sync — 15/15.
- **Add-on không bao giờ tự xoá dữ liệu.** Chỉ "Delete forever" mới xoá.

### Giới hạn đã biết

- Chỉ chạy trên **Anki desktop**; AnkiDroid/AnkiMobile không hiện heatmap (dữ liệu vẫn đi theo sync).
- Không chặn được việc chỉnh đồng hồ máy để tick ngày khác — công cụ cá nhân, không chống gian lận.
- Khi hai máy cùng thay đổi, cần 2 lần sync (add-on tự làm lần thứ hai) mới thấy hai máy giống nhau.
- Hai máy cùng sửa **một habit** (đổi tên khác nhau): bản của máy sync trước thắng.
- Anki gọi `sync_did_finish` cả khi sync lỗi; add-on đã tính tới, nhưng tick vẫn chỉ tới máy kia
  khi một lần sync thật sự thành công.

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
