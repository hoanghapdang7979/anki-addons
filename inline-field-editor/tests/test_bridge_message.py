from editor_hook import parse_save_message


def test_parse_save_message_extracts_field_name_and_html():
    result = parse_save_message("ife:save:Front:<b>Hello</b>")

    assert result == ("Front", "<b>Hello</b>")


def test_parse_save_message_keeps_colons_inside_html_content():
    result = parse_save_message("ife:save:Front:10:30am - see http://x")

    assert result == ("Front", "10:30am - see http://x")


def test_parse_save_message_allows_empty_html():
    result = parse_save_message("ife:save:Front:")

    assert result == ("Front", "")


def test_parse_save_message_returns_none_for_unrelated_message():
    assert parse_save_message("someOtherAddon:doStuff") is None


def test_parse_save_message_returns_none_when_field_name_missing():
    assert parse_save_message("ife:save:") is None
