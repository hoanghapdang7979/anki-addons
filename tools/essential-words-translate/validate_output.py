"""Validate a translated Essential Words JSON output against the original.

Checks (see SPEC.md -> Success Criteria):
(a) same number of word entries
(b) no Chinese characters remain in any field that was supposed to be
    translated
(c) every English-only field is byte-for-byte identical to the original
(d) the original source file has not been modified
"""

import argparse
import hashlib
import json
import re
import sys

_CJK_RE = re.compile(r"[一-鿿]")

ENGLISH_ONLY_KEYS_IN_TRANS_LIKE = ("pos",)


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_remaining_chinese(data: list[dict]) -> list[str]:
    """Return a description of every spot that still contains a CJK
    character in a field that was supposed to be fully translated.
    """
    problems: list[str] = []

    def check(label: str, text: str) -> None:
        if text and _CJK_RE.search(text):
            problems.append(f"{label}: {text!r}")

    for i, item in enumerate(data):
        word = item.get("word", f"<entry {i}>")
        for j, t in enumerate(item.get("trans", [])):
            check(f"{word}.trans[{j}].cn", t.get("cn", ""))
        for j, s in enumerate(item.get("sentences", [])):
            check(f"{word}.sentences[{j}].cn", s.get("cn", ""))
        for j, p in enumerate(item.get("phrases", [])):
            check(f"{word}.phrases[{j}].cn", p.get("cn", ""))
        for j, s in enumerate(item.get("synos", [])):
            check(f"{word}.synos[{j}].cn", s.get("cn", ""))
        for j, rel in enumerate(item.get("relWords", {}).get("rels", [])):
            for k, w in enumerate(rel.get("words", [])):
                check(f"{word}.relWords.rels[{j}].words[{k}].cn", w.get("cn", ""))
        for j, e in enumerate(item.get("etymology", [])):
            check(f"{word}.etymology[{j}].d", e.get("d", ""))
            t_value = e.get("t", "")
            _, sep, cn_part = t_value.partition(":")
            if sep:
                check(f"{word}.etymology[{j}].t (suffix)", cn_part)

    return problems


_ENGLISH_FIELD_PATHS = (
    "word",
    "phonetic0",
    "phonetic1",
)


def _diff_english_fields(original: list[dict], translated: list[dict]) -> list[str]:
    """Return a description of every English-only field that differs
    between the original and the translated output - these must never
    change.
    """
    problems: list[str] = []
    if len(original) != len(translated):
        problems.append(
            f"entry count differs: original={len(original)} translated={len(translated)}"
        )
        return problems

    for orig_item, new_item in zip(original, translated):
        word = orig_item.get("word", "<unknown>")
        for key in _ENGLISH_FIELD_PATHS:
            if orig_item.get(key) != new_item.get(key):
                problems.append(f"{word}.{key} changed")

        for label, orig_list, new_list in (
            ("trans", orig_item.get("trans", []), new_item.get("trans", [])),
            ("sentences", orig_item.get("sentences", []), new_item.get("sentences", [])),
            ("phrases", orig_item.get("phrases", []), new_item.get("phrases", [])),
            ("synos", orig_item.get("synos", []), new_item.get("synos", [])),
        ):
            for i, (o, n) in enumerate(zip(orig_list, new_list)):
                for key in ("c", "pos", "ws"):
                    if key in o and o.get(key) != n.get(key):
                        problems.append(f"{word}.{label}[{i}].{key} changed")

        orig_rw = orig_item.get("relWords", {})
        new_rw = new_item.get("relWords", {})
        if orig_rw.get("root") != new_rw.get("root"):
            problems.append(f"{word}.relWords.root changed")
        for i, (orel, nrel) in enumerate(
            zip(orig_rw.get("rels", []), new_rw.get("rels", []))
        ):
            if orel.get("pos") != nrel.get("pos"):
                problems.append(f"{word}.relWords.rels[{i}].pos changed")
            for j, (ow, nw) in enumerate(zip(orel.get("words", []), nrel.get("words", []))):
                if ow.get("c") != nw.get("c"):
                    problems.append(f"{word}.relWords.rels[{i}].words[{j}].c changed")

        for i, (oe, ne) in enumerate(
            zip(orig_item.get("etymology", []), new_item.get("etymology", []))
        ):
            orig_prefix = oe.get("t", "").split(":", 1)[0]
            new_prefix = ne.get("t", "").split(":", 1)[0]
            if orig_prefix != new_prefix:
                problems.append(f"{word}.etymology[{i}].t prefix changed")

    return problems


def validate(original_path: str, translated_path: str) -> bool:
    original_hash_before = _sha256(original_path)

    with open(original_path, encoding="utf-8") as f:
        original = json.load(f)
    with open(translated_path, encoding="utf-8") as f:
        translated = json.load(f)

    original_hash_after = _sha256(original_path)

    ok = True

    if len(translated) != len(original):
        print(f"FAIL: entry count mismatch - original {len(original)}, translated {len(translated)}")
        ok = False
    else:
        print(f"OK: entry count matches ({len(translated)})")

    if original_hash_before != original_hash_after:
        print("FAIL: original source file changed while reading it (checksum mismatch)")
        ok = False
    else:
        print("OK: original source file untouched (checksum matches)")

    remaining_chinese = _find_remaining_chinese(translated)
    if remaining_chinese:
        print(f"FAIL: {len(remaining_chinese)} field(s) still contain Chinese characters:")
        for p in remaining_chinese[:20]:
            print(f"  - {p}")
        if len(remaining_chinese) > 20:
            print(f"  ... and {len(remaining_chinese) - 20} more")
        ok = False
    else:
        print("OK: no Chinese characters remain in any translated field")

    english_diffs = _diff_english_fields(original, translated)
    if english_diffs:
        print(f"FAIL: {len(english_diffs)} English field(s) changed unexpectedly:")
        for p in english_diffs[:20]:
            print(f"  - {p}")
        if len(english_diffs) > 20:
            print(f"  ... and {len(english_diffs) - 20} more")
        ok = False
    else:
        print("OK: all English fields preserved exactly")

    return ok


def main(argv: list[str] | None = None) -> None:
    # Windows terminals often default to cp1252, which can't encode
    # Vietnamese/Chinese characters this script prints in diagnostics -
    # force UTF-8 on stdout so a report with real content doesn't crash
    # instead of being shown.
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True)
    parser.add_argument("--translated", required=True)
    args = parser.parse_args(argv)

    ok = validate(args.original, args.translated)
    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
