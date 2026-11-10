# Card template snippet — interactive checklist UI

> Đây **không phải code của add-on** — add-on `habit-checklist` chỉ auto-fill text thô
> `[ ] Habit` vào field lúc tạo note (xem [SPEC.md](../SPEC.md)). Phần checkbox click-to-toggle
> dưới đây là code người dùng tự paste vào Card Template (Tools → Manage Note Types → Cards...),
> giống cách bạn đã tự viết `date-badge`/`quote-box`. Lưu lại đây để tham khảo/tái dùng sau này.
>
> **Yêu cầu:** note type phải dùng `{{edit:Habits}}` (không phải `{{Habits}}` thường) — cần
> add-on `inline-field-editor` đã cài và hoạt động, vì cơ chế save (`pycmd('ife:save:...')`) tái
> dùng đúng bridge command mà add-on đó cung cấp. Không cần thêm bridge command mới nào.

## HTML (đặt trong Front Template, ví dụ cạnh `{{edit:Entry}}`)

```html
<div class="habit-section">
{{#Habits}}
<div class="habit-title">✅ Thói quen hôm nay</div>
<div class="habit-list">{{edit:Habits}}</div>
{{/Habits}}
</div>
```

## CSS (thêm vào Styling)

```css
.habit-section {
  margin: 0 24px 20px;
  padding: 16px 20px;
  background: #ffffff;
  border-radius: 14px;
  text-align: left;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.habit-title {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #b8a37c;
  text-transform: uppercase;
  margin-bottom: 10px;
}
.habit-list {
  line-height: 2;
}
.hc-box {
  display: inline-block;
  width: 20px;
  cursor: pointer;
  user-select: none;
  margin-right: 4px;
  font-size: 16px;
}
.hc-box.hc-checked {
  color: #6b9b5e;
}

.night_mode .habit-section, .nightMode .habit-section { background: #2a251c; box-shadow: none; }
.night_mode .habit-title, .nightMode .habit-title { color: #7d6f52; }
.night_mode .hc-box.hc-checked, .nightMode .hc-box.hc-checked { color: #8fc47a; }
```

## JS (thêm 1 khối `<script>` riêng, không cần gộp vào script date-badge sẵn có)

> **v2 — sửa bug timing.** Bản đầu chỉ gọi `renderHabitBoxes()` 1 lần ngay khi script chạy +
> `MutationObserver`. Thực tế script này có thể chạy **trước khi** div chứa `{{edit:Habits}}`
> tồn tại trong DOM (tuỳ vị trí đặt `<script>` trong template và cách Anki chèn HTML/script vào
> card — không verify được chi tiết cơ chế này vì không có quyền điều khiển Anki để debug trực
> tiếp). Bản dưới đây dùng polling (thử lại mỗi 100ms, tối đa 2 giây) để không phụ thuộc vào thứ
> tự/thời điểm chính xác — chắc chắn hoạt động bất kể `<script>` đặt ở đâu trong template.

