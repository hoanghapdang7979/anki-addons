import json
from unittest.mock import patch

import translate as translate_cli

SAMPLE = [
    {
        "word": "agree",
        "phonetic0": "x",
        "phonetic1": "x",
        "trans": [{"pos": "v.", "cn": "同意"}],
        "sentences": [],
        "phrases": [],
        "synos": [],
        "relWords": {"root": "agree", "rels": []},
        "etymology": [],
    },
    {
        "word": "alcohol",
        "phonetic0": "y",
        "phonetic1": "y",
        "trans": [{"pos": "n.", "cn": "酒精"}],
        "sentences": [],
        "phrases": [],
        "synos": [],
        "relWords": {"root": "alcohol", "rels": []},
        "etymology": [],
    },
]


def _fake_translate_chunks(strings, credentials_path, on_chunk_done=None):
    translations = [f"[VI]{s}" for s in strings]
    if on_chunk_done:
        on_chunk_done(strings, translations)
    return translations


def _write_sample(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(SAMPLE, ensure_ascii=False), encoding="utf-8")
    return input_path


def test_run_writes_translated_output_and_populates_cache(tmp_path):
    input_path = _write_sample(tmp_path)
    output_path = tmp_path / "output.json"
    cache_path = tmp_path / "cache.json"

    with patch("translate.translate_chunks", side_effect=_fake_translate_chunks):
        translate_cli.run(str(input_path), str(output_path), "fake-creds.json", None, str(cache_path))

    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(result) == 2
    assert result[0]["trans"][0]["cn"] == "[VI]同意"
    assert result[1]["trans"][0]["cn"] == "[VI]酒精"
    assert result[0]["word"] == "agree"  # English fields untouched

    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    assert cache["同意"] == "[VI]同意"
    assert cache["酒精"] == "[VI]酒精"


def test_run_respects_limit(tmp_path):
    input_path = _write_sample(tmp_path)
    output_path = tmp_path / "output.json"
    cache_path = tmp_path / "cache.json"

    with patch("translate.translate_chunks", side_effect=_fake_translate_chunks):
        translate_cli.run(str(input_path), str(output_path), "fake-creds.json", 1, str(cache_path))

    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(result) == 1
    assert result[0]["word"] == "agree"


def test_run_does_not_retranslate_strings_already_in_cache(tmp_path):
    input_path = _write_sample(tmp_path)
    output_path = tmp_path / "output.json"
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({"同意": "Đồng ý"}, ensure_ascii=False), encoding="utf-8")

    calls = []

    def spy(strings, credentials_path, on_chunk_done=None):
        calls.extend(strings)
        return _fake_translate_chunks(strings, credentials_path, on_chunk_done)

    with patch("translate.translate_chunks", side_effect=spy):
        translate_cli.run(str(input_path), str(output_path), "fake-creds.json", None, str(cache_path))

    assert "同意" not in calls  # already cached - must not be re-translated (real cost)
    assert "酒精" in calls

    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result[0]["trans"][0]["cn"] == "Đồng ý"  # came from cache, not re-translated


def test_run_skips_the_api_call_entirely_when_everything_is_already_cached(tmp_path):
    input_path = _write_sample(tmp_path)
    output_path = tmp_path / "output.json"
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(
        json.dumps({"同意": "Đồng ý", "酒精": "Cồn"}, ensure_ascii=False), encoding="utf-8"
    )

    with patch("translate.translate_chunks") as mock_translate_chunks:
        translate_cli.run(str(input_path), str(output_path), "fake-creds.json", None, str(cache_path))

    mock_translate_chunks.assert_not_called()
    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result[0]["trans"][0]["cn"] == "Đồng ý"
    assert result[1]["trans"][0]["cn"] == "Cồn"


def test_parse_args_reads_required_and_optional_flags():
    args = translate_cli._parse_args(
        [
            "--input", "in.json",
            "--output", "out.json",
            "--credentials", "creds.json",
            "--limit", "10",
            "--cache", "my_cache.json",
        ]
    )

    assert args.input == "in.json"
    assert args.output == "out.json"
    assert args.credentials == "creds.json"
    assert args.limit == 10
    assert args.cache == "my_cache.json"


def test_parse_args_limit_defaults_to_none():
    args = translate_cli._parse_args(
        ["--input", "in.json", "--output", "out.json", "--credentials", "creds.json"]
    )

    assert args.limit is None
