from datetime import datetime, timedelta
from pathlib import Path

import pytest

from garden_water.database import TimersDatabase
from garden_water.models import Timer, TimerId

EXAMPLE_TIMER_1 = Timer(TimerId(1), "test-1", datetime(1970, 5, 1), timedelta(minutes=10), True)
EXAMPLE_TIMER_2 = Timer(TimerId(2), "test-2", datetime(1971, 6, 2), timedelta(minutes=100), False)
EXAMPLE_TIMER_3 = Timer(TimerId(3), "test-3", datetime(1972, 7, 3), timedelta(minutes=1000), True)
EXAMPLE_TIMERS = (EXAMPLE_TIMER_1, EXAMPLE_TIMER_2, EXAMPLE_TIMER_3)


@pytest.fixture
def timers_database(tmpdir: Path) -> TimersDatabase:
    yield TimersDatabase(f"sqlite:///{Path(tmpdir / 'test.db')}")


class TestTimersDatabase:
    def test_add(self, timers_database: TimersDatabase):
        for timer in EXAMPLE_TIMERS:
            timers_database.add(timer)

        assert set(timers_database.get_all()) == set(EXAMPLE_TIMERS)

        for timer in EXAMPLE_TIMERS:
            assert timers_database.get(timer.id) == timer

    def test_add_with_duplicate_id(self, timers_database: TimersDatabase):
        timers_database.add(EXAMPLE_TIMER_1)
        with pytest.raises(ValueError):
            timers_database.add(EXAMPLE_TIMER_1)

    def test_get_when_none(self, timers_database: TimersDatabase):
        assert timers_database.get_all() == ()

    def test_get_timer_when_does_not_exist(self, timers_database: TimersDatabase):
        with pytest.raises(KeyError):
            timers_database.get(TimerId(123))

    def test_remove(self, timers_database: TimersDatabase):
        for timer in EXAMPLE_TIMERS:
            timers_database.add(timer)
        timers_database.remove(EXAMPLE_TIMERS[1].id)
        assert set(timers_database.get_all()) == {EXAMPLE_TIMERS[0], *EXAMPLE_TIMERS[2:]}

    def test_remove_when_does_not_exist(self, timers_database: TimersDatabase):
        assert not timers_database.remove(EXAMPLE_TIMER_1.id)

    def test_contains(self, timers_database: TimersDatabase):
        for timer in EXAMPLE_TIMERS:
            timers_database.add(timer)
        for timer in EXAMPLE_TIMERS:
            assert timer in timers_database

    def test_contains_when_not_exists(self, timers_database: TimersDatabase):
        assert TimerId(123) not in timers_database
