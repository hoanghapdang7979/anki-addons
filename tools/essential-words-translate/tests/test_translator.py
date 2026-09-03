import copy

from translator import extract_translatable_strings, rebuild_json

SAMPLE = [
    {
        "word": "agree",
        "phonetic0": "əˈɡriː",
        "phonetic1": "əˈɡriː",
        "trans": [{"pos": "v.", "cn": "同意"}],
        "sentences": [{"c": "I agree.", "cn": "我同意。"}],
        "phrases": [],
        "synos": [{"pos": "vt.", "cn": "同意；赞成", "ws": ["undertake", "accept"]}],
        "relWords": {
            "root": "agree",
            "rels": [{"pos": "adj.", "words": [{"c": "agreed", "cn": "同意的"}]}],
        },
        "etymology": [
            {"t": "agree:", "d": ""},
            {"t": "agree:同意", "d": "来自拉丁语"},
        ],
    },
    {
        "word": "alcohol",
        "phonetic0": "ˈælkəhɒl",
        "phonetic1": "ˈælkəhɔːl",
        "trans": [{"pos": "n.", "cn": "酒精"}],
        "sentences": [],
        "phrases": [{"c": "ethyl alcohol", "cn": "乙醇"}],
        "synos": [],
        "relWords": {"root": "alcohol", "rels": []},
        "etymology": [],
    },
]


def test_extract_translatable_strings_collects_all_chinese_fields_in_order():
    strings = extract_translatable_strings(SAMPLE)

    assert strings == [
        "同意",  # agree.trans[0].cn
        "我同意。",  # agree.sentences[0].cn
        "同意；赞成",  # agree.synos[0].cn
        "同意的",  # agree.relWords.rels[0].words[0].cn
        "来自拉丁语",  # agree.etymology[1].d
        "同意",  # agree.etymology[1].t chinese part ("agree:同意" -> "同意")
        "酒精",  # alcohol.trans[0].cn
        "乙醇",  # alcohol.phrases[0].cn
    ]


def test_extract_translatable_strings_excludes_english_only_text():
    strings = extract_translatable_strings(SAMPLE)

    assert "agree" not in strings
    assert "I agree." not in strings
    assert "agreed" not in strings
    assert "vt." not in strings
    assert "agree:" not in strings  # the whole etymology.t value, prefix included


def test_rebuild_json_preserves_english_fields_exactly():
    result = rebuild_json(SAMPLE, lambda ss: [f"[VI]{s}" for s in ss])

    assert result[0]["word"] == "agree"
    assert result[0]["phonetic0"] == "əˈɡriː"
    assert result[0]["phonetic1"] == "əˈɡriː"
    assert result[0]["sentences"][0]["c"] == "I agree."
    assert result[0]["synos"][0]["pos"] == "vt."
    assert result[0]["synos"][0]["ws"] == ["undertake", "accept"]
    assert result[0]["relWords"]["root"] == "agree"
    assert result[0]["relWords"]["rels"][0]["pos"] == "adj."
    assert result[0]["relWords"]["rels"][0]["words"][0]["c"] == "agreed"
    assert result[1]["word"] == "alcohol"
    assert result[1]["phrases"][0]["c"] == "ethyl alcohol"


def test_rebuild_json_translates_chinese_fields():
    result = rebuild_json(SAMPLE, lambda ss: [f"[VI]{s}" for s in ss])

    assert result[0]["trans"][0]["cn"] == "[VI]同意"
    assert result[0]["sentences"][0]["cn"] == "[VI]我同意。"
    assert result[0]["synos"][0]["cn"] == "[VI]同意；赞成"
    assert result[0]["relWords"]["rels"][0]["words"][0]["cn"] == "[VI]同意的"
    assert result[1]["trans"][0]["cn"] == "[VI]酒精"
    assert result[1]["phrases"][0]["cn"] == "[VI]乙醇"


def test_rebuild_json_handles_etymology_t_with_chinese_suffix():
    result = rebuild_json(SAMPLE, lambda ss: [f"[VI]{s}" for s in ss])

    # "agree:" prefix (including the colon) must survive untouched; only the
    # Chinese part after it goes through translate_fn.
    assert result[0]["etymology"][1]["t"] == "agree:[VI]同意"
    assert result[0]["etymology"][1]["d"] == "[VI]来自拉丁语"


def test_rebuild_json_leaves_etymology_t_untouched_when_no_chinese_present():
    result = rebuild_json(SAMPLE, lambda ss: [f"[VI]{s}" for s in ss])

    assert result[0]["etymology"][0]["t"] == "agree:"
    assert result[0]["etymology"][0]["d"] == ""


def test_rebuild_json_never_passes_the_whole_etymology_t_value_to_translate_fn():
    calls = []

    def spy_translate(strings):
        calls.extend(strings)
        return ["X"] * len(strings)

    rebuild_json(SAMPLE, spy_translate)

    assert "agree:" not in calls
    assert "agree:同意" not in calls


def test_rebuild_json_does_not_mutate_the_original_input():
    original = copy.deepcopy(SAMPLE)

    rebuild_json(SAMPLE, lambda ss: ["X"] * len(ss))

    assert SAMPLE == original


def test_rebuild_json_raises_if_translate_fn_returns_wrong_count():
    import pytest

    with pytest.raises(ValueError):
        rebuild_json(SAMPLE, lambda ss: ["only one"])
