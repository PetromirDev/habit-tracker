"""The predefined demo habits with four weeks of example check-offs.

The same data fills the demo database and serves as the test fixture.
"""

from datetime import date, datetime, time, timedelta

from habit_tracker.models import Habit, Periodicity

DEMO_HISTORY_DAYS = 28
_CREATED_TIME = time(8, 0)
# Days 28, 21, 14 and 7 share a weekday, so they fall in 4 consecutive calendar weeks.
_WEEKLY_DAYS = (28, 21, 14, 7)


def demo_habits(today: date) -> list[Habit]:
    """Builds the five unsaved demo habits, three daily and two weekly.

    Each habit is created ``DEMO_HISTORY_DAYS`` before ``today``. Today itself
    has no check-offs, so every current period is still open.
    """

    def at(days_ago: int, hour: int, minute: int = 0) -> datetime:
        return datetime.combine(today - timedelta(days=days_ago), time(hour, minute))

    created_at = at(DEMO_HISTORY_DAYS, _CREATED_TIME.hour, _CREATED_TIME.minute)
    every_day = range(DEMO_HISTORY_DAYS, 0, -1)

    def habit(name: str, task: str, periodicity: Periodicity, done: list[datetime]) -> Habit:
        return Habit(name, task, periodicity, created_at, sorted(done))

    return [
        habit(
            "Drink water",
            "Drink 2 litres of water",
            Periodicity.DAILY,
            [at(day, 20) for day in every_day] + [at(day, 9) for day in _WEEKLY_DAYS],
        ),
        habit(
            "Read 20 pages",
            "Read 20 pages of a book",
            Periodicity.DAILY,
            [at(day, 21) for day in every_day if day not in (20, 9)],
        ),
        habit(
            "Meditate",
            "Meditate for 10 minutes",
            Periodicity.DAILY,
            [at(day, 7) for day in (27, 25, 24, 20, 15, 14, 13, 8, 3, 1)],
        ),
        habit(
            "Clean the flat",
            "Clean the whole flat",
            Periodicity.WEEKLY,
            [at(day, 10) for day in _WEEKLY_DAYS],
        ),
        habit(
            "Call parents",
            "Call my parents",
            Periodicity.WEEKLY,
            [at(28, 18), at(14, 18), at(14, 19, 30), at(7, 18)],
        ),
    ]
