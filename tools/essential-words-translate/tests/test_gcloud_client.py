from unittest.mock import MagicMock, patch

import pytest

import gcloud_client


def _fake_translate(translated_map):
    def fake(values, target_language=None, source_language=None):
        return [{"translatedText": translated_map[v]} for v in values]

    return fake


@patch("gcloud_client.translate.Client")
def test_translate_batch_returns_translations_in_order(mock_client_cls):
    client = MagicMock()
    client.translate.side_effect = _fake_translate(
        {"你好": "Xin chào", "谢谢": "Cảm ơn"}
    )
    mock_client_cls.from_service_account_json.return_value = client

    result = gcloud_client.translate_batch(["你好", "谢谢"], "fake-creds.json")

    assert result == ["Xin chào", "Cảm ơn"]


@patch("gcloud_client.translate.Client")
def test_translate_batch_returns_empty_list_for_empty_input(mock_client_cls):
    result = gcloud_client.translate_batch([], "fake-creds.json")

    assert result == []
    mock_client_cls.from_service_account_json.assert_not_called()


@patch("gcloud_client.time.sleep")
@patch("gcloud_client.translate.Client")
def test_translate_batch_retries_on_transient_failure(mock_client_cls, mock_sleep):
    client = MagicMock()
    call_count = {"n": 0}

    def flaky(values, target_language=None, source_language=None):
        call_count["n"] += 1
        if call_count["n"] < 2:
            raise ConnectionError("network blip")
        return [{"translatedText": "Xin chào"}]

    client.translate.side_effect = flaky
    mock_client_cls.from_service_account_json.return_value = client

    result = gcloud_client.translate_batch(["你好"], "fake-creds.json")

    assert result == ["Xin chào"]
    assert call_count["n"] == 2
    mock_sleep.assert_called()  # backoff actually happened between retries


@patch("gcloud_client.time.sleep")
@patch("gcloud_client.translate.Client")
def test_translate_batch_raises_after_max_retries(mock_client_cls, mock_sleep):
    client = MagicMock()
    client.translate.side_effect = ConnectionError("still down")
    mock_client_cls.from_service_account_json.return_value = client

    with pytest.raises(RuntimeError):
        gcloud_client.translate_batch(["你好"], "fake-creds.json")

    assert client.translate.call_count == gcloud_client.MAX_RETRIES


@patch("gcloud_client.translate.Client")
def test_translate_batch_splits_large_input_into_multiple_requests(mock_client_cls):
    client = MagicMock()
    calls = []

    def fake(values, target_language=None, source_language=None):
        calls.append(list(values))
        return [{"translatedText": f"VI-{v}"} for v in values]

    client.translate.side_effect = fake
    mock_client_cls.from_service_account_json.return_value = client

    strings = [f"word{i}" for i in range(150)]  # exceeds MAX_BATCH_COUNT (100)
    result = gcloud_client.translate_batch(strings, "fake-creds.json")

    assert len(calls) > 1
    assert result == [f"VI-word{i}" for i in range(150)]


def test_chunk_by_budget_respects_max_count():
    chunks = list(gcloud_client._chunk_by_budget(["a"] * 250, max_count=100, max_chars=100000))

    assert all(len(c) <= 100 for c in chunks)
    assert sum(len(c) for c in chunks) == 250


def test_chunk_by_budget_respects_max_chars():
    strings = ["x" * 1000] * 10
    chunks = list(gcloud_client._chunk_by_budget(strings, max_count=1000, max_chars=4500))

    assert all(sum(len(s) for s in c) <= 4500 for c in chunks)
    assert sum(len(c) for c in chunks) == 10
