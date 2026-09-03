"""Thin wrapper around Google Cloud Translation API v2.

This is the ONLY module that imports google.cloud.translate - keep it
isolated so translator.py's pure logic stays testable without network
access or real credentials (tests here mock gcloud_client.translate.Client).
"""

import logging
import time
from typing import Callable, Iterator

from google.cloud import translate_v2 as translate

logger = logging.getLogger(__name__)

SOURCE_LANGUAGE = "zh"
TARGET_LANGUAGE = "vi"

# Conservative batching: Google Translate API v2 caps requests at 128
# strings and ~30KB total - stay well under both rather than rely on the
# exact undocumented limit holding forever.
MAX_BATCH_COUNT = 100
MAX_BATCH_CHARS = 4500

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2.0


def _chunk_by_budget(
    strings: list[str], max_count: int, max_chars: int
) -> Iterator[list[str]]:
    """Split `strings` into batches that respect both a max item count and a
    max total character budget per batch.
    """
    batch: list[str] = []
    batch_chars = 0
    for s in strings:
        if batch and (len(batch) >= max_count or batch_chars + len(s) > max_chars):
            yield batch
            batch = []
            batch_chars = 0
        batch.append(s)
        batch_chars += len(s)
    if batch:
        yield batch


def translate_batch(strings: list[str], credentials_path: str) -> list[str]:
    """Translate every string in `strings` from Chinese to Vietnamese.

    Returns translations in the same order as the input. Convenience
    wrapper around translate_chunks() for small inputs (e.g. the manual
    "translate 2 strings" smoke test) where no per-chunk checkpointing is
    needed - for large jobs, translate.py calls translate_chunks() directly
    with on_chunk_done to persist a resumable cache.
    """
    return translate_chunks(strings, credentials_path)


def translate_chunks(
    strings: list[str],
    credentials_path: str,
    on_chunk_done: Callable[[list[str], list[str]], None] | None = None,
) -> list[str]:
    """Translate `strings`, calling on_chunk_done(originals, translations)
    after each internal chunk succeeds.

    Retries transient failures (network, rate limit) with backoff within a
    chunk; a chunk that still fails after MAX_RETRIES raises RuntimeError -
    on_chunk_done will already have fired for every earlier chunk, so the
    caller's cache checkpoint keeps everything translated so far instead of
    silently losing entries.
    """
    if not strings:
        return []

    client = translate.Client.from_service_account_json(credentials_path)
    results: list[str] = []

    for batch in _chunk_by_budget(strings, MAX_BATCH_COUNT, MAX_BATCH_CHARS):
        translated = _translate_one_batch(client, batch)
        results.extend(translated)
        if on_chunk_done is not None:
            on_chunk_done(batch, translated)

    return results


def _translate_one_batch(client, batch: list[str]) -> list[str]:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.translate(
                batch, target_language=TARGET_LANGUAGE, source_language=SOURCE_LANGUAGE
            )
            return [r["translatedText"] for r in response]
        except Exception as exc:  # network/API errors - retry with backoff
            last_error = exc
            logger.warning(
                "translate_batch attempt %d/%d failed for a batch of %d strings: %s",
                attempt,
                MAX_RETRIES,
                len(batch),
                exc,
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    raise RuntimeError(f"translate_batch failed after {MAX_RETRIES} attempts") from last_error
