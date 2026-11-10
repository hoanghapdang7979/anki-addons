import inspect
import json
from datetime import date

import pytest

from bitmap import Bitmap, toggle_today, union

D = date(2026, 11, 11).toordinal()


def test_empty_bitmap_has_nothing_ticked():
    bm = Bitmap()
    assert not bm.is_set(D)
    assert bm.ticked_ordinals() == set()


def test_with_bit_sets_only_that_day():
    bm = Bitmap().with_bit(D, True)
    assert bm.is_set(D)
    assert not bm.is_set(D - 1)
    assert not bm.is_set(D + 1)


def test_with_bit_false_clears_the_day():
    bm = Bitmap().with_bit(D, True).with_bit(D, False)
    assert not bm.is_set(D)
    assert bm.ticked_ordinals() == set()


def test_with_bit_earlier_than_epoch_keeps_existing_bits():
    bm = Bitmap().with_bit(D, True).with_bit(D - 100, True)
    assert bm.ticked_ordinals() == {D, D - 100}


def test_with_bit_far_later_than_epoch_keeps_existing_bits():
    bm = Bitmap().with_bit(D, True).with_bit(D + 400, True)
    assert bm.ticked_ordinals() == {D, D + 400}


def test_with_bit_does_not_mutate_original():
    bm = Bitmap().with_bit(D, True)
    bm.with_bit(D + 1, True)
    assert bm.ticked_ordinals() == {D}


def test_dict_roundtrip_preserves_ticks():
    bm = Bitmap().with_bit(D, True).with_bit(D + 9, True).with_bit(D - 3, True)
    again = Bitmap.from_dict(json.loads(json.dumps(bm.to_dict())))
    assert again.ticked_ordinals() == bm.ticked_ordinals()


def test_from_dict_none_or_empty_is_empty_bitmap():
    assert Bitmap.from_dict(None).ticked_ordinals() == set()
    assert Bitmap.from_dict({}).ticked_ordinals() == set()


def test_from_dict_malformed_raises_value_error():
    with pytest.raises(ValueError):
        Bitmap.from_dict({"epoch": D, "bits": "!!!not base64!!!"})
    with pytest.raises(ValueError):
        Bitmap.from_dict({"epoch": "x", "bits": ""})


def test_union_combines_ticks_from_both_sides():
    a = Bitmap().with_bit(D, True).with_bit(D + 2, True)
    b = Bitmap().with_bit(D + 1, True).with_bit(D - 50, True)
    assert union(a, b).ticked_ordinals() == {D, D + 1, D + 2, D - 50}


def test_union_is_commutative_and_idempotent():
    a = Bitmap().with_bit(D, True).with_bit(D + 5, True)
    b = Bitmap().with_bit(D + 5, True).with_bit(D + 6, True)
    assert union(a, b) == union(b, a)
    assert union(a, a) == a
    assert union(union(a, b), b) == union(a, b)


def test_union_with_empty_is_identity():
    a = Bitmap().with_bit(D, True)
    assert union(a, Bitmap()) == a
    assert union(Bitmap(), a) == a


def test_five_years_all_ticked_for_ten_habits_stays_small():
    bm = Bitmap()
    for i in range(5 * 365):
        bm = bm.with_bit(D + i, True)
    assert len(json.dumps(bm.to_dict())) < 1024


def test_toggle_today_sets_then_clears_only_today():
    today = date(2026, 11, 11)
    base = Bitmap().with_bit(D - 5, True).with_bit(D - 1, True)
    on = toggle_today(base, today)
    assert on.ticked_ordinals() == {D - 5, D - 1, D}
    off = toggle_today(on, today)
    assert off.ticked_ordinals() == {D - 5, D - 1}


def test_toggle_today_accepts_no_date_other_than_today():
    params = list(inspect.signature(toggle_today).parameters)
    assert params == ["bitmap", "today"]
