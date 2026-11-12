import sqlite3
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest

from habit_tracker.errors import DuplicateHabitError, HabitNotFoundError
from habit_tracker.models import Habit, Periodicity
from habit_tracker.storage import HabitStore

CREATED = datetime(2026, 3, 1, 8, 0)


def unsaved(habits: list[Habit]) -> list[Habit]:
    return [replace(habit, id=None) for habit in habits]


def completion_count(store: HabitStore) -> int:
    # The store has no public way to count every check-off, so ask SQLite directly.
    (total,) = store._connection.execute("SELECT COUNT(*) FROM completion").fetchone()
    return int(total)


def test_demo_habits_survive_a_round_trip(store: HabitStore, demo: list[Habit]) -> None:
    [store.add(habit) for habit in demo]

    loaded = store.all()

    assert unsaved(loaded) == sorted(demo, key=lambda habit: habit.name.casefold())
    assert unsaved([store.get("call PARENTS")]) == [demo[4]]


def test_duplicate_name_in_different_case_is_rejected(store: HabitStore) -> None:
    store.add(Habit("Read", "Read 20 pages", Periodicity.DAILY, CREATED))
    with pytest.raises(DuplicateHabitError):
        store.add(Habit("READ", "Read a book", Periodicity.WEEKLY, CREATED))
    assert store.count() == 1


def test_rename_to_an_existing_name_is_rejected(store: HabitStore) -> None:
    store.add(Habit("Read", "Read 20 pages", Periodicity.DAILY, CREATED))
    walk = store.add(Habit("Walk", "Walk 5 km", Periodicity.DAILY, CREATED))
    walk.edit(name="read")
    with pytest.raises(DuplicateHabitError):
        store.update(walk)


def test_delete_removes_check_offs_by_cascade(store: HabitStore, demo: list[Habit]) -> None:
    saved = [store.add(habit) for habit in demo]
    remaining = sum(len(habit.completions) for habit in saved[1:])

    assert saved[0].id is not None
    store.delete(saved[0].id)

    assert completion_count(store) == remaining, f"expected {remaining} check-offs to remain"


def test_unknown_periodicity_violates_the_foreign_key(store: HabitStore) -> None:
    # Raw SQL, because the Periodicity enum cannot even build a 'monthly' habit.
    with pytest.raises(sqlite3.IntegrityError):
        store._connection.execute(
            "INSERT INTO habit (name, task, periodicity_code, created_at) "
            "VALUES ('Run', 'Run 5 km', 'monthly', '2026-03-01 08:00:00')"
        )


def test_foreign_keys_are_on_and_schema_version_is_set(store: HabitStore) -> None:
    pragmas = {
        name: store._connection.execute(f"PRAGMA {name}").fetchone()[0]
        for name in ("foreign_keys", "user_version")
    }
    assert pragmas == {"foreign_keys": 1, "user_version": 1}


def test_reopening_a_file_keeps_the_data(tmp_path: Path, demo: list[Habit]) -> None:
    path = tmp_path / "habits.db"
    with HabitStore(path) as store:
        [store.add(habit) for habit in demo]

    with HabitStore(path) as reopened:
        assert len(reopened.all()) == len(demo)
        assert reopened.get("Drink water").completions == demo[0].completions


def test_get_unknown_name_raises(store: HabitStore) -> None:
    with pytest.raises(HabitNotFoundError, match="'Unknown' not found"):
        store.get("Unknown")
