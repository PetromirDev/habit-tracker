import copy
from datetime import datetime, timedelta

import pytest

from habit_tracker.analytics import (
    LongestStreak,
    current_streak,
    habits_by_periodicity,
    longest_streak,
    longest_streak_overall,
    struggle_report,
    summarize,
    tracked_habits,
)
from habit_tracker.models import Habit, Periodicity

DAYS = 30

# name: (current streak, longest streak, ended, missed, completion rate)
EXPECTED = {
    "Drink water": (28, 28, 28, 0, 1.0),
    "Read 20 pages": (8, 10, 28, 2, 26 / 28),
    "Meditate": (1, 3, 28, 18, 10 / 28),
    "Clean the flat": (4, 4, 4, 0, 1.0),
    "Call parents": (2, 2, 4, 1, 0.75),
}


def by_name(habits: list[Habit], name: str) -> Habit:
    return next(habit for habit in habits if habit.name == name)


def names(habits: tuple[Habit, ...]) -> list[str]:
    return [habit.name for habit in habits]


def daily(name: str, created_at: datetime, *completions: datetime) -> Habit:
    return Habit(name, "Task", Periodicity.DAILY, created_at, list(completions))


@pytest.mark.parametrize("name", EXPECTED)
def test_demo_habit_matches_expected_values(demo: list[Habit], name: str, now: datetime) -> None:
    current, longest, ended, missed, rate = EXPECTED[name]
    habit = by_name(demo, name)
    entry = next(e for e in struggle_report(demo, now, DAYS) if e.habit.name == name)

    actual = (current_streak(habit, now), longest_streak(habit), entry.ended, entry.missed)
    assert actual == (current, longest, ended, missed), f"{name}: got {actual}"
    assert entry.completion_rate == pytest.approx(rate), f"{name}: rate {entry.completion_rate}"
    assert summarize(habit, now)[1:] == (current, longest)


def test_struggle_report_order(demo: list[Habit], now: datetime) -> None:
    order = [entry.habit.name for entry in struggle_report(demo, now, DAYS)]
    assert order == ["Meditate", "Call parents", "Read 20 pages", "Clean the flat", "Drink water"]


def test_longest_streak_overall_with_one_winner(demo: list[Habit]) -> None:
    result = longest_streak_overall(demo)
    assert (names(result.habits), result.length) == (["Drink water"], 28)


def test_longest_streak_overall_includes_all_tied_habits() -> None:
    created = datetime(2026, 3, 1, 8, 0)
    days = [created + timedelta(days=offset) for offset in range(3)]
    habits = [daily("b walk", created, *days), daily("A run", created, *days), daily("C", created)]

    result = longest_streak_overall(habits)

    assert (names(result.habits), result.length) == (["A run", "b walk"], 3)


def test_longest_streak_overall_without_check_offs(now: datetime) -> None:
    result = longest_streak_overall([daily("Idle", now)])
    assert result == LongestStreak((), 0)


def test_habits_by_periodicity(demo: list[Habit]) -> None:
    daily_names = names(habits_by_periodicity(demo, Periodicity.DAILY))
    weekly_names = names(habits_by_periodicity(demo, Periodicity.WEEKLY))
    assert daily_names == ["Drink water", "Meditate", "Read 20 pages"]
    assert weekly_names == ["Call parents", "Clean the flat"]


def test_tracked_habits_sorts_names_regardless_of_case(now: datetime) -> None:
    habits = [daily("banana", now), daily("Cherry", now), daily("apple", now)]
    assert names(tracked_habits(habits)) == ["apple", "banana", "Cherry"]


# Nothing is checked off today yet, so the streak depends only on whether yesterday was done.
@pytest.mark.parametrize(("days_ago", "expected"), [(1, 1), (2, 0)])
def test_open_current_period_does_not_break_the_streak(
    days_ago: int, expected: int, now: datetime
) -> None:
    created = now - timedelta(days=5)
    habit = daily("Read", created, now - timedelta(days=days_ago))
    assert current_streak(habit, now) == expected


def test_habit_created_today_has_no_streak_and_no_struggle_entry(now: datetime) -> None:
    habit = daily("New", now.replace(hour=8))
    assert current_streak(habit, now) == 0
    assert struggle_report([habit], now, DAYS) == ()


def test_struggle_report_counts_only_periods_inside_the_window(now: datetime) -> None:
    created = now - timedelta(weeks=10)
    # A 14-day window from 4 March starts on 18 February, so the 17th is just outside it.
    read = daily("Read", created, *(now - timedelta(days=d) for d in (1, 2, 3, 4, 14, 15)))
    # The window starts mid-week, and that whole week counts. The 10th is a week too early.
    walk = Habit(
        "Walk",
        "Task",
        Periodicity.WEEKLY,
        created,
        [datetime(2026, 2, 16, 8), datetime(2026, 2, 10, 8)],
    )

    report = struggle_report([read, walk], now, 14)

    actual = {entry.habit.name: (entry.ended, entry.missed) for entry in report}
    assert actual == {"Read": (14, 9), "Walk": (2, 1)}


def test_analytics_leave_the_input_habits_unchanged(demo: list[Habit], now: datetime) -> None:
    before = copy.deepcopy(demo)

    tracked_habits(demo)
    habits_by_periodicity(demo, Periodicity.DAILY)
    longest_streak_overall(demo)
    struggle_report(demo, now, DAYS)
    [summarize(habit, now) for habit in demo]

    assert demo == before
