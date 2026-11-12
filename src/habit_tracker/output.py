"""All terminal output of the command-line interface and the menu."""

from collections.abc import Iterable
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.text import Text

from habit_tracker.analytics import HabitSummary, LongestStreak, StruggleEntry
from habit_tracker.config import DISPLAY_TIME_FORMAT, RECENT_CHECK_OFFS_SHOWN
from habit_tracker.models import Habit, Periodicity

DEMO_BANNER = "Demo data. Create a habit to start tracking. Changes to demo habits stay in demo.db."

console = Console(highlight=False)


def format_time(moment: datetime) -> str:
    return moment.strftime(DISPLAY_TIME_FORMAT)


def format_streak(length: int, periodicity: Periodicity) -> str:
    """Formats a streak with its unit, like ``"8 days"`` or ``"1 week"``."""
    unit = periodicity.unit if length == 1 else f"{periodicity.unit}s"
    return f"{length} {unit}"


def format_rate(rate: float) -> str:
    """Formats a rate between 0 and 1 as a whole percentage, like ``"36%"``."""
    return f"{rate:.0%}"


def _say(message: str, style: str = "") -> None:
    # Habit names may contain [brackets], which rich would otherwise parse as markup.
    console.print(Text(message, style=style))


def print_demo_banner() -> None:
    _say(DEMO_BANNER, "bold yellow")


def print_error(message: str) -> None:
    _say(f"Error: {message}", "red")


def print_no_habits() -> None:
    _say("No habits.")


def print_created(habit: Habit) -> None:
    _say(f"Created {habit.periodicity.label.lower()} habit '{habit.name}'.", "green")


def print_check_off(summary: HabitSummary) -> None:
    habit = summary.habit
    streak = format_streak(summary.current_streak, habit.periodicity)
    _say(
        f"Checked off '{habit.name}' at {format_time(habit.completions[-1])}. "
        f"Current streak: {streak}.",
        "green",
    )


def print_undo(name: str, removed: datetime) -> None:
    _say(f"Removed the check-off of '{name}' from {format_time(removed)}.", "green")


def print_edited(habit: Habit) -> None:
    _say(f"Saved '{habit.name}': {habit.task}", "green")


def print_deleted(name: str) -> None:
    _say(f"Deleted '{name}' and all its check-offs.", "green")


def print_habit_table(summaries: Iterable[HabitSummary]) -> None:
    rows = tuple(summaries)
    if not rows:
        print_no_habits()
        return
    table = Table("Name", "Task", "Period", "Created", "Current streak", "Longest streak")
    for habit, current, longest in rows:
        table.add_row(
            Text(habit.name),
            Text(habit.task),
            habit.periodicity.label,
            format_time(habit.created_at),
            format_streak(current, habit.periodicity),
            format_streak(longest, habit.periodicity),
        )
    console.print(table)


def print_habit_details(summary: HabitSummary) -> None:
    """Prints all fields of a habit, its streaks and its latest check-offs."""
    habit = summary.habit
    details = Table.grid(padding=(0, 2))
    details.add_row("Name", Text(habit.name))
    details.add_row("Task", Text(habit.task))
    details.add_row("Period", habit.periodicity.label)
    details.add_row("Created", format_time(habit.created_at))
    details.add_row("Current streak", format_streak(summary.current_streak, habit.periodicity))
    details.add_row("Longest streak", format_streak(summary.longest_streak, habit.periodicity))
    details.add_row("Check-offs", str(len(habit.completions)))
    console.print(details)
    recent = habit.completions[-RECENT_CHECK_OFFS_SHOWN:][::-1]
    if recent:
        _say(f"\nLatest {len(recent)} check-offs:")
        for moment in recent:
            _say(f"  {format_time(moment)}")


def print_streak(summary: HabitSummary) -> None:
    habit = summary.habit
    _say(
        f"'{habit.name}': current streak {format_streak(summary.current_streak, habit.periodicity)}"
        f", longest streak {format_streak(summary.longest_streak, habit.periodicity)}."
    )


def print_longest_streak(result: LongestStreak) -> None:
    """Prints every habit that shares the longest streak, one per line."""
    if not result.habits:
        _say("No habit has a check-off yet.")
        return
    for habit in result.habits:
        length = format_streak(result.length, habit.periodicity)
        _say(f"Longest streak: '{habit.name}' with {length}.")


def print_struggle_report(entries: Iterable[StruggleEntry], days: int) -> None:
    rows = tuple(entries)
    if not rows:
        _say(f"No habit has an ended period in the last {days} days.")
        return
    table = Table("Habit", "Period", "Done", "Missed", "Completion rate", title=f"Last {days} days")
    for habit, ended, missed, rate in rows:
        table.add_row(
            Text(habit.name),
            habit.periodicity.label,
            str(ended - missed),
            str(missed),
            format_rate(rate),
        )
    console.print(table)


def print_demo_status(is_demo: bool) -> None:
    if is_demo:
        _say("Demo mode is on. Create a habit to start tracking your own habits.")
    else:
        _say("Demo mode is off. The app uses your own habits.")


def print_demo_reset() -> None:
    _say("The demo data was reset and now ends today.", "green")
