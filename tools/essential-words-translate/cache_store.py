"""Resumable translation cache: original string -> translated string.

Persisted to disk after every update() call (not just once at the end of a
job) so a crash, network failure, or Ctrl+C partway through the full
51,452-string run doesn't require re-translating - and re-paying for -
strings already done.
"""

import json
import time
from pathlib import Path

_SAVE_MAX_RETRIES = 5
_SAVE_RETRY_DELAY_SECONDS = 0.2


class CacheStore:
    """Loads a JSON cache file (if present) and tracks which strings still
    need translating, persisting new entries immediately as they arrive.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._data: dict[str, str] = {}
        if self._path.exists():
            with open(self._path, encoding="utf-8") as f:
                self._data = json.load(f)

    def missing(self, strings: list[str]) -> list[str]:
        """Return the strings in `strings` not yet cached, deduplicated and
        in first-seen order.
        """
        seen: set[str] = set()
        result: list[str] = []
        for s in strings:
            if s not in self._data and s not in seen:
                seen.add(s)
                result.append(s)
        return result

    def get(self, string: str) -> str | None:
        return self._data.get(string)

    def update(self, pairs: dict[str, str]) -> None:
        """Merge new translations into the cache and persist to disk
        immediately - the caller should call this after every batch, not
        just once at the end.
        """
        self._data.update(pairs)
        self._save()

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

        # tmp_path.replace(self._path) is meant to be atomic, but on Windows
        # it can transiently raise PermissionError if something else (a
        # sync client like OneDrive watching a Desktop folder, an antivirus
        # scanner) briefly has the target file open - retry rather than
        # losing the whole translation job over a momentary lock.
        last_error: OSError | None = None
        for attempt in range(1, _SAVE_MAX_RETRIES + 1):
            try:
                tmp_path.replace(self._path)
                return
            except OSError as exc:
                last_error = exc
                if attempt < _SAVE_MAX_RETRIES:
                    time.sleep(_SAVE_RETRY_DELAY_SECONDS * attempt)
        raise last_error
