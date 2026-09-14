"""Pure logic for rendering a TreeNode into a self-contained HTML block.

No aqt import here - keep this module testable without a running Anki
instance. Deliberately uses ONLY inline style="..." attributes and native
<details>/<summary> for expand/collapse - NOT a <style> block or <script>.

Real-world finding (see tasks/plan.md Task 5/6): Anki's paste sanitization
strips <style> and <script> tags entirely when pasting rich HTML into a
field, so a self-contained block relying on either loses all
styling/behavior the moment a user pastes it. Inline style attributes and
plain <details>/<summary> (native browser expand/collapse, no JS needed)
are what actually survive.
"""

import html as html_lib

try:
    from .tree_parser import TreeNode  # real Anki: loaded as a package submodule
except ImportError:
    from tree_parser import TreeNode  # pytest: conftest.py puts this dir on sys.path

_INDENT_PX = 18
# Alternating background per depth, purely for visual distinction between
# nesting levels - inline so it survives paste.
_PALETTE = ["#eef3fb", "#f7f2fa", "#ffffff"]


def _indent_style(depth: int) -> str:
    return f"margin-left:{(depth - 1) * _INDENT_PX}px;"


def _timestamp_html(node: TreeNode) -> str:
    if not node.timestamp:
        return ""
    ts = html_lib.escape(node.timestamp)
    return f'<span style="color:#888;font-size:0.9em;margin-right:4px;">[{ts}]</span>'


def _render_node(node: TreeNode, depth: int) -> str:
    label_html = _timestamp_html(node) + html_lib.escape(node.label)

    if node.children:
        bg = _PALETTE[(depth - 1) % len(_PALETTE)]
        summary_style = (
            f"cursor:pointer;background:{bg};padding:4px 8px;"
            f"border-radius:6px;{_indent_style(depth)}"
        )
        children_html = "".join(_render_node(c, depth + 1) for c in node.children)
        return (
            f'<details style="margin:2px 0;">'
            f'<summary style="{summary_style}">{label_html}</summary>'
            f"{children_html}"
            f"</details>"
        )

    leaf_style = f"margin:2px 0;padding:2px 8px;{_indent_style(depth)}"
    return (
        f'<div style="{leaf_style}">'
        f'<span style="display:inline-block;width:1.2em;">–</span>'
        f"{label_html}"
        f"</div>"
    )


def render_html(root: TreeNode) -> str:
    """Render a TreeNode into HTML using only inline style="..." attributes
    and native <details>/<summary> for expand/collapse (collapsed by
    default - <details> without "open" is collapsed natively, no extra
    markup needed). A node with children becomes a <details>/<summary>
    pair, a leaf node becomes a plain bullet <div>.
    """
    body = "".join(_render_node(c, 1) for c in root.children)
    title = html_lib.escape(root.label)
    return (
        f'<div style="font-family:-apple-system,sans-serif;text-align:left;">'
        f'<div style="font-weight:700;font-size:1.1em;margin-bottom:6px;">{title}</div>'
        f"{body}"
        f"</div>"
    )
