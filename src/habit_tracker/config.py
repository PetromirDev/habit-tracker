"""Paths, defaults and limits shared by the whole app."""

from pathlib import Path

DB_ENV_VAR = "HABIT_TRACKER_DB"
DEFAULT_DB_PATH = Path.home() / ".habit_tracker" / "habits.db"
DEMO_DB_FILENAME = "demo.db"
DEFAULT_STRUGGLE_DAYS = 30
RECENT_CHECK_OFFS_SHOWN = 10
DISPLAY_TIME_FORMAT = "%Y-%m-%d %H:%M"
