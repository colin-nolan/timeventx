from pathlib import Path

import pytest

from garden_water.database import TimersDatabase
from garden_water.models import IdentifiableTimer, TimerId
from garden_water.tests._common import (
    EXAMPLE_IDENTIFIABLE_TIMER_1,
    EXAMPLE_TIMER_1,
    EXAMPLE_TIMERS,
)


@pytest.fixture
def timers_database(tmpdir: Path) -> TimersDatabase:
    yield TimersDatabase(f"sqlite:///{Path(tmpdir / 'test.db')}")


class TestTimersDatabase:
    def test_add(self, timers_database: TimersDatabase):
        added_timer = timers_database.add(EXAMPLE_TIMER_1)
        assert added_timer.to_timer() == EXAMPLE_TIMER_1

    def test_add_identifiable_timer(self, timers_database: TimersDatabase):
        added_timer = timers_database.add(EXAMPLE_IDENTIFIABLE_TIMER_1)
        assert added_timer == EXAMPLE_IDENTIFIABLE_TIMER_1

    def test_add_many(self, timers_database: TimersDatabase):
        added_timers = set()
        for timer in EXAMPLE_TIMERS:
            added_timers.add(timers_database.add(timer))
        assert {timer.to_timer() if isinstance(timer, IdentifiableTimer) else timer for timer in EXAMPLE_TIMERS} == {
            timer.to_timer() for timer in added_timers
        }

    def test_add_with_duplicate_id(self, timers_database: TimersDatabase):
        timers_database.add(EXAMPLE_IDENTIFIABLE_TIMER_1)
        with pytest.raises(ValueError):
            timers_database.add(EXAMPLE_IDENTIFIABLE_TIMER_1)

    def test_get(self, timers_database: TimersDatabase):
        timers_database.add(EXAMPLE_IDENTIFIABLE_TIMER_1)
        assert timers_database.get(EXAMPLE_IDENTIFIABLE_TIMER_1.id) == EXAMPLE_IDENTIFIABLE_TIMER_1

    def test_get_when_none(self, timers_database: TimersDatabase):
        assert timers_database.get_all() == ()

    def test_get_timer_when_does_not_exist(self, timers_database: TimersDatabase):
        with pytest.raises(KeyError):
            timers_database.get(TimerId(123))

    def test_remove(self, timers_database: TimersDatabase):
        added_timers = []
        for timer in EXAMPLE_TIMERS:
            added_timers.append(timers_database.add(timer))
        timers_database.remove(added_timers[1].id)
        assert set(timers_database.get_all()) == {
            added_timers[0],
            *added_timers[2:],
        }

    def test_remove_when_does_not_exist(self, timers_database: TimersDatabase):
        assert not timers_database.remove(EXAMPLE_IDENTIFIABLE_TIMER_1.id)

    def test_contains(self, timers_database: TimersDatabase):
        added_timers = []
        for timer in EXAMPLE_TIMERS:
            added_timers.append(timers_database.add(timer))
        for timer in added_timers:
            assert timer in timers_database

    def test_contains_when_not_present(self, timers_database: TimersDatabase):
        assert EXAMPLE_IDENTIFIABLE_TIMER_1 not in timers_database

    def test_contains_when_not_exists(self, timers_database: TimersDatabase):
        assert TimerId(123) not in timers_database
