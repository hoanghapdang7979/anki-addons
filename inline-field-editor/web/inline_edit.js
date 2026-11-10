// Wires up [data-ife-field] spans (rendered by editor_hook.py's field
// filter) so blurring them saves the new HTML back to the note via the
// pycmd bridge. Anki swaps #qa content between cards without a full page
// reload, so a MutationObserver re-attaches listeners to newly rendered
// cards instead of a one-shot scan.
(function () {
    function attach(el) {
        if (el.dataset.ifeBound) {
            return;
        }
        el.dataset.ifeBound = "1";
        el.addEventListener("blur", function () {
            var fieldName = el.getAttribute("data-ife-field");
            pycmd("ife:save:" + fieldName + ":" + el.innerHTML);
        });
    }

    function scan(root) {
        root.querySelectorAll("[data-ife-field]").forEach(attach);
    }

    scan(document);

    new MutationObserver(function () {
        scan(document);
    }).observe(document.body, { childList: true, subtree: true });
})();
