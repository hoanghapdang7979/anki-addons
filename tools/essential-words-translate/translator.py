"""Pure logic for extracting Chinese strings from, and rebuilding, the
Essential Words dictionary structure. No network/API calls here - see
gcloud_client.py for the part that actually talks to Google Cloud.
"""

import copy
import re
from typing import Callable

_CJK_RE = re.compile(r"[一-鿿]")


def _has_chinese(text: str) -> bool:
    return bool(_CJK_RE.search(text))


def _collect_slots(data: list[dict]) -> list[tuple[str, Callable[[str], None]]]:
    """Walk the word-entry list, returning (original_string, setter) pairs for
    every Chinese field that needs translating.

    `setter(translated)` writes the translation back into `data` at the
    right spot - this keeps extraction and rebuilding in lockstep by
    construction (one walk, reused by both extract_translatable_strings and
    rebuild_json), so they can't drift out of sync with each other.
    """
    slots: list[tuple[str, Callable[[str], None]]] = []

    def add(container: dict, key: str) -> None:
        value = container.get(key)
        if value:
            slots.append((value, lambda v, c=container, k=key: c.__setitem__(k, v)))

    for item in data:
        for t in item.get("trans", []):
            add(t, "cn")
        for s in item.get("sentences", []):
            add(s, "cn")
        for p in item.get("phrases", []):
            add(p, "cn")
        for s in item.get("synos", []):
            add(s, "cn")
        rel_words = item.get("relWords", {})
        for rel in rel_words.get("rels", []):
            for w in rel.get("words", []):
                add(w, "cn")
        for etymology_note in item.get("etymology", []):
            add(etymology_note, "d")
            t_value = etymology_note.get("t", "")
            prefix, sep, cn_part = t_value.partition(":")
            if sep and _has_chinese(cn_part):
                keep = prefix + sep
                slots.append(
                    (cn_part, lambda v, c=etymology_note, k=keep: c.__setitem__("t", k + v))
                )

    return slots


def extract_translatable_strings(data: list[dict]) -> list[str]:
    """Return every Chinese string that needs translating, in the exact
    order rebuild_json() applies translations back.
    """
    return [s for s, _ in _collect_slots(data)]


def rebuild_json(
    data: list[dict], translate_fn: Callable[[list[str]], list[str]]
) -> list[dict]:
    """Return a deep copy of `data` with every Chinese field replaced by its
    translation, everything else untouched.

    translate_fn receives the full list of strings needing translation and
    must return translations in the same order - this is the only seam that
    touches the network, so tests pass in a fake translate_fn and never hit
    Google's API.
    """
    result = copy.deepcopy(data)
    slots = _collect_slots(result)
    originals = [s for s, _ in slots]
    translations = translate_fn(originals)
    if len(translations) != len(originals):
        raise ValueError(
            f"translate_fn returned {len(translations)} results for "
            f"{len(originals)} inputs"
        )
    for (_, setter), translated in zip(slots, translations):
        setter(translated)
    return result
