"""Domain model of the habit tracker: periodicities and habits."""

from bisect import insort
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum

from habit_tracker.errors import InvalidHabitError, NothingToUndoError


class Periodicity(Enum):
    """How often a habit must be checked off, fololwing the local calendar."""

    DAILY = "daily"
    WEEKLY = "weekly"

    def period_start(self, moment: datetime) -> date:
        """Returns the day itself for daily habits, or the Monday of its week for weekly ones."""
        day = moment.date()
        if self is Periodicity.WEEKLY:
            return day - timedelta(days=day.weekday())
        return day

    @property
    def step(self) -> timedelta:
        """Time between the starts of two consecutive periods."""
        return timedelta(days=7) if self is Periodicity.WEEKLY else timedelta(days=1)

    @property
    def unit(self) -> str:
        return "week" if self is Periodicity.WEEKLY else "day"

    @property
    def label(self) -> str:
        return self.value.capitalize()


def _require_text(value: str, field_name: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise InvalidHabitError(f"The {field_name} must not be empty.")
    return stripped


@dataclass
class Habit:
    """A habit with a task, a periodicity and its check-off history.

    Attributes:
        name: Unique name, compared without case.
        task: Free text that says what to do.
        periodicity: How often the task must be done.
        created_at: When the habit was created.
        completions: Check-off times, oldest first.
        id: The database ID, or ``None`` until the habit is saved.

    Raises:
        InvalidHabitError: If the name or the task is blank.
    """

    name: str
    task: str
    periodicity: Periodicity
    created_at: datetime
    completions: list[datetime] = field(default_factory=list)
    id: int | None = None

    def __post_init__(self) -> None:
        self.name = _require_text(self.name, "name")
        self.task = _require_text(self.task, "task")

    def check_off(self, at: datetime | None = None) -> datetime:
        """Records a check-off and keeps the completions sorted.

        Args:
            at: The check-off time. Defaults to now, to the second.

        Returns:
            The recorded time.
        """
        moment = at if at is not None else datetime.now().replace(microsecond=0)
        insort(self.completions, moment)
        return moment

    def undo_last_check_off(self) -> datetime:
        """Removes the latest check-off and returns its time.

        Raises:
            NothingToUndoError: If the habit has no check-offs.
        """
        if not self.completions:
            raise NothingToUndoError(f"Habit '{self.name}' has no check-offs to undo.")
        return self.completions.pop()

    def edit(self, name: str | None = None, task: str | None = None) -> None:
        """Renames the habit and/or changes its task. ``None`` keeps a value as it is.

        Raises:
            InvalidHabitError: If both arguments are ``None``, or a new value is blank.
        """
        if name is None and task is None:
            raise InvalidHabitError("Nothing to change.")
        new_name = self.name if name is None else _require_text(name, "name")
        new_task = self.task if task is None else _require_text(task, "task")
        self.name, self.task = new_name, new_task
