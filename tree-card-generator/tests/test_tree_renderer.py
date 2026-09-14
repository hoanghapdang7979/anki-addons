from pathlib import Path

from tree_parser import TreeNode, parse_tree
from tree_renderer import render_html

FIXTURES = Path(__file__).parent / "fixtures"


def test_render_html_has_no_style_or_script_tags():
    # Real-world finding (see tasks/plan.md Task 5/6): Anki's paste
    # sanitization strips <style> and <script> blocks entirely when pasting
    # rich HTML into a field, so relying on either makes the collapsible
    # tree lose all styling/behavior once pasted. The renderer must not
    # emit either - only inline style="..." attributes and native
    # <details>/<summary> (no JS needed for expand/collapse).
    root = TreeNode(label="Root", children=[TreeNode(label="Leaf")])

    output = render_html(root)

    assert "<style" not in output
    assert "<script" not in output
    assert "onclick" not in output


def test_render_html_node_with_children_uses_details_summary():
    child = TreeNode(label="Child")
    parent = TreeNode(label="Parent", children=[child])
    root = TreeNode(label="Root", children=[parent])

    output = render_html(root)

    assert "<details" in output
    assert "<summary" in output
    assert "Parent" in output


def test_render_html_details_is_collapsed_by_default():
    # <details> without the "open" attribute is collapsed natively - no
    # class/JS needed to achieve the default-collapsed requirement.
    child = TreeNode(label="Child")
    parent = TreeNode(label="Parent", children=[child])
    root = TreeNode(label="Root", children=[parent])

    output = render_html(root)

    assert "<details open" not in output
    assert "<details" in output  # sanity: a real <details> tag is actually present


def test_render_html_leaf_only_tree_has_no_details_wrapper():
    root = TreeNode(label="Root", children=[TreeNode(label="Only Leaf")])

    output = render_html(root)

    assert "Only Leaf" in output
    assert "<details" not in output
    assert "<summary" not in output


def test_render_html_escapes_malicious_label():
    root = TreeNode(label="Root", children=[TreeNode(label="<script>alert(1)</script> & more")])

    output = render_html(root)

    assert "<script>alert(1)</script>" not in output
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in output
    assert "&amp; more" in output


def test_render_html_escapes_malicious_timestamp():
    root = TreeNode(label="Root", children=[TreeNode(label="X", timestamp='00:00:00"><b>')])

    output = render_html(root)

    assert '00:00:00"><b>' not in output


def test_render_html_includes_timestamp_when_present():
    root = TreeNode(label="Root", children=[TreeNode(label="Heading", timestamp="00:03:04")])

    output = render_html(root)

    assert "00:03:04" in output
    assert "Heading" in output


def test_render_html_all_visible_styling_is_inline_not_in_a_stylesheet():
    # Since there's no <style> block at all, any visual styling (colors,
    # indentation) must come from inline style="..." attributes directly
    # on the elements - this is what actually survives Anki's paste.
    child = TreeNode(label="Child")
    parent = TreeNode(label="Parent", children=[child])
    root = TreeNode(label="Root", children=[parent])

    output = render_html(root)

    assert 'style="' in output


def test_render_html_full_sample_tree_has_balanced_tags():
    text = (FIXTURES / "full_sample_tree.txt").read_text(encoding="utf-8")
    root = parse_tree(text)

    output = render_html(root)

    assert output.count("<div") == output.count("</div>")
    assert output.count("<details") == output.count("</details>")
    assert output.count("<summary") == output.count("</summary>")
    for i in range(1, 7):
        assert f"{i}." in output
