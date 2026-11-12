"""SQLite persistence for habits and their check-offs."""

import sqlite3
from dataclasses import replace
from datetime import datetime
from importlib.resources import files
from itertools import groupby
from pathlib import Path
from types import TracebackType

from habit_tracker.errors import DuplicateHabitError, HabitNotFoundError
from habit_tracker.models import Habit, Periodicity

_SCHEMA_FILE = "schema.sql"
_DUPLICATE_NAME_MESSAGE = "UNIQUE constraint failed: habit.name"
_HABIT_COLUMNS = "id, name, task, periodicity_code, created_at"


def _format_time(moment: datetime) -> str:
    # The format that SQLite datetime() returns, so the CHECK constraints accept it.
    return moment.isoformat(sep=" ", timespec="seconds")


def _habit_from_row(row: sqlite3.Row, completions: list[datetime]) -> Habit:
    return Habit(
        name=row["name"],
        task=row["task"],
        periodicity=Periodicity(row["periodicity_code"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        completions=completions,
        id=row["id"],
    )


def _raise_if_duplicate(error: sqlite3.IntegrityError, name: str) -> None:
    if _DUPLICATE_NAME_MESSAGE in str(error):
        raise DuplicateHabitError(f"A habit named '{name}' already exists.") from error


class HabitStore:
    """Repository that maps database rows to ``Habit`` objects and back.

    This is the only place that writes SQL, and every write is its own
    transaction. Pass ``":memory:"`` as the path for a throwaway database.
    """

    def __init__(self, path: str | Path) -> None:
        self._connection = sqlite3.connect(path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        # A new database file has user_version 0, the schema sets it to 1.
        (version,) = self._connection.execute("PRAGMA user_version").fetchone()
        if version == 0:
            schema = files("habit_tracker").joinpath(_SCHEMA_FILE).read_text(encoding="utf-8")
            self._connection.executescript(schema)

    def count(self) -> int:
        (total,) = self._connection.execute("SELECT COUNT(*) FROM habit").fetchone()
        return int(total)

    def all(self) -> list[Habit]:
        """Returns all habits with their check-offs, sorted by name ignoring case."""
        rows = self._connection.execute(
            f"SELECT {_HABIT_COLUMNS} FROM habit ORDER BY name"
        ).fetchall()
        completion_rows = self._connection.execute(
            "SELECT habit_id, completed_at FROM completion ORDER BY habit_id, completed_at"
        ).fetchall()
        completions = {
            habit_id: [datetime.fromisoformat(row["completed_at"]) for row in group]
            for habit_id, group in groupby(completion_rows, key=lambda row: row["habit_id"])
        }
        return [_habit_from_row(row, completions.get(row["id"], [])) for row in rows]

    def get(self, name: str) -> Habit:
        """Looks up a habit by name, ignoring case, with its check-offs.

        Raises:
            HabitNotFoundError: If no habit has the name.
        """
        row = self._connection.execute(
            f"SELECT {_HABIT_COLUMNS} FROM habit WHERE name = ?", (name,)
        ).fetchone()
        if row is None:
            raise HabitNotFoundError(f"Habit '{name}' not found.")
        completions = self._connection.execute(
            "SELECT completed_at FROM completion WHERE habit_id = ? ORDER BY completed_at",
            (row["id"],),
        ).fetchall()
        return _habit_from_row(
            row, [datetime.fromisoformat(c["completed_at"]) for c in completions]
        )

    def add(self, habit: Habit) -> Habit:
        """Inserts a new habit with its check-offs and returns a copy that has ``id`` set.

        Raises:
            DuplicateHabitError: If another habit has the name, ignoring case.
        """
        try:
            with self._connection:
                cursor = self._connection.execute(
                    "INSERT INTO habit (name, task, periodicity_code, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        habit.name,
                        habit.task,
                        habit.periodicity.value,
                        _format_time(habit.created_at),
                    ),
                )
                habit_id = cursor.lastrowid
                self._connection.executemany(
                    "INSERT INTO completion (habit_id, completed_at) VALUES (?, ?)",
                    [(habit_id, _format_time(moment)) for moment in habit.completions],
                )
        except sqlite3.IntegrityError as error:
            _raise_if_duplicate(error, habit.name)
            raise
        return replace(habit, completions=list(habit.completions), id=habit_id)

    def update(self, habit: Habit) -> None:
        """Saves a new name or task of a stored habit.

        Raises:
            DuplicateHabitError: If another habit has the new name, ignoring case.
        """
        try:
            with self._connection:
                self._connection.execute(
                    "UPDATE habit SET name = ?, task = ? WHERE id = ?",
                    (habit.name, habit.task, habit.id),
                )
        except sqlite3.IntegrityError as error:
            _raise_if_duplicate(error, habit.name)
            raise

    def delete(self, habit_id: int) -> None:
        with self._connection:
            self._connection.execute("DELETE FROM habit WHERE id = ?", (habit_id,))

    def add_completion(self, habit_id: int, at: datetime) -> None:
        with self._connection:
            self._connection.execute(
                "INSERT INTO completion (habit_id, completed_at) VALUES (?, ?)",
                (habit_id, _format_time(at)),
            )

    def delete_completion(self, habit_id: int, at: datetime) -> None:
        """Deletes one check-off at this time, even if there are duplicates."""
        with self._connection:
            self._connection.execute(
                "DELETE FROM completion WHERE id = "
                "(SELECT id FROM completion WHERE habit_id = ? AND completed_at = ? LIMIT 1)",
                (habit_id, _format_time(at)),
            )

    def clear(self) -> None:
        """Deletes every habit. The schema cascades the delete to the check-offs."""
        with self._connection:
            self._connection.execute("DELETE FROM habit")

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "HabitStore":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
