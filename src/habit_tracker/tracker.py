"""The backend API that the command-line interface and the menu call."""

import sqlite3
from datetime import date, datetime
from pathlib import Path
from types import TracebackType

from habit_tracker import analytics
from habit_tracker.analytics import HabitSummary, LongestStreak, StruggleEntry
from habit_tracker.config import DEFAULT_STRUGGLE_DAYS, DEMO_DB_FILENAME
from habit_tracker.demo_data import demo_habits
from habit_tracker.models import Habit, Periodicity
from habit_tracker.storage import HabitStore


def _now() -> datetime:
    return datetime.now().replace(microsecond=0)


def _saved_id(habit: Habit) -> int:
    if habit.id is None:
        raise ValueError(f"Habit '{habit.name}' has not been saved.")
    return habit.id


class HabitTracker:
    """Service layer between the interfaces and the storage and analytics.

    As long as the user's own store is empty, every action works on the demo
    store. Creating the first habit ends the demo mode.
    """

    def __init__(self, store: HabitStore, demo_store: HabitStore) -> None:
        self._store = store
        self._demo_store = demo_store

    @property
    def is_demo(self) -> bool:
        """``True`` while the user has no habits of their own."""
        return self._store.count() == 0

    @property
    def _active(self) -> HabitStore:
        return self._demo_store if self.is_demo else self._store

    def create(self, name: str, task: str, periodicity: Periodicity) -> Habit:
        """Creates a habit in the user's store, which ends the demo mode.

        Raises:
            InvalidHabitError: If the name or the task is blank.
            DuplicateHabitError: If the user already has a habit with this name.
        """
        return self._store.add(Habit(name, task, periodicity, _now()))

    def check_off(self, name: str) -> HabitSummary:
        """Checks off a habit now and returns its streaks after the check-off.

        Raises:
            HabitNotFoundError: If no habit has the name.
        """
        store = self._active
        habit = store.get(name)
        now = _now()
        habit.check_off(now)
        store.add_completion(_saved_id(habit), now)
        return analytics.summarize(habit, now)

    def undo(self, name: str) -> datetime:
        """Removes the latest check-off of a habit and returns its time.

        Raises:
            HabitNotFoundError: If no habit has the name.
            NothingToUndoError: If the habit has no check-offs.
        """
        store = self._active
        habit = store.get(name)
        removed = habit.undo_last_check_off()
        store.delete_completion(_saved_id(habit), removed)
        return removed

    def edit(self, name: str, new_name: str | None = None, task: str | None = None) -> Habit:
        """Renames a habit and/or changes its task.

        Raises:
            HabitNotFoundError: If no habit has the name.
            InvalidHabitError: If nothing changes, or a new value is blank.
            DuplicateHabitError: If another habit has the new name.
        """
        store = self._active
        habit = store.get(name)
        habit.edit(new_name, task)
        store.update(habit)
        return habit

    def delete(self, name: str) -> None:
        """Deletes a habit and its check-offs.

        Raises:
            HabitNotFoundError: If no habit has the name.
        """
        store = self._active
        store.delete(_saved_id(store.get(name)))

    def list_habits(self, periodicity: Periodicity | None = None) -> tuple[HabitSummary, ...]:
        """Returns all habits, or the ones of one periodicity, sorted by name."""
        habits = self._active.all()
        selected = (
            analytics.tracked_habits(habits)
            if periodicity is None
            else analytics.habits_by_periodicity(habits, periodicity)
        )
        now = _now()
        return tuple(analytics.summarize(habit, now) for habit in selected)

    def summary(self, name: str) -> HabitSummary:
        """Returns one habit with its streaks.

        Raises:
            HabitNotFoundError: If no habit has the name.
        """
        return analytics.summarize(self._active.get(name), _now())

    def longest_streak_overall(self) -> LongestStreak:
        return analytics.longest_streak_overall(self._active.all())

    def struggle(self, days: int = DEFAULT_STRUGGLE_DAYS) -> tuple[StruggleEntry, ...]:
        """Ranks the habits by completion rate in the last ``days`` days, weakest first."""
        return analytics.struggle_report(self._active.all(), _now(), days)

    def reset_demo(self) -> None:
        """Replaces the demo habits with fresh ones whose history ends today."""
        self._demo_store.clear()
        for habit in demo_habits(date.today()):
            self._demo_store.add(habit)

    def close(self) -> None:
        self._store.close()
        self._demo_store.close()

    def __enter__(self) -> "HabitTracker":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def open_tracker(db_path: Path) -> HabitTracker:
    """Opens the user's database and the demo database in the same folder.

    The folder is created if needed. The demo database is filled only when its
    file is new. The caller must close the returned tracker.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    demo_path = db_path.with_name(DEMO_DB_FILENAME)
    demo_is_new = not demo_path.exists()
    store = HabitStore(db_path)
    try:
        demo_store = HabitStore(demo_path)
    except sqlite3.Error:
        store.close()
        raise
    tracker = HabitTracker(store, demo_store)
    if demo_is_new:
        tracker.reset_demo()
    return tracker
