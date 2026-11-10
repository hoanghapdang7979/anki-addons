import re

from assets import SCRIPT, STYLE, build_assets_html


def test_assets_html_has_exactly_one_style_and_one_script_block():
    html = build_assets_html()
    assert html.count("<style") == 1 and html.count("</style>") == 1
    assert html.count("<script") == 1 and html.count("</script>") == 1


def test_script_builds_tooltip_content_with_textcontent_never_innerhtml():
    assert "textContent" in SCRIPT
    for forbidden in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function"):
        assert forbidden not in SCRIPT


def test_script_is_idempotent_and_self_contained():
    assert "window.__hhInit" in SCRIPT
    assert "http://" not in SCRIPT and "https://" not in SCRIPT and "fetch(" not in SCRIPT


def test_script_reads_the_cell_data_attributes_and_drops_native_titles():
    for attr in ("data-label", "data-status", "data-note", "data-hint"):
        assert attr in SCRIPT
    assert "removeAttribute('title')" in SCRIPT


def test_script_keeps_the_tooltip_inside_the_viewport():
    assert "getBoundingClientRect" in SCRIPT and "clientWidth" in SCRIPT


def test_every_css_selector_is_namespaced_with_hh():
    selectors = re.findall(r"([^{}]+)\{", STYLE)
    for group in selectors:
        for sel in group.split(","):
            assert ".hh-" in sel, sel.strip()


def test_style_defines_the_tooltip_and_note_marker_and_preserves_note_line_breaks():
    assert ".hh-tip" in STYLE and "position:fixed" in STYLE.replace(" ", "")
    assert ".hh-note::after" in STYLE.replace(" ", "") or ".hh-note:after" in STYLE
    assert "pre-wrap" in STYLE


def test_style_does_not_leak_to_global_elements():
    assert not re.search(r"(^|})\s*(body|html|button|div|table|td|\*)\s*[{,]", STYLE)
