"""CLI: translate the Essential Words dictionary from Chinese to Vietnamese.

Orchestrates translator.py (pure JSON transform), gcloud_client.py (the
Google Cloud API), and cache_store.py (resumable checkpoint). See SPEC.md
and tasks/plan.md for the full design - especially the hard gate between a
`--limit` dry run and a full run, which costs real money and is NOT
triggered automatically by this script (that decision lives with whoever
invokes it without --limit).
"""

import argparse
import json
import logging
from pathlib import Path

from cache_store import CacheStore
from gcloud_client import translate_chunks
from translator import extract_translatable_strings, rebuild_json

logger = logging.getLogger(__name__)

DEFAULT_CACHE_PATH = Path(__file__).resolve().parent / "cache" / "translations.json"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to the source JSON dictionary")
    parser.add_argument("--output", required=True, help="Path to write the translated JSON")
    parser.add_argument(
        "--credentials", required=True, help="Path to the Google Cloud service account JSON key"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N word entries (for a cheap dry run)",
    )
    parser.add_argument(
        "--cache",
        default=str(DEFAULT_CACHE_PATH),
        help="Path to the resumable translation cache file",
    )
    return parser.parse_args(argv)


def run(
    input_path: str,
    output_path: str,
    credentials_path: str,
    limit: int | None,
    cache_path: str,
) -> None:
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    if limit is not None:
        data = data[:limit]
        logger.info("Limiting to first %d word entries", limit)

    all_strings = extract_translatable_strings(data)
    cache = CacheStore(cache_path)
    missing = cache.missing(all_strings)
    logger.info(
        "%d translatable strings across %d entries - %d already cached, %d need translating",
        len(all_strings),
        len(data),
        len(all_strings) - len(missing),
        len(missing),
    )

    if missing:
        translated_count = 0

        def on_chunk_done(originals: list[str], translations: list[str]) -> None:
            nonlocal translated_count
            cache.update(dict(zip(originals, translations)))
            translated_count += len(originals)
            logger.info("Translated %d/%d missing strings", translated_count, len(missing))

        translate_chunks(missing, credentials_path, on_chunk_done=on_chunk_done)

    def translate_fn(strings: list[str]) -> list[str]:
        return [_lookup_or_raise(cache, s) for s in strings]

    result_data = rebuild_json(data, translate_fn)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    logger.info("Wrote %d word entries to %s", len(result_data), output_path)


def _lookup_or_raise(cache: CacheStore, string: str) -> str:
    cached = cache.get(string)
    if cached is None:
        raise RuntimeError(f"String not found in cache after translation pass: {string!r}")
    return cached


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = _parse_args(argv)
    run(args.input, args.output, args.credentials, args.limit, args.cache)


if __name__ == "__main__":
    main()
