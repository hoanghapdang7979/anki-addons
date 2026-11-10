"""Pure streak/summary statistics over a set of ticked day ordinals.
No aqt/anki imports.
"""


def current_streak(ticked: set[int], today: int) -> int:
    """Consecutive ticked days ending today, or ending yesterday if today is not
    ticked yet (an unticked *today* does not break the streak)."""
    day = today if today in ticked else today - 1
    count = 0
    while day in ticked:
        count += 1
        day -= 1
    return count


def longest_streak(ticked: set[int], today: int) -> int:
    best = run = 0
    prev: int | None = None
    for day in sorted(d for d in ticked if d <= today):
        run = run + 1 if prev is not None and day == prev + 1 else 1
        best = max(best, run)
        prev = day
    return best


def days_done(ticked: set[int], today: int) -> int:
    return sum(1 for d in ticked if d <= today)


def completion_pct(ticked: set[int], start: int, today: int) -> int:
    """Percent of days in [start, today] that are ticked, rounded to an int."""
    total = today - start + 1
    if total <= 0:
        return 0
    done = sum(1 for d in ticked if start <= d <= today)
    return round(done * 100 / total)


def streak_runs(ticked: set[int]) -> dict[int, int]:
    """For every ticked day, the length of the run of consecutive ticked days ending on it."""
    runs: dict[int, int] = {}
    for day in sorted(ticked):
        runs[day] = runs.get(day - 1, 0) + 1
    return runs
