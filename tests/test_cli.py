from pathlib import Path

from click.testing import CliRunner, Result

from habit_tracker.cli import cli
from habit_tracker.output import DEMO_BANNER


def run(db_path: Path, *args: str, answer: str | None = None) -> Result:
    return CliRunner().invoke(cli, ["--db", str(db_path), *args], input=answer)


def test_list_on_a_new_path_shows_the_demo_data(tmp_path: Path) -> None:
    result = run(tmp_path / "habits.db", "list")
    assert result.exit_code == 0, result.output
    # rich wraps the banner to the terminal width, so compare it with the line breaks removed.
    assert DEMO_BANNER in " ".join(result.output.split()), result.output
    assert "Drink water" in result.output, result.output


def test_unknown_habit_gives_a_short_error(tmp_path: Path) -> None:
    result = run(tmp_path / "habits.db", "check", "Unknown")
    assert result.exit_code == 1, result.output
    assert "not found" in result.output, result.output
    assert "Traceback" not in result.output, result.output


def test_declined_delete_keeps_the_habit(tmp_path: Path) -> None:
    db_path = tmp_path / "habits.db"

    result = run(db_path, "delete", "Meditate", answer="n\n")

    assert "Delete 'Meditate' and all its check-offs?" in result.output, result.output
    assert "Meditate" in run(db_path, "show", "Meditate").output
    assert run(db_path, "show", "Meditate").exit_code == 0


def test_command_help_opens_no_database(tmp_path: Path) -> None:
    result = run(tmp_path / "habits.db", "list", "--help")
    assert result.exit_code == 0, result.output
    assert "Usage: cli list" in result.output, result.output
    assert list(tmp_path.iterdir()) == [], "--help created database files"
