import json
from pathlib import Path

import pytest

from cache_store import CacheStore


def test_missing_returns_strings_not_in_cache(tmp_path):
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({"你好": "Xin chào"}, ensure_ascii=False), encoding="utf-8")
    store = CacheStore(cache_path)

    result = store.missing(["你好", "谢谢"])

    assert result == ["谢谢"]


def test_missing_returns_all_strings_when_no_cache_file_exists(tmp_path):
    store = CacheStore(tmp_path / "does_not_exist.json")

    result = store.missing(["你好", "谢谢"])

    assert result == ["你好", "谢谢"]


def test_missing_dedupes_while_preserving_first_seen_order(tmp_path):
    store = CacheStore(tmp_path / "cache.json")

    result = store.missing(["你好", "谢谢", "你好"])

    assert result == ["你好", "谢谢"]


def test_get_returns_cached_translation_or_none(tmp_path):
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({"你好": "Xin chào"}, ensure_ascii=False), encoding="utf-8")
    store = CacheStore(cache_path)

    assert store.get("你好") == "Xin chào"
    assert store.get("unknown") is None


def test_update_persists_to_disk_immediately(tmp_path):
    cache_path = tmp_path / "cache.json"
    store = CacheStore(cache_path)

    store.update({"你好": "Xin chào"})

    # A fresh CacheStore reading the same file sees the update - proves it
    # was actually written to disk, not just kept in this instance's memory.
    reloaded = CacheStore(cache_path)
    assert reloaded.get("你好") == "Xin chào"


def test_update_merges_with_existing_entries_without_losing_them(tmp_path):
    cache_path = tmp_path / "cache.json"
    store = CacheStore(cache_path)
    store.update({"你好": "Xin chào"})
    store.update({"谢谢": "Cảm ơn"})

    reloaded = CacheStore(cache_path)
    assert reloaded.get("你好") == "Xin chào"
    assert reloaded.get("谢谢") == "Cảm ơn"


def test_cache_write_survives_even_if_caller_crashes_right_afterward(tmp_path):
    """Proves the real guarantee this module exists for: once update()
    returns, that batch's translations are durable on disk - a crash in the
    NEXT batch must not lose them (see plan.md Risks: avoid re-paying for
    strings already translated).
    """
    cache_path = tmp_path / "cache.json"
    store = CacheStore(cache_path)

    store.update({"batch1-word": "batch1-translation"})
    # Simulate the process dying right here (network error in batch 2,
    # uncaught exception, Ctrl+C) - nothing after this line runs.

    reloaded_after_crash = CacheStore(cache_path)
    assert reloaded_after_crash.get("batch1-word") == "batch1-translation"


def test_missing_excludes_strings_added_by_a_previous_update_call(tmp_path):
    cache_path = tmp_path / "cache.json"
    store = CacheStore(cache_path)
    store.update({"你好": "Xin chào"})

    result = store.missing(["你好", "谢谢"])

    assert result == ["谢谢"]


def test_save_retries_on_transient_permission_error(tmp_path, monkeypatch):
    # Reproduces a real failure hit during the full translation run: Windows
    # (with the cache file under a OneDrive-synced Desktop folder) can
    # transiently deny os.replace() while a sync client briefly locks the
    # target file. Must retry instead of losing the whole job.
    cache_path = tmp_path / "cache.json"
    store = CacheStore(cache_path)
    original_replace = Path.replace
    call_count = {"n": 0}

    def flaky_replace(self, target):
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise PermissionError("simulated transient lock (e.g. OneDrive sync)")
        return original_replace(self, target)

    monkeypatch.setattr(Path, "replace", flaky_replace)

    store.update({"你好": "Xin chào"})  # must not raise

    assert call_count["n"] == 3
    reloaded = CacheStore(cache_path)
    assert reloaded.get("你好") == "Xin chào"


def test_save_raises_after_persistent_permission_error(tmp_path, monkeypatch):
    cache_path = tmp_path / "cache.json"
    store = CacheStore(cache_path)

    def always_fail_replace(self, target):
        raise PermissionError("persistent lock")

    monkeypatch.setattr(Path, "replace", always_fail_replace)

    with pytest.raises(PermissionError):
        store.update({"你好": "Xin chào"})
