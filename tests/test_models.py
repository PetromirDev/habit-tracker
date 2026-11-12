from datetime import date, datetime

import pytest

from habit_tracker.errors import InvalidHabitError, NothingToUndoError
from habit_tracker.models import Habit, Periodicity

CREATED = datetime(2026, 3, 1, 8, 0)


def make_habit(*completions: datetime) -> Habit:
    return Habit("Read", "Read 20 pages", Periodicity.DAILY, CREATED, list(completions))


def test_daily_periods_split_at_midnight() -> None:
    before = Periodicity.DAILY.period_start(datetime(2026, 3, 3, 23, 59, 59))
    after = Periodicity.DAILY.period_start(datetime(2026, 3, 4, 0, 0, 0))
    assert before != after, f"both moments fell in the period {before}"


def test_weekly_periods_split_between_sunday_and_monday() -> None:
    sunday = Periodicity.WEEKLY.period_start(datetime(2026, 3, 8, 23, 59, 59))
    monday = Periodicity.WEEKLY.period_start(datetime(2026, 3, 9, 0, 0, 0))
    assert (sunday, monday) == (date(2026, 3, 2), date(2026, 3, 9))


def test_monday_and_following_sunday_share_a_weekly_period() -> None:
    monday = Periodicity.WEEKLY.period_start(datetime(2026, 3, 2, 0, 0, 0))
    sunday = Periodicity.WEEKLY.period_start(datetime(2026, 3, 8, 23, 59, 59))
    assert monday == sunday == date(2026, 3, 2), f"monday={monday}, sunday={sunday}"


@pytest.mark.parametrize(("name", "task"), [("  ", "Read 20 pages"), ("Read", ""), ("", "\t")])
def test_empty_name_or_task_is_rejected(name: str, task: str) -> None:
    with pytest.raises(InvalidHabitError):
        Habit(name, task, Periodicity.DAILY, CREATED)


def test_undo_without_check_offs_raises() -> None:
    with pytest.raises(NothingToUndoError):
        make_habit().undo_last_check_off()


def test_undo_removes_latest_check_off_even_if_added_out_of_order() -> None:
    habit = make_habit()
    latest = datetime(2026, 3, 3, 21, 0)
    earlier = datetime(2026, 3, 2, 21, 0)
    habit.check_off(latest)
    habit.check_off(earlier)

    removed = habit.undo_last_check_off()

    assert removed == latest, f"removed {removed}, completions left {habit.completions}"
    assert habit.completions == [earlier]


def test_edit_without_arguments_raises() -> None:
    habit = make_habit()
    with pytest.raises(InvalidHabitError):
        habit.edit()
    assert (habit.name, habit.task) == ("Read", "Read 20 pages")


def test_edit_with_empty_task_keeps_the_old_name() -> None:
    habit = make_habit()
    with pytest.raises(InvalidHabitError):
        habit.edit(name="Reading", task=" ")
    assert (habit.name, habit.task) == ("Read", "Read 20 pages")
