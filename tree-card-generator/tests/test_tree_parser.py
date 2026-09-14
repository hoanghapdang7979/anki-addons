from pathlib import Path

from tree_parser import parse_tree

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_tree_single_level():
    text = "Root\n├── Child A\n└── Child B"

    root = parse_tree(text)

    assert root.label == "Root"
    assert [c.label for c in root.children] == ["Child A", "Child B"]
    assert root.children[0].children == []


def test_parse_tree_nested_levels():
    text = (
        "Root\n"
        "├── Section 1\n"
        "│   ├── Item 1.1\n"
        "│   └── Item 1.2\n"
        "└── Section 2\n"
        "    └── Item 2.1\n"
    )

    root = parse_tree(text)

    assert [c.label for c in root.children] == ["Section 1", "Section 2"]
    section1, section2 = root.children
    assert [c.label for c in section1.children] == ["Item 1.1", "Item 1.2"]
    assert [c.label for c in section2.children] == ["Item 2.1"]


def test_parse_tree_skips_bare_separator_lines():
    text = "Root\n├── Section 1\n│\n└── Section 2\n"

    root = parse_tree(text)

    assert [c.label for c in root.children] == ["Section 1", "Section 2"]


def test_parse_tree_extracts_leading_timestamp():
    text = "Root\n├── [00:03:04] Some heading\n└── No timestamp here"

    root = parse_tree(text)

    with_ts, without_ts = root.children
    assert with_ts.timestamp == "00:03:04"
    assert with_ts.label == "Some heading"
    assert without_ts.timestamp is None
    assert without_ts.label == "No timestamp here"


def test_parse_tree_keeps_angle_brackets_and_ampersand_raw():
    # Escaping is render_html's job, not parse_tree's - the raw label
    # should come through untouched here.
    text = "Root\n└── <b>bold</b> & more"

    root = parse_tree(text)

    assert root.children[0].label == "<b>bold</b> & more"


def test_parse_tree_last_child_marker_produces_same_structure_as_middle_child():
    # "└──" (last child) and "├── " (a child with more siblings after it)
    # must both correctly attach as children of the same parent at the
    # same depth - only the connector glyph differs, not the parsed depth.
    text = "Root\n├── First (has more siblings)\n└── Last (no more siblings)\n"

    root = parse_tree(text)

    assert len(root.children) == 2
    assert root.children[0].label == "First (has more siblings)"
    assert root.children[1].label == "Last (no more siblings)"


def test_parse_full_sample_tree_top_level_structure():
    text = (FIXTURES / "full_sample_tree.txt").read_text(encoding="utf-8")

    root = parse_tree(text)

    assert root.label == "THE 7-11-4 BLUEPRINT & PHÁT TRIỂN BẢN THÂN (DANIEL PRIESTLEY)"
    assert len(root.children) == 6
    assert [c.label[:2] for c in root.children] == ["1.", "2.", "3.", "4.", "5.", "6."]


def test_parse_full_sample_tree_section_1_has_three_children_each_with_two_leaves():
    text = (FIXTURES / "full_sample_tree.txt").read_text(encoding="utf-8")

    root = parse_tree(text)
    section1 = root.children[0]

    assert len(section1.children) == 3
    for depth2_node in section1.children:
        assert len(depth2_node.children) == 2
        for leaf in depth2_node.children:
            assert leaf.children == []


def test_parse_full_sample_tree_section_1_first_child_has_correct_timestamp():
    text = (FIXTURES / "full_sample_tree.txt").read_text(encoding="utf-8")

    root = parse_tree(text)
    first_grandchild = root.children[0].children[0]

    assert first_grandchild.timestamp == "00:03:04"
    assert "Kỷ nguyên Công nghiệp" in first_grandchild.label


def test_parse_full_sample_tree_section_2_last_child_marker_single_child():
    # "├── [00:25:37] Định luật Dunbar..." has exactly ONE child rendered
    # with "└──" (not "├──", since it's the only/last child) - regression
    # check that a lone last-child still parses as a real child, not 0.
    text = (FIXTURES / "full_sample_tree.txt").read_text(encoding="utf-8")

    root = parse_tree(text)
    section2 = root.children[1]
    dunbar_node = section2.children[0]

    assert dunbar_node.timestamp == "00:25:37"
    assert len(dunbar_node.children) == 1
    assert "1.500 gương mặt" in dunbar_node.children[0].label


def test_parse_full_sample_tree_section_4_leaves_have_no_grandchildren():
    # Section 4's depth-2 items are themselves leaves (no depth-3 children
    # at all) - a different shape than sections 1/2/3/5/6.
    text = (FIXTURES / "full_sample_tree.txt").read_text(encoding="utf-8")

    root = parse_tree(text)
    section4 = root.children[3]

    assert len(section4.children) == 4
    for leaf in section4.children:
        assert leaf.children == []
