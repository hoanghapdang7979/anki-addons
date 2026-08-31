# Anki Add-ons

Repo tổng hợp các add-on (plugin Python) cho [Anki](https://apps.ankiweb.net/), ứng dụng
flashcard spaced-repetition.

**Status:** Mới khởi tạo, chưa có add-on nào. Xem [CLAUDE.md](./CLAUDE.md) cho quy ước phát
triển đầy đủ (cấu trúc `manifest.json`, hook system, packaging...).

## Cấu trúc repo

Mỗi add-on là một thư mục top-level riêng, tự chứa `manifest.json` + `__init__.py` — Anki load
mỗi thư mục như một add-on độc lập:

```
anki-addons/
  CLAUDE.md
  README.md
  docs/                    # Ghi chú/spec cho từng add-on (nếu cần)
  <ten-addon-1>/
    manifest.json
    __init__.py
    config.json             # (tuỳ chọn) default user config
    config.md                # (tuỳ chọn) mô tả config, hiển thị trong Anki
  <ten-addon-2>/
    manifest.json
    __init__.py
    ...
```

`meta.json` (config runtime + trạng thái enable của mỗi add-on) do Anki tự sinh khi chạy —
không hand-author, không commit (đã có trong `.gitignore`).

## Local testing

Symlink hoặc copy thư mục add-on vào profile folder của Anki, rồi khởi động lại Anki:

```bash
# Windows
mklink /D "%APPDATA%\Anki2\addons21\<ten-addon>" "C:\Users\Client\Desktop\anki-addons\<ten-addon>"
```

Tools → Add-ons → chọn add-on → **View Files** mở thẳng thư mục đó trong `addons21/` để kiểm
tra add-on đã load đúng.

## Packaging

Add-on phân phối dưới dạng file `.ankiaddon` — zip nội dung thư mục add-on (không zip cả thư
mục cha) ở root của file zip, gồm `manifest.json`, loại bỏ `__pycache__/` và `meta.json`.

```bash
cd <ten-addon>
zip -r ../<ten-addon>.ankiaddon . -x "__pycache__/*" "meta.json"
```

File `.ankiaddon` là build artifact, không commit vào repo (đã có trong `.gitignore`).

## Quy ước code

- Ưu tiên `aqt.gui_hooks` / `anki.hooks` thay vì monkey-patch trực tiếp.
- Add-on chỉ xử lý dữ liệu (không đụng UI) nên tránh import `aqt` — giữ testable không cần Qt.
- Package (`manifest.json` → `package`) phải là ID số của AnkiWeb khi đã publish, hoặc string
  duy nhất cho add-on local-only.

Chi tiết đầy đủ: xem [CLAUDE.md](./CLAUDE.md).
