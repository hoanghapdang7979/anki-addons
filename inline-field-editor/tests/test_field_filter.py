from editor_hook import build_editable_span, edit_field_filter


def test_build_editable_span_wraps_content_in_contenteditable_span():
    html = build_editable_span("Hello <b>world</b>", "Front")

    assert html == (
        '<span data-ife-field="Front" contenteditable="true" '
        'class="ife-editable">Hello <b>world</b></span>'
    )


def test_build_editable_span_escapes_double_quotes_in_field_name():
    html = build_editable_span("text", 'Weird"Name')

    assert html == (
        '<span data-ife-field="Weird&quot;Name" contenteditable="true" '
        'class="ife-editable">text</span>'
    )


def test_build_editable_span_allows_empty_field_content():
    html = build_editable_span("", "Front")

    assert html == (
        '<span data-ife-field="Front" contenteditable="true" '
        'class="ife-editable"></span>'
    )


def test_edit_field_filter_wraps_field_when_filter_name_is_edit():
    result = edit_field_filter("Hello", "Front", "edit", ctx=None)

    assert result == build_editable_span("Hello", "Front")


def test_edit_field_filter_leaves_field_unchanged_for_other_filters():
    result = edit_field_filter("Hello", "Front", "furigana", ctx=None)

    assert result == "Hello"


def test_edit_field_filter_leaves_field_unchanged_when_no_filter_applied():
    result = edit_field_filter("Hello", "Front", "", ctx=None)

    assert result == "Hello"
