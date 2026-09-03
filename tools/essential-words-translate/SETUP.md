# Setup: Google Cloud Translation API

> Các bước dưới đây bạn tự làm trên trình duyệt (đăng nhập Google, bật billing, tạo key) — tôi
> không có quyền tạo tài khoản hay nhập thông tin thanh toán giúp bạn. Sau khi có file key JSON,
> báo tôi để tiếp tục `/planning`.

## 1. Tạo Google Cloud Project

1. Vào https://console.cloud.google.com/ (đăng nhập bằng Google account của bạn).
2. Góc trên bên trái, bấm dropdown project → **New Project**.
3. Đặt tên bất kỳ (vd `essential-words-translate`) → **Create**.
4. Chờ vài giây, chọn đúng project vừa tạo trong dropdown.

## 2. Bật billing (bắt buộc — Translation API không cho dùng nếu chưa bật billing)

1. Menu ☰ → **Billing** → **Link a billing account**.
2. Nếu chưa có billing account, tạo mới (cần thẻ thanh toán — Google thường có free trial credit
   cho tài khoản mới, nhưng khối lượng dịch ~1.27 triệu ký tự của bạn **sẽ vượt free tier** của
   riêng Translation API là 500,000 ký tự/tháng, nên chắc chắn phát sinh phí thật ở phần vượt).
3. Link billing account vào đúng project vừa tạo ở bước 1.

## 3. Bật Cloud Translation API

1. Menu ☰ → **APIs & Services** → **Library**.
2. Tìm **"Cloud Translation API"** → chọn đúng project → **Enable**.

## 4. Tạo Service Account + key JSON

1. Menu ☰ → **APIs & Services** → **Credentials**.
2. **Create Credentials** → **Service account**.
3. Đặt tên bất kỳ (vd `translate-runner`) → **Create and Continue**.
4. Ở bước "Grant this service account access to project", chọn role **Cloud Translation API
   User** (đủ quyền gọi API, không cần quyền admin rộng hơn) → **Continue** → **Done**.
5. Trong danh sách Service Accounts, click vào account vừa tạo → tab **Keys** → **Add Key** →
   **Create new key** → chọn **JSON** → **Create**.
6. File JSON key tự động tải về máy (vd `essential-words-translate-xxxxx.json`).

## 5. Đặt key vào đúng chỗ trong repo

```bash
mkdir -p "C:\Users\Client\Desktop\anki-addons\tools\essential-words-translate\secrets"
```

Copy file JSON vừa tải về vào đúng thư mục đó, đổi tên thành `gcloud-key.json` (khớp path mặc
định trong `SPEC.md` → Commands):

```
tools/essential-words-translate/secrets/gcloud-key.json
```

Thư mục `secrets/` đã nằm trong `.gitignore` chung của repo — file key **sẽ không bao giờ bị
commit**, nhưng vẫn nên tự kiểm tra lại bằng lệnh sau trước khi commit bất kỳ thứ gì trong lúc
implement:

```bash
git status --short tools/essential-words-translate/
```

→ nếu thấy `secrets/gcloud-key.json` xuất hiện trong danh sách (không phải trạng thái ignored),
**dừng lại báo tôi ngay** — nghĩa là gitignore chưa match đúng, chưa an toàn để commit.

## 6. Kiểm tra key hoạt động (tuỳ chọn, làm nhanh trước khi vào code thật)

```bash
cd tools/essential-words-translate
python -m venv .venv
.venv/Scripts/pip install google-cloud-translate

.venv/Scripts/python -c "
from google.cloud import translate_v2 as translate
client = translate.Client.from_service_account_json('secrets/gcloud-key.json')
result = client.translate('你好', target_language='vi', source_language='zh')
print(result['translatedText'])
"
```

Nếu in ra `Xin chào` (hoặc tương đương) → key hoạt động đúng, sẵn sàng cho `/planning`.

## Chi phí cần biết trước

- Free tier: 500,000 ký tự/tháng cho Cloud Translation API (Basic, v2/v3).
- Khối lượng job này: ~1.27 triệu ký tự → **vượt free tier ~770,000 ký tự**.
- Giá sau free tier (cần tự verify tại https://cloud.google.com/translate/pricing vì giá có thể
  đổi theo thời gian, không dựa vào số cụ thể tôi ước tính trước đó) — ước tính sơ bộ trước đây
  là ~20-25 USD, **chỉ mang tính tham khảo, không phải giá cam kết**.
- Đúng theo Boundaries trong SPEC.md: script sẽ luôn chạy `--limit 10` (dịch ~vài trăm ký tự,
  gần như miễn phí) để bạn xác nhận chất lượng **trước khi** chạy full job tốn phí thật.
