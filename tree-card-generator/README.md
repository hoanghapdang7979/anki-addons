# Tree Card Generator

Add-on Anki: dán text dạng cây ASCII (`├──`/`│`/`└──`) vào 1 dialog, bấm **Generate** → tự động
dịch thành thẻ HTML có thể bấm mở/thu gọn từng nhánh, **ghi thẳng vào field đang focus** — không
cần copy/paste tay.

## Cách dùng

1. Mở **Add Cards** hoặc **Browse** (bất kỳ màn hình nào có Editor).
2. **Click vào field muốn điền TRƯỚC** (quan trọng — add-on ghi vào field cuối cùng bạn đã focus).
3. Trong thanh công cụ của Editor, bấm nút **Tree Card**.
4. Dán text dạng cây vào ô nhập, ví dụ:

   ```
   Tiêu đề gốc
   ├── 1. Mục lớn thứ nhất
   │   ├── [00:03:04] Mục con có timestamp
   │   │   ├── Chi tiết A
   │   │   └── Chi tiết B
   │   └── Mục con khác
   └── 2. Mục lớn thứ hai
       └── ...
   ```

5. Bấm **Generate** — HTML xuất hiện thẳng trong field đã click ở bước 2, không cần Ctrl+V.
6. Kết quả: mục có mục con hiện dạng có thể bấm tiêu đề để mở/thu gọn (mặc định thu gọn hết);
   mục không có con hiện dạng bullet "–" đơn giản; dòng có tiền tố `[hh:mm:ss]` tách riêng phần
   giờ thành nhãn nhỏ màu xám trước nội dung.

## Cú pháp tree được hỗ trợ

- Thụt lề đúng **4 ký tự mỗi cấp** (`"│   "` hoặc `"    "`) + marker `"├── "`/`"└── "`.
- Dòng chỉ chứa `"│"` (dòng trống ngăn cách giữa các block) tự động bị bỏ qua.
- Tiền tố `[hh:mm:ss] ` ở đầu label (tuỳ chọn) được tách riêng làm timestamp.
- **Chưa hỗ trợ**: thụt lề bằng tab, hoặc ký tự tree khác ngoài `├──`/`│`/`└──`.

## Vì sao ghi thẳng vào field, không copy/paste?

Đã thử 2 hướng dựa trên clipboard trước khi chốt cách này, cả 2 đều thất bại vì Anki/Qt WebEngine
strip nội dung khi paste vào field:

1. HTML dùng `<style>`+`<script>` nhúng — bị strip toàn bộ `<style>`/`<script>`, dán ra chỉ còn
   text phẳng.
2. HTML dùng inline `style="..."` + `<details>`/`<summary>` thuần — vẫn bị strip: `<details>`/
   `<summary>` biến mất hoàn toàn, các CSS layout (`margin`/`padding`/`background`/`cursor`/
   `border-radius`) cũng bị bóc khỏi inline style, chỉ `color` và thẻ `<div>`/`<span>` sống sót.

Đây là giới hạn ở tầng sanitize paste-vào-contenteditable của Chromium/Qt WebEngine, không sửa
được bằng cách đổi HTML/CSS. Giải pháp: bỏ paste hoàn toàn, ghi thẳng vào `note.fields[...]` của
note đang mở trong Editor rồi refresh hiển thị (`editor.loadNote()`) — sanitize chỉ áp dụng lúc
paste, không áp dụng khi field content được set trực tiếp qua Python.

## Vì sao HTML chỉ dùng inline `style`, không có `<style>`/`<script>`?

Dù không còn qua paste nữa, add-on vẫn giữ giới hạn này để HTML tự chứa hoàn toàn — dán/ghi được
vào field của bất kỳ note type nào mà không cần setup Card Template riêng.

Xem chi tiết đầy đủ 3 vòng đổi kiến trúc trong [SPEC.md](./SPEC.md) mục "Đổi kiến trúc lúc build".

## Dev

Xem [SPEC.md](./SPEC.md) và [tasks/plan.md](./tasks/plan.md) cho spec/kiến trúc đầy đủ.

```bash
cd tree-card-generator
python -m venv .venv
.venv/Scripts/pip install pytest
.venv/Scripts/pip install -r requirements.txt   # pin đúng version Anki thật đang cài

cd tests
../.venv/Scripts/python -m pytest . -v
```
