## field_name

Tên field sẽ tự động điền danh sách habit khi note mới được tạo. Note type nào có field trùng
tên này thì tự điền — chỉ điền nếu field đang trống, không bao giờ ghi đè nội dung đã có (kể cả
nội dung trông giống checklist cũ đã tick/ghi chú).

## habits

Danh sách tên habit, mỗi habit sẽ thành 1 dòng `[ ] Tên habit` trong field. Điền danh sách này
**trước khi** tạo note đầu tiên để không bị bỏ lỡ. Ví dụ:

```json
"habits": ["Exercise", "Read", "Meditate"]
```

Sau khi note đã tạo, tick hoàn thành bằng cách tự gõ đè `[ ]` thành `[x]`, và có thể gõ thêm ghi
chú ngay sau tên habit trên cùng dòng.
