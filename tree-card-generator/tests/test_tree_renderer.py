from pathlib import Path

from tree_parser import TreeNode, parse_tree
from tree_renderer import render_html

FIXTURES = Path(__file__).parent / "fixtures"


def test_render_html_contains_exactly_one_style_and_script_block():
    root = TreeNode(label="Root", children=[TreeNode(label="Leaf")])

    output = render_html(root)

    assert output.count("<style>") == 1
    assert output.count("</style>") == 1
    assert output.count("<script>") == 1
    assert output.count("</script>") == 1


def test_render_html_node_with_children_has_clickable_header_and_collapsed_container():
    child = TreeNode(label="Child")
    parent = TreeNode(label="Parent", children=[child])
    root = TreeNode(label="Root", children=[parent])

    output = render_html(root)

    assert 'onclick="tcgToggle(this)"' in output
    assert 'class="tcg-children tcg-collapsed"' in output


def test_render_html_distinguishes_parent_wrapper_from_leaf_wrapper():
    leaf = TreeNode(label="Leaf")
    parent = TreeNode(label="Parent", children=[leaf])
    root = TreeNode(label="Root", children=[parent])

    output = render_html(root)

    assert 'class="tcg-node' in output
    assert 'class="tcg-leaf' in output


def test_render_html_leaf_only_tree_has_no_toggle_at_all():
    root = TreeNode(label="Root", children=[TreeNode(label="Only Leaf")])

    output = render_html(root)
    body = output.split("<style>")[0]  # the static CSS always mentions
    # "tcg-node"/"tcg-timestamp" as selectors - only the body (the actual
    # rendered markup) reflects whether this specific tree used them.

    assert "tcg-leaf" in body
    assert "onclick" not in body
    assert "tcg-node" not in body


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


def test_render_html_omits_timestamp_markup_when_absent():
    root = TreeNode(label="Root", children=[TreeNode(label="No timestamp here")])

    output = render_html(root)
    body = output.split("<style>")[0]  # the static CSS always defines the
    # ".tcg-timestamp" selector - check the body, not the whole output.

    assert "tcg-timestamp" not in body


def test_render_html_full_sample_tree_has_balanced_div_tags():
    text = (FIXTURES / "full_sample_tree.txt").read_text(encoding="utf-8")
    root = parse_tree(text)

    output = render_html(root)

    assert output.count("<div") == output.count("</div>")
    # sanity: every section title from the sample tree survived into the output
    for i in range(1, 7):
        assert f"{i}." in output
