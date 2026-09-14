"""Pure logic for parsing ASCII tree text into a TreeNode structure.

No aqt import here - keep this module testable without a running Anki
instance (see CLAUDE.md code style: data-only modules stay Qt-free).
HTML escaping is deliberately NOT done here - see tree_renderer.py; a
raw label may contain "<", "&", etc. untouched.
"""

import re
from dataclasses import dataclass, field

_TIMESTAMP_RE = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]\s*")
# Matches the shortest prefix up to the first "├── " or "└── " connector -
# depth is derived from the prefix length (4 chars per indent level),
# regardless of which of the two connector glyphs is used.
_NODE_LINE_RE = re.compile(r"^(?P<prefix>.*?)[├└]── (?P<label>.*)$")


@dataclass
class TreeNode:
    label: str
    timestamp: str | None = None
    children: list["TreeNode"] = field(default_factory=list)


def _split_timestamp(text: str) -> tuple[str | None, str]:
    m = _TIMESTAMP_RE.match(text)
    if m:
        return m.group(1), text[m.end() :]
    return None, text


def _line_depth_and_label(line: str) -> tuple[int, str] | None:
    """Return (depth, raw_label) for a tree line, or None if the line has
    no "├── "/"└── " connector (e.g. a bare "│" separator line).
    """
    m = _NODE_LINE_RE.match(line)
    if not m:
        return None
    depth = len(m.group("prefix")) // 4 + 1
    return depth, m.group("label").strip()


def parse_tree(text: str) -> TreeNode:
    """Parse ASCII tree text (├──/│/└── connectors, 4-char indent per
    level) into a TreeNode. The first non-empty line becomes the root.
    """
    non_empty = [line for line in text.splitlines() if line.strip()]
    if not non_empty:
        raise ValueError("empty tree text")

    root = TreeNode(label=non_empty[0].strip())
    stack: list[tuple[int, TreeNode]] = [(0, root)]

    for line in non_empty[1:]:
        parsed = _line_depth_and_label(line)
        if parsed is None:
            continue  # bare "│" separator line between sibling blocks
        depth, raw_label = parsed
        timestamp, label = _split_timestamp(raw_label)
        node = TreeNode(label=label, timestamp=timestamp)

        while stack[-1][0] >= depth:
            stack.pop()
        stack[-1][1].children.append(node)
        stack.append((depth, node))

    return root
