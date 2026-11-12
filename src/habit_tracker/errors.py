"""Error classes of the habit tracker.

Each message is user-facing text, so the CLI and the menu can print it as is.
"""


class HabitError(Exception):
    """Base class of all expected habit tracker failures."""


class InvalidHabitError(HabitError):
    """A name or task is blank, or an edit changes nothing."""


class HabitNotFoundError(HabitError):
    """No habit has the given name."""


class DuplicateHabitError(HabitError):
    """Another habit already has the name, ignoring case."""


class NothingToUndoError(HabitError):
    """The habit has no check-offs to undo."""
