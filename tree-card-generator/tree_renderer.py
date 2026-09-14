"""Pure logic for rendering a TreeNode into a self-contained HTML block.

No aqt import here - keep this module testable without a running Anki
instance. The output embeds its own <style> and <script> (no external
files/CDN) so it can be pasted into a field on any note type and just
work - see SPEC.md Boundaries.
"""

import html as html_lib

from tree_parser import TreeNode

_CSS = """
.tcg-root { font-family: -apple-system, sans-serif; text-align: left; }
.tcg-title { font-weight: 700; font-size: 1.1em; margin-bottom: 0.5em; }
.tcg-node { margin: 0.2em 0; }
.tcg-header { cursor: pointer; user-select: none; padding: 0.15em 0; }
.tcg-arrow { display: inline-block; width: 1.2em; }
.tcg-children { margin-left: 1.4em; }
.tcg-children.tcg-collapsed { display: none; }
.tcg-leaf { margin: 0.15em 0 0.15em 1.4em; }
.tcg-bullet { display: inline-block; width: 1.2em; }
.tcg-timestamp { color: #888; font-size: 0.9em; margin-right: 0.3em; }
"""

_JS = """
function tcgToggle(headerEl) {
    var childrenEl = headerEl.nextElementSibling;
    childrenEl.classList.toggle("tcg-collapsed");
    var arrow = headerEl.querySelector(".tcg-arrow");
    arrow.textContent = childrenEl.classList.contains("tcg-collapsed") ? "▸" : "▾";
}
"""


def _timestamp_html(node: TreeNode) -> str:
    if not node.timestamp:
        return ""
    return f'<span class="tcg-timestamp">[{html_lib.escape(node.timestamp)}]</span> '


def _render_node(node: TreeNode, depth: int) -> str:
    label_html = _timestamp_html(node) + html_lib.escape(node.label)

    if node.children:
        children_html = "".join(_render_node(c, depth + 1) for c in node.children)
        return (
            f'<div class="tcg-node tcg-depth-{depth}">'
            f'<div class="tcg-header" onclick="tcgToggle(this)">'
            f'<span class="tcg-arrow">▸</span>'
            f'<span class="tcg-label">{label_html}</span>'
            f"</div>"
            f'<div class="tcg-children tcg-collapsed">{children_html}</div>'
            f"</div>"
        )

    return (
        f'<div class="tcg-leaf tcg-depth-{depth}">'
        f'<span class="tcg-bullet">–</span>'
        f'<span class="tcg-label">{label_html}</span>'
        f"</div>"
    )


def render_html(root: TreeNode) -> str:
    """Render a TreeNode into a self-contained HTML block (inline <style>
    and <script>) - a node with children becomes a clickable collapsible
    section (collapsed by default), a leaf node becomes a plain bullet.
    """
    body = "".join(_render_node(c, 1) for c in root.children)
    title = html_lib.escape(root.label)
    return (
        f'<div class="tcg-root">'
        f'<div class="tcg-title">{title}</div>'
        f"{body}"
        f"</div>"
        f"<style>{_CSS}</style>"
        f"<script>{_JS}</script>"
    )
