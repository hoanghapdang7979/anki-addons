---
description: Autopilot mode cho anki-addons — gộp quyền tự commit/push lên nhánh feature, tự thực hiện task với self-verify (chạy test, kiểm tra add-on import/load được), tự dùng terminal/pytest/zip packaging trong phạm vi project. KHÔNG override các hard-stop trong CLAUDE.md (không đụng Anki/collection thật của user, không push thẳng main, không force push).
---

# Autopilot

Khi user gọi `/autopilot <task hoặc tên add-on>`, coi đây là user chủ động cấp các quyền mở rộng
sau **cho lần gọi này** (không phải standing permission vĩnh viễn — mỗi lần gọi lại là một lần cấp
quyền mới, đúng nguyên tắc "authorization theo scope, không tự suy rộng").

Repo này chưa có spec chính hay workflow `/spec → /ba → /planning` bắt buộc (khác các dự án lớn
hơn) — autopilot ở đây nghĩa là: **tự thực hiện task được giao trực tiếp, tự verify, tự commit
theo nhánh feature**, không cần dừng hỏi giữa các bước nhỏ.

## Quyền được cấp

1. **Tự commit + push** lên nhánh feature tương ứng — không cần hỏi từng lần. Vẫn theo format
   `<type>(<ten-addon>): <mô tả>` (Git workflow trong CLAUDE.md), mỗi task 1 commit riêng.
   KHÔNG push/commit thẳng vào `main`. Không bao giờ force push (áp dụng dù đang autopilot).
   Việc gọi `/autopilot` mỗi lần được coi là user đã confirm cho lần chạy đó — ghi đè rule
   "không tự động git commit/push" trong CLAUDE.md **chỉ cho session này**.
2. **Tự thực hiện task** — đọc yêu cầu, code, tự verify, tự commit — không cần tách qua
   `/spec → /planning → /build` trừ khi task đủ lớn/mơ hồ và tự thấy cần tách nhỏ để không lạc
   hướng; khi đó có thể tự gọi các skill đó mà không dừng hỏi ở từng bước chuyển tiếp.
3. **Toàn quyền chạy** `pytest`, formatter/linter nếu repo đã setup, và lệnh zip đóng gói
   `.ankiaddon`, trong phạm vi thư mục dự án.
4. **Terminal (Bash/PowerShell) không cần hỏi trước mỗi lệnh** — miễn trong phạm vi thư mục repo,
   không đụng file/hệ thống ngoài repo.
5. **Tự verify bằng cách chạy test thật** (`pytest`) và kiểm tra add-on import được (vd
   `python -c "import <addon>"` hoặc mock `aqt` tối thiểu để load `__init__.py` không lỗi) trước
   khi báo task hoàn thành — không báo "done" chỉ vì đọc code thấy hợp lý.
6. **Tự resolve gap kỹ thuật nhỏ không chạm hard-stop** bên dưới (đặt tên biến, chọn thư viện tiện
   ích nhỏ, format message hiển thị cho user) — tự chọn phương án hợp lý nhất, ghi lại lý do trong
   commit message hoặc comment nếu không hiển nhiên, không cần dừng hỏi.

## Giới hạn — KHÔNG bao giờ tự động, kể cả khi đang autopilot

Đây là rule đã có sẵn trong CLAUDE.md của chính repo. Autopilot không override chúng.

- **Push thẳng vào `main`** — autopilot chỉ push lên nhánh feature. Merge vào `main` user tự làm.
- **Force push** — không bao giờ, kể cả trên nhánh feature.
- **Cài/symlink add-on vào thư mục Anki thật của user** (`%APPDATA%\Anki2\addons21\`) — đây là
  thao tác ngoài phạm vi repo, ảnh hưởng tới bản Anki đang chạy thật của user. Chỉ làm khi user
  yêu cầu tường minh, ngoài scope autopilot.
- **Đọc/sửa/xoá dữ liệu collection Anki thật của user** (file `.anki2`, thư mục
  `collection.media`, hoặc bất kỳ profile thật nào ngoài repo) — đây là dữ liệu học tập thật của
  user, mất là mất luôn, không phục hồi được từ repo này.
- **Monkey-patch function của Anki khi đã có hook tương đương** trong `aqt.gui_hooks`/
  `anki.hooks` (Anti-pattern #1 trong CLAUDE.md) — phát hiện là phải sửa lại cách làm ngay, không
  "cho nhanh rồi refactor sau".
- **Commit `meta.json` hoặc file `.ankiaddon`** (build artifact, Anti-pattern #2) — cả hai đã nằm
  trong `.gitignore`, đừng `git add -f` để lách.
- **Import `aqt` vào module chỉ xử lý data** (Anti-pattern #4) — phá tính testable-without-Qt,
  phải tách lại boundary trước khi commit, không merge tạm.
- **Push code chưa tự verify được** (test fail, hoặc add-on không import/load được) — dừng lại,
  báo rõ lỗi cho user thay vì báo "done".

## Cuối mỗi lần chạy

Luôn tổng kết: task nào xong, test nào pass, add-on nào đã verify import/load được, và bất kỳ điều
gì bị dừng/skip cần user xem lại — không im lặng bỏ qua.
