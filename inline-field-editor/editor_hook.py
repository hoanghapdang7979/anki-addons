"""Pure logic for rendering {{edit:Field}} template fields as editable HTML.

No aqt/anki imports here - keep this module testable without a running
Anki instance (see CLAUDE.md code style: data-only modules stay Qt-free).
"""

from html import escape
from typing import Any


def build_editable_span(field_text: str, field_name: str) -> str:
    """Wrap field HTML in a contenteditable span for inline review editing."""
    return (
        f'<span data-ife-field="{escape(field_name)}" '
        f'contenteditable="true" class="ife-editable">{field_text}</span>'
    )


def edit_field_filter(
    field_text: str, field_name: str, filter_name: str, ctx: Any
) -> str:
    """Anki field-filter callback: wraps the field when {{edit:Field}} is used.

    Registered via anki.hooks.field_filter.append() - see docs/api-notes.md.
    Any filter other than "edit" is passed through unchanged so other
    add-ons' filters (or none) keep working.
    """
    if filter_name != "edit":
        return field_text
    return build_editable_span(field_text, field_name)
