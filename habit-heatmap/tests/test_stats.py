from stats import completion_pct, current_streak, days_done, longest_streak

T = 739000  # arbitrary "today" ordinal


def run(start: int, length: int) -> set[int]:
    return set(range(start, start + length))


def test_empty_everything_is_zero():
    assert current_streak(set(), T) == 0
    assert longest_streak(set(), T) == 0
    assert days_done(set(), T) == 0


def test_current_streak_today_only():
    assert current_streak({T}, T) == 1


def test_current_streak_counts_today_and_previous_days():
    assert current_streak(run(T - 4, 5), T) == 5


def test_unticked_today_does_not_break_streak_ending_yesterday():
    assert current_streak(run(T - 3, 3), T) == 3  # T-3, T-2, T-1


def test_streak_is_zero_when_yesterday_and_today_both_unticked():
    assert current_streak({T - 2, T - 3}, T) == 0


def test_gap_breaks_streak():
    assert current_streak({T, T - 1, T - 3}, T) == 2


def test_future_ticks_are_ignored():
    assert current_streak({T + 1, T - 1}, T) == 1
    assert days_done({T + 1, T - 1}, T) == 1


def test_longest_streak_picks_longest_run():
    ticked = run(T - 30, 3) | run(T - 20, 5) | run(T - 10, 2)
    assert longest_streak(ticked, T) == 5


def test_longest_streak_includes_run_ending_today_and_ignores_future():
    ticked = run(T - 2, 3) | run(T + 1, 10)
    assert longest_streak(ticked, T) == 3


def test_days_done_counts_ticks_up_to_today():
    assert days_done(run(T - 9, 10), T) == 10


def test_completion_pct_over_window():
    assert completion_pct(run(T - 4, 5), T - 9, T) == 50


def test_completion_pct_ignores_ticks_before_window_start():
    assert completion_pct(run(T - 20, 21), T - 9, T) == 100


def test_completion_pct_rounds_to_int():
    assert completion_pct({T}, T - 2, T) == 33


def test_completion_pct_empty_window_is_zero():
    assert completion_pct({T}, T + 1, T) == 0
