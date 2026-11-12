"""Command-line interface of the habit tracker."""

from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

import click

from habit_tracker import output
from habit_tracker.config import DB_ENV_VAR, DEFAULT_DB_PATH, DEFAULT_STRUGGLE_DAYS
from habit_tracker.errors import HabitError
from habit_tracker.menu import run_menu
from habit_tracker.models import Periodicity
from habit_tracker.tracker import HabitTracker, open_tracker

PERIOD_CHOICE = click.Choice([periodicity.value for periodicity in Periodicity])


def pass_tracker(command: Callable[..., None]) -> Callable[..., None]:
    """Decorator that opens the tracker and passes it to the command as the first argument.

    A ``HabitError`` is printed as a short message, not a traceback.
    """

    @wraps(command)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        ctx = click.get_current_context()
        tracker = open_tracker(ctx.obj)
        ctx.call_on_close(tracker.close)
        if tracker.is_demo:
            output.print_demo_banner()
        try:
            command(tracker, *args, **kwargs)
        except HabitError as error:
            raise click.ClickException(str(error)) from error

    return wrapper


@click.group(invoke_without_command=True)
@click.option(
    "--db",
    "db_path",
    type=click.Path(dir_okay=False, path_type=Path),
    envvar=DB_ENV_VAR,
    default=DEFAULT_DB_PATH,
    show_default=True,
    help=f"The habit database. The environment variable {DB_ENV_VAR} also sets it.",
)
@click.pass_context
def cli(ctx: click.Context, db_path: Path) -> None:
    """Track daily and weekly habits and analyse your streaks."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        return
    ctx.obj = db_path


@cli.command()
@click.argument("name")
@click.option("--task", prompt=True, help="What to do, for example 'Read 20 pages'.")
@click.option("--period", type=PERIOD_CHOICE, prompt=True, help="How often to do it.")
@pass_tracker
def create(tracker: HabitTracker, name: str, task: str, period: str) -> None:
    """Create a habit called NAME."""
    output.print_created(tracker.create(name, task, Periodicity(period)))


@cli.command()
@click.argument("name")
@pass_tracker
def check(tracker: HabitTracker, name: str) -> None:
    """Check off the habit NAME now."""
    output.print_check_off(tracker.check_off(name))


@cli.command()
@click.argument("name")
@pass_tracker
def undo(tracker: HabitTracker, name: str) -> None:
    """Remove the latest check-off of the habit NAME."""
    output.print_undo(name, tracker.undo(name))


@cli.command()
@click.argument("name")
@click.option("--name", "new_name", help="The new name.")
@click.option("--task", help="The new task.")
@pass_tracker
def edit(tracker: HabitTracker, name: str, new_name: str | None, task: str | None) -> None:
    """Change the name or the task of the habit NAME."""
    output.print_edited(tracker.edit(name, new_name, task))


@cli.command()
@click.argument("name")
@click.option("--yes", is_flag=True, help="Delete without asking.")
@pass_tracker
def delete(tracker: HabitTracker, name: str, yes: bool) -> None:
    """Delete the habit NAME and all its check-offs."""
    habit = tracker.summary(name).habit
    if not yes:
        click.confirm(f"Delete '{habit.name}' and all its check-offs?", abort=True)
    tracker.delete(habit.name)
    output.print_deleted(habit.name)


@cli.command("list")
@click.option("--period", type=PERIOD_CHOICE, help="Show only daily or weekly habits.")
@pass_tracker
def list_command(tracker: HabitTracker, period: str | None) -> None:
    """List habits with their streaks."""
    periodicity = Periodicity(period) if period else None
    output.print_habit_table(tracker.list_habits(periodicity))


@cli.command()
@click.argument("name")
@pass_tracker
def show(tracker: HabitTracker, name: str) -> None:
    """Show the details and the latest check-offs of the habit NAME."""
    output.print_habit_details(tracker.summary(name))


@cli.command()
@click.argument("name", required=False)
@pass_tracker
def streak(tracker: HabitTracker, name: str | None) -> None:
    """Show the streaks of NAME, or the longest streak of all habits."""
    if name:
        output.print_streak(tracker.summary(name))
    else:
        output.print_longest_streak(tracker.longest_streak_overall())


@cli.command()
@click.option(
    "--days",
    type=click.IntRange(min=1),
    default=DEFAULT_STRUGGLE_DAYS,
    show_default=True,
    help="How many days back to look.",
)
@pass_tracker
def struggle(tracker: HabitTracker, days: int) -> None:
    """Show the habits you struggled with most, weakest first."""
    output.print_struggle_report(tracker.struggle(days), days)


@cli.command()
@click.option("--reset", is_flag=True, help="Rebuild the demo data so that it ends today.")
@click.option("--yes", is_flag=True, help="Reset without asking.")
@pass_tracker
def demo(tracker: HabitTracker, reset: bool, yes: bool) -> None:
    """Show whether the demo mode is on, or reset the demo data."""
    if not reset:
        output.print_demo_status(tracker.is_demo)
        return
    if not yes:
        click.confirm("Replace the demo habits with fresh demo data?", abort=True)
    tracker.reset_demo()
    output.print_demo_reset()


@cli.command()
@pass_tracker
def menu(tracker: HabitTracker) -> None:
    """Open the interactive menu."""
    run_menu(tracker)


def main() -> None:
    cli()
