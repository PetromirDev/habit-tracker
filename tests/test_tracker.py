from pathlib import Path

from habit_tracker.config import DEMO_DB_FILENAME
from habit_tracker.models import Periodicity
from habit_tracker.storage import HabitStore
from habit_tracker.tracker import HabitTracker, open_tracker

DEMO_HABIT_COUNT = 5


def names(tracker: HabitTracker) -> list[str]:
    return [summary.habit.name for summary in tracker.list_habits()]


def real_count(db_path: Path) -> int:
    with HabitStore(db_path) as store:
        return store.count()


def test_new_folder_starts_in_demo_mode(tmp_path: Path) -> None:
    db_path = tmp_path / "new" / "habits.db"
    with open_tracker(db_path) as tracker:
        assert tracker.is_demo
        assert len(tracker.list_habits()) == DEMO_HABIT_COUNT, names(tracker)
    assert (tmp_path / "new" / DEMO_DB_FILENAME).exists()


def test_check_off_in_demo_mode_leaves_real_database_empty(tmp_path: Path) -> None:
    db_path = tmp_path / "habits.db"
    with open_tracker(db_path) as tracker:
        summary = tracker.check_off("Drink water")
        # The demo gives Drink water a 28-day streak, so today's check-off makes it 29.
        assert summary.current_streak == 29, summary
    assert real_count(db_path) == 0


def test_create_ends_demo_mode(tracker: HabitTracker) -> None:
    tracker.create("Walk", "Walk 5 km", Periodicity.DAILY)
    assert not tracker.is_demo
    assert names(tracker) == ["Walk"]


def test_deleted_demo_habits_stay_deleted_after_reopening(tmp_path: Path) -> None:
    db_path = tmp_path / "habits.db"
    with open_tracker(db_path) as tracker:
        for name in names(tracker):
            tracker.delete(name)
    with open_tracker(db_path) as reopened:
        assert reopened.is_demo
        assert names(reopened) == []


def test_reset_demo_restores_all_demo_habits(tracker: HabitTracker) -> None:
    tracker.delete("Meditate")
    tracker.check_off("Drink water")

    tracker.reset_demo()

    assert len(tracker.list_habits()) == DEMO_HABIT_COUNT, names(tracker)
    assert tracker.summary("Drink water").current_streak == 28


def test_demo_mode_returns_when_all_real_habits_are_deleted(tracker: HabitTracker) -> None:
    tracker.check_off("Meditate")
    tracker.create("Walk", "Walk 5 km", Periodicity.DAILY)

    tracker.delete("walk")

    # Meditate was done yesterday in the demo, so today's check-off makes the streak 2.
    assert tracker.is_demo
    assert len(tracker.list_habits()) == DEMO_HABIT_COUNT
    assert tracker.summary("Meditate").current_streak == 2, "the demo check-off was lost"


def test_undo_is_saved(tmp_path: Path) -> None:
    db_path = tmp_path / "habits.db"
    with open_tracker(db_path) as tracker:
        tracker.create("Walk", "Walk 5 km", Periodicity.DAILY)
        tracker.check_off("Walk")
        tracker.undo("Walk")
    with open_tracker(db_path) as reopened:
        assert reopened.summary("Walk").habit.completions == []