```html
<script>
(function () {
    function transformField() {
        var field = document.querySelector('[data-ife-field="Habits"]');
        if (!field) {
            return false; // field chưa tồn tại trong DOM - thử lại sau
        }
        var html = field.innerHTML;
        if (html.indexOf("hc-box") !== -1) {
            return true; // đã transform rồi, không làm lại
        }
        // Only transform "[ ]"/"[x]" markers at the start of a line (start of
        // field or right after <br>) - avoids matching literal "[x]" text a
        // user might type inside a note.
        var wrapped = html.replace(/(^|<br>)\[( |x|X)\]/g, function (_, prefix, mark) {
            var checked = mark.toLowerCase() === "x";
            return (
                prefix +
                '<span class="hc-box' + (checked ? " hc-checked" : "") + '" ' +
                'contenteditable="false" data-checked="' + checked + '">' +
                (checked ? "☑" : "☐") +
                "</span>"
            );
        });
        if (wrapped !== html) {
            field.innerHTML = wrapped;
        }
        return true;
    }

    function toggleBox(box) {
        var checked = box.getAttribute("data-checked") === "true";
        checked = !checked;
        box.setAttribute("data-checked", checked ? "true" : "false");
        box.classList.toggle("hc-checked", checked);
        box.textContent = checked ? "☑" : "☐";

        var field = box.closest("[data-ife-field]");
        if (field && typeof pycmd === "function") {
            pycmd("ife:save:" + field.getAttribute("data-ife-field") + ":" + field.innerHTML);
        }
    }

    document.addEventListener("click", function (e) {
        var box = e.target.closest && e.target.closest(".hc-box");
        if (box) {
            e.preventDefault();
            toggleBox(box);
        }
    });

    // Poll instead of relying on a single synchronous call + MutationObserver
    // alone - robust regardless of exactly when/how Anki inserts the rest of
    // the card HTML relative to this <script> tag running.
    var attempts = 0;
    var timer = setInterval(function () {
        attempts += 1;
        if (transformField() || attempts >= 20) {
            clearInterval(timer);
        }
    }, 100);

    // Still keep the observer for later re-renders (e.g. if the field's HTML
    // gets replaced again while this card is showing).
    new MutationObserver(transformField).observe(document.body, {
        childList: true,
        subtree: true,
    });
})();
</script>
```

## Cách hoạt động

1. Add-on `habit-checklist` điền `"[ ] Exercise<br>[ ] Read<br>[ ] Meditate"` (text thô) vào
   field `Habits` lúc tạo note — không đổi.
2. `inline-field-editor` render `{{edit:Habits}}` thành
   `<span data-ife-field="Habits" contenteditable="true">...</span>`.
3. Script ở trên tìm span đó, thay `[ ]`/`[x]` đầu mỗi dòng bằng 1 `<span class="hc-box"
   contenteditable="false">☐/☑</span>` — nằm **trong** vùng editable nhưng bản thân nó không
   nhận gõ chữ (giữ đúng chỗ, không lệch khi user gõ note cạnh nó).
4. Click vào checkbox → đổi glyph + gọi thẳng `pycmd('ife:save:Habits:<html-mới>')` — đúng
   format `inline-field-editor` đã có sẵn cơ chế nhận và lưu (`parse_save_message` +
   `_on_webview_did_receive_js_message`), nên **không cần sửa Python của add-on nào**.
5. Muốn ghi note cho 1 habit: click ngay sau tên habit (vùng vẫn contenteditable bình thường) và
   gõ thêm — save khi blur (cơ chế `inline-field-editor` đã có).

## Rủi ro / giới hạn đã biết

- Field lưu lại sẽ có HTML `<span class="hc-box">` thay vì text thuần `[ ]`/`[x]` sau lần đầu
  tương tác — không ảnh hưởng gì tới add-on (chỉ chạm field lúc note vừa tạo, không đọc lại sau
  đó), nhưng nếu sau này muốn đọc lại field bằng script khác (vd thống kê % hoàn thành) thì phải
  parse cả 2 dạng (text thô ban đầu và HTML đã transform).
- Chưa tự test trong Anki thật (không có quyền computer-use) — bạn paste vào Card Types, xem
  Preview, xác nhận: (a) checkbox hiện đúng glyph ☐/☑, (b) click đổi trạng thái + lưu đúng (mở
  lại note/Browse kiểm tra), (c) click ngay sau tên habit vẫn gõ thêm note được bình thường.
- Nếu v2 (polling) vẫn không hiện checkbox: nhiều khả năng còn lại là ký tự `[`/`]` trong field
  không phải ASCII thường (do gõ tiếng Việt/IME chuyển thành ký tự khác), hoặc dòng ngăn cách
  không phải `<br>`. Cách chẩn đoán chính xác nhất: Browse → click field Habits → **Ctrl+Shift+X**
  (xem HTML source) → gửi lại đoạn HTML thô đó (không phải code template) để so khớp với regex.
