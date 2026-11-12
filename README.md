# Habit Tracker

A command-line app that tracks daily and weekly habits, counts your streaks and shows which habits you struggle with.

Built as a portfolio project for the course Object Oriented and Functional Programming with Python (DLBDSOOFPP01) at IU International University of Applied Sciences.

## Features

Mandatory functions:

- Create, edit and delete habits. Each habit has a name, a task and a periodicity, daily or weekly.
- Check off a habit at the current time. The app stores when each habit was created and every check-off.
- List all habits, or only the daily or the weekly ones.
- Show the longest streak of one habit, and the longest streak of all habits.
- Five predefined habits with four weeks of example data.
- All data is saved in an SQLite database between sessions.

Extras:

- Undo the latest check-off.
- The current streak of each habit, next to the longest streak.
- A struggle report that ranks habits by how often you missed them in the last 30 days.
- An interactive arrow-key menu, as an alternative to the commands.

## Requirements

- Python 3.10 or later
- `pip`, which comes with Python

## Installation

```bash
git clone https://github.com/PetromirDev/habit-tracker.git
cd habit-tracker
python -m venv .venv
```

Activate the virtual environment on Linux and macOS:

```bash
source .venv/bin/activate
```

Or on Windows (PowerShell or cmd):

```
.venv\Scripts\activate
```

Then install the app with its development tools:

```bash
pip install -e ".[dev]"
```

This installs the `habit` command. `python -m habit_tracker` does the same thing.

## Quick start

On the first run, the app shows five demo habits, so you can try every command at once:

```console
$ habit list
Demo data. Create a habit to start tracking. Changes to demo habits stay in demo.db.
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Name           ┃ Task                    ┃ Period ┃ Created          ┃ Current streak ┃ Longest streak ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ Call parents   │ Call my parents         │ Weekly │ 2026-10-09 08:00 │ 2 weeks        │ 2 weeks        │
│ Clean the flat │ Clean the whole flat    │ Weekly │ 2026-10-09 08:00 │ 4 weeks        │ 4 weeks        │
│ Drink water    │ Drink 2 litres of water │ Daily  │ 2026-10-09 08:00 │ 28 days        │ 28 days        │
│ Meditate       │ Meditate for 10 minutes │ Daily  │ 2026-10-09 08:00 │ 1 day          │ 3 days         │
│ Read 20 pages  │ Read 20 pages of a book │ Daily  │ 2026-10-09 08:00 │ 8 days         │ 10 days        │
└────────────────┴─────────────────────────┴────────┴──────────────────┴────────────────┴────────────────┘
```

Create your first own habit. This ends the demo mode, and from now on the app shows only your habits:

```console
$ habit create Read --task "Read 20 pages" --period daily
Demo data. Create a habit to start tracking. Changes to demo habits stay in demo.db.
Created daily habit 'Read'.
```

If you leave out `--task` or `--period`, the app asks for them.

Complete the task for the current period by checking off the habit. You can check off a habit any time during the day (daily) or the week (weekly):

```console
$ habit check Read
Checked off 'Read' at 2026-11-06 10:42. Current streak: 1 day.
```

Names ignore upper and lower case, so `habit check read` works too. This applies to the letters A to Z only, so `Ärger` and `ärger` are two different names.

## Command reference

Run `habit --help` or `habit COMMAND --help` for all options.

| Command | What it does | Example |
|---|---|---|
| `create NAME` | Creates a habit. Asks for `--task` and `--period` if they are missing. | `habit create Walk --task "Walk 5 km" --period weekly` |
| `check NAME` | Checks off the habit now and shows the current streak. | `habit check Walk` |
| `undo NAME` | Removes the latest check-off. | `habit undo Walk` |
| `edit NAME` | Changes the name (`--name`), the task (`--task`) or both. The periodicity cannot change. | `habit edit Walk --task "Walk 8 km"` |
| `delete NAME` | Deletes the habit and its check-offs after you confirm. `--yes` skips the question. | `habit delete Walk` |
| `list` | Shows all habits with their streaks. `--period` shows only daily or weekly habits. | `habit list --period daily` |
| `show NAME` | Shows the details of one habit and its latest 10 check-offs. | `habit show Read` |
| `streak [NAME]` | With NAME, shows the current and the longest streak of the habit. Without NAME, shows the longest streak of all habits. | `habit streak` |
| `struggle` | Ranks the habits by completion rate, weakest first. `--days` sets the window (default 30). | `habit struggle --days 14` |
| `demo` | Tells you whether the demo mode is on. `--reset` rebuilds the demo data so that it ends today. | `habit demo --reset` |
| `menu` | Opens the interactive menu. | `habit menu` |

Example output:

```console
$ habit streak
Longest streak: 'Drink water' with 28 days.
$ habit struggle
                        Last 30 days
┏━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Habit          ┃ Period ┃ Done ┃ Missed ┃ Completion rate ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Meditate       │ Daily  │ 10   │ 18     │ 36%             │
│ Call parents   │ Weekly │ 3    │ 1      │ 75%             │
│ Read 20 pages  │ Daily  │ 26   │ 2      │ 93%             │
│ Clean the flat │ Weekly │ 4    │ 0      │ 100%            │
│ Drink water    │ Daily  │ 28   │ 0      │ 100%            │
└────────────────┴────────┴──────┴────────┴─────────────────┘
```

If something goes wrong, for example an unknown habit name, the app prints a short message and exits with code 1:

```console
$ habit check Unknown
Error: Habit 'Unknown' not found.
```

## Interactive menu

```bash
habit menu
```

The menu does the same as the commands. Use the arrow keys and Enter to select an action, and select a habit from a list instead of typing its name. Select "Exit" or press Ctrl+C to leave. Ctrl+C inside a question cancels only that action.

## Data storage

- Your habits are saved in `~/.habit_tracker/habits.db`, an SQLite file. The folder is created on the first run.
- `--db PATH` uses another file, for example `habit --db ./test.db list`. The environment variable `HABIT_TRACKER_DB` does the same.
- The demo habits are in `demo.db`, in the same folder. While you have no habits of your own, every command uses `demo.db`. Changes to demo habits stay there.
- If you delete all your own habits, the demo habits show again.
- The demo dates are fixed when `demo.db` is created, so the demo streaks drop after some days. `habit demo --reset` rebuilds the demo data so that it ends today.

## Tests and checks

Run these from the project folder, with the virtual environment active:

```bash
pytest
ruff check .
ruff format --check .
mypy
```

The tests use the demo habits as a fixture with a fixed date, so their expected values never change. They cover the periods and the streak rules, the analytics functions, the database constraints, the demo mode and the error handling of the CLI.

## Project structure

```
habit-tracker/
├── README.md
├── pyproject.toml        package metadata, dependencies and tool settings
├── src/habit_tracker/
│   ├── __init__.py       package docstring
│   ├── __main__.py       runs the CLI for python -m habit_tracker
│   ├── config.py         paths, defaults and limits
│   ├── errors.py         error classes with user-facing messages
│   ├── models.py         Periodicity and Habit
│   ├── schema.sql        the database tables
│   ├── storage.py        HabitStore, the only module that writes SQL
│   ├── analytics.py      streaks and reports as pure functions
│   ├── demo_data.py      the five predefined habits
│   ├── tracker.py        HabitTracker, the backend API, and the demo mode
│   ├── output.py         all terminal output
│   ├── cli.py            the habit command and its subcommands
│   └── menu.py           the interactive menu
└── tests/                pytest tests for each module
```
