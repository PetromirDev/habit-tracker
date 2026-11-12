from collections.abc import Iterator
from datetime import date, datetime
from pathlib import Path

import pytest

from habit_tracker.demo_data import demo_habits
from habit_tracker.models import Habit
from habit_tracker.storage import HabitStore
from habit_tracker.tracker import HabitTracker, open_tracker

# A fixed clock keeps the expected streaks the same on every day the tests run.
# Noon leaves today's period open, which is how the app sees it during the day.
FIXED_TODAY = date(2026, 3, 4)
NOW = datetime(2026, 3, 4, 12, 0)


@pytest.fixture
def demo() -> list[Habit]:
    return demo_habits(FIXED_TODAY)


@pytest.fixture
def now() -> datetime:
    return NOW


@pytest.fixture
def store() -> Iterator[HabitStore]:
    with HabitStore(":memory:") as habit_store:
        yield habit_store


@pytest.fixture
def tracker(tmp_path: Path) -> Iterator[HabitTracker]:
    with open_tracker(tmp_path / "habits.db") as habit_tracker:
        yield habit_tracker
