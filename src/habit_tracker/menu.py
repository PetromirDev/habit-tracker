"""Interactive arrow-key menu for users who prefer not to type commands."""

from collections.abc import Callable
from typing import Any

import questionary

from habit_tracker import output
from habit_tracker.config import DEFAULT_STRUGGLE_DAYS
from habit_tracker.errors import HabitError
from habit_tracker.models import Periodicity
from habit_tracker.tracker import HabitTracker

EXIT = "Exit"


class _Cancelled(Exception):
    """The user pressed Ctrl+C in a prompt, which cancels the current action."""


def _ask(question: questionary.Question) -> Any:
    # questionary returns None on Ctrl+C instead of raising.
    answer = question.ask()
    if answer is None:
        raise _Cancelled
    return answer


def _choose_habit(tracker: HabitTracker) -> str:
    names = [summary.habit.name for summary in tracker.list_habits()]
    if not names:
        output.print_no_habits()
        raise _Cancelled
    return str(_ask(questionary.select("Which habit?", choices=names)))


def _create(tracker: HabitTracker) -> None:
    name = _ask(questionary.text("Name:"))
    task = _ask(questionary.text("Task:"))
    period = _ask(questionary.select("Period:", choices=[p.value for p in Periodicity]))
    output.print_created(tracker.create(name, task, Periodicity(period)))


def _check_off(tracker: HabitTracker) -> None:
    output.print_check_off(tracker.check_off(_choose_habit(tracker)))


def _undo(tracker: HabitTracker) -> None:
    name = _choose_habit(tracker)
    output.print_undo(name, tracker.undo(name))


def _edit(tracker: HabitTracker) -> None:
    habit = tracker.summary(_choose_habit(tracker)).habit
    new_name = _ask(questionary.text("Name:", default=habit.name))
    task = _ask(questionary.text("Task:", default=habit.task))
    output.print_edited(
        tracker.edit(
            habit.name,
            new_name if new_name != habit.name else None,
            task if task != habit.task else None,
        )
    )


def _delete(tracker: HabitTracker) -> None:
    name = _choose_habit(tracker)
    if _ask(questionary.confirm(f"Delete '{name}' and all its check-offs?", default=False)):
        tracker.delete(name)
        output.print_deleted(name)


def _list(tracker: HabitTracker) -> None:
    output.print_habit_table(tracker.list_habits())


def _show(tracker: HabitTracker) -> None:
    output.print_habit_details(tracker.summary(_choose_habit(tracker)))


def _streaks(tracker: HabitTracker) -> None:
    output.print_longest_streak(tracker.longest_streak_overall())


def _struggle(tracker: HabitTracker) -> None:
    output.print_struggle_report(tracker.struggle(), DEFAULT_STRUGGLE_DAYS)


def _reset_demo(tracker: HabitTracker) -> None:
    if _ask(questionary.confirm("Replace the demo habits with fresh demo data?", default=False)):
        tracker.reset_demo()
        output.print_demo_reset()


ACTIONS: dict[str, Callable[[HabitTracker], None]] = {
    "Create habit": _create,
    "Check off habit": _check_off,
    "Undo check-off": _undo,
    "Edit habit": _edit,
    "Delete habit": _delete,
    "List habits": _list,
    "Show habit": _show,
    "Streaks": _streaks,
    "Struggle report": _struggle,
    "Reset demo data": _reset_demo,
}


def run_menu(tracker: HabitTracker) -> None:
    """Shows the menu in a loop until the user picks Exit or presses Ctrl+C.

    Each item uses the same tracker method and output function as the matching
    command. A ``HabitError`` is printed and the menu keeps running.
    """
    while True:
        choice = questionary.select("What do you want to do?", choices=[*ACTIONS, EXIT]).ask()
        if choice is None or choice == EXIT:
            return
        if tracker.is_demo:
            output.print_demo_banner()
        try:
            ACTIONS[choice](tracker)
        except HabitError as error:
            output.print_error(str(error))
        except _Cancelled:
            continue
