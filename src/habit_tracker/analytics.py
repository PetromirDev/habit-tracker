"""Habit analytics written as pure functions."""

from collections.abc import Iterable
from datetime import date, datetime, timedelta
from itertools import pairwise
from typing import NamedTuple

from habit_tracker.models import Habit, Periodicity


class HabitSummary(NamedTuple):
    """A habit with its current and longest streak, counted in periods."""

    habit: Habit
    current_streak: int
    longest_streak: int


class LongestStreak(NamedTuple):
    """The habits that share the longest streak, and its length in periods."""

    habits: tuple[Habit, ...]
    length: int


class StruggleEntry(NamedTuple):
    """How well a habit was kept in the ended periods of a time window."""

    habit: Habit
    ended: int
    missed: int
    completion_rate: float


def _name_key(habit: Habit) -> str:
    return habit.name.casefold()


def _done_periods(habit: Habit) -> frozenset[date]:
    return frozenset(map(habit.periodicity.period_start, habit.completions))


def _runs(habit: Habit) -> tuple[tuple[date, ...], ...]:
    """Splits the done periods into runs of consecutive periods, oldest first."""
    starts = sorted(_done_periods(habit))
    step = habit.periodicity.step
    # A new run begins at the first period and after every gap.
    run_begins = [i for i, start in enumerate(starts) if i == 0 or start - starts[i - 1] != step]
    return tuple(tuple(starts[begin:end]) for begin, end in pairwise([*run_begins, len(starts)]))


def _ended_periods(habit: Habit, since: date, now: datetime) -> tuple[date, ...]:
    """Period starts from ``since``, or from the creation period if later, up to the current one.

    The current period is left out because it has not ended yet.
    """
    periodicity = habit.periodicity
    first = max(since, periodicity.period_start(habit.created_at))
    total = (periodicity.period_start(now) - first) // periodicity.step
    return tuple(first + periodicity.step * index for index in range(total))


def tracked_habits(habits: Iterable[Habit]) -> tuple[Habit, ...]:
    """Returns all habits sorted by name, ignoring case."""
    return tuple(sorted(habits, key=_name_key))


def habits_by_periodicity(habits: Iterable[Habit], periodicity: Periodicity) -> tuple[Habit, ...]:
    return tracked_habits(habit for habit in habits if habit.periodicity is periodicity)


def longest_streak(habit: Habit) -> int:
    return max((len(run) for run in _runs(habit)), default=0)


def longest_streak_overall(habits: Iterable[Habit]) -> LongestStreak:
    """Returns the habits with the highest longest streak.

    Daily and weekly streaks are compared by their number of periods, and all
    tied habits are returned, sorted by name. If no habit has a check-off, the
    result is ``LongestStreak((), 0)``.
    """
    streaks = tuple((habit, longest_streak(habit)) for habit in habits)
    best = max((length for _, length in streaks), default=0)
    winners = (habit for habit, length in streaks if length == best)
    return LongestStreak(tracked_habits(winners), best) if best else LongestStreak((), 0)


def current_streak(habit: Habit, now: datetime) -> int:
    """Returns how many done periods in a row lead up to ``now``.

    An unchecked current period does not break the streak yet, so counting
    starts from the previous period in that case.
    """
    runs = _runs(habit)
    if not runs:
        return 0
    current = habit.periodicity.period_start(now)
    last_run = runs[-1]
    return len(last_run) if last_run[-1] in (current, current - habit.periodicity.step) else 0


def _struggle_entry(habit: Habit, now: datetime, days: int) -> StruggleEntry:
    done = _done_periods(habit)
    window_start = habit.periodicity.period_start(now - timedelta(days=days))
    ended = _ended_periods(habit, window_start, now)
    missed = sum(1 for start in ended if start not in done)
    rate = (len(ended) - missed) / len(ended) if ended else 0.0
    return StruggleEntry(habit, len(ended), missed, rate)


def _struggle_rank(entry: StruggleEntry) -> tuple[float, int, str]:
    return entry.completion_rate, -entry.missed, _name_key(entry.habit)


def struggle_report(habits: Iterable[Habit], now: datetime, days: int) -> tuple[StruggleEntry, ...]:
    """Ranks habits by how well they were kept in the last ``days`` days.

    Only ended periods count, so a habit created in the current period is left
    out. The lowest completion rate comes first, then the most missed periods,
    then the name.
    """
    entries = (_struggle_entry(habit, now, days) for habit in habits)
    kept = (entry for entry in entries if entry.ended > 0)
    return tuple(sorted(kept, key=_struggle_rank))


def summarize(habit: Habit, now: datetime) -> HabitSummary:
    return HabitSummary(habit, current_streak(habit, now), longest_streak(habit))
