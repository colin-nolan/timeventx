from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from garden_water.tests._common import EXAMPLE_IDENTIFIABLE_TIMER_1, EXAMPLE_TIMER_1, EXAMPLE_TIMERS, EXAMPLE_TIMER_2
from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.collections.database import TimersDatabase
from garden_water.timers.collections.memory import InMemoryIdentifiableTimersCollection
from garden_water.timers.timers import IdentifiableTimer, TimerId


def timers_database() -> TimersDatabase:
    # Create temporary database in temp directory
    with TemporaryDirectory() as tmpdir:
        yield TimersDatabase(Path(tmpdir) / "test.db")


def in_memory_collection() -> InMemoryIdentifiableTimersCollection:
    yield InMemoryIdentifiableTimersCollection()


@pytest.fixture(params=[timers_database, in_memory_collection])
def timers_collection(request):
    yield from request.param()


class TestIdentifiableTimersCollection:
    def test_len_when_zero(self, timers_collection: IdentifiableTimersCollection):
        assert len(timers_collection) == 0

    def test_len(self, timers_collection: IdentifiableTimersCollection):
        timers_collection.add(EXAMPLE_TIMER_1)
        timers_collection.add(EXAMPLE_TIMER_2)
        assert len(timers_collection) == 2

    def test_add(self, timers_collection: IdentifiableTimersCollection):
        added_timer = timers_collection.add(EXAMPLE_TIMER_1)
        assert added_timer.to_timer() == EXAMPLE_TIMER_1

    def test_add_identifiable_timer(self, timers_collection: IdentifiableTimersCollection):
        added_timer = timers_collection.add(EXAMPLE_IDENTIFIABLE_TIMER_1)
        assert added_timer == EXAMPLE_IDENTIFIABLE_TIMER_1

    def test_add_many(self, timers_collection: IdentifiableTimersCollection):
        added_timers = set()
        for timer in EXAMPLE_TIMERS:
            added_timers.add(timers_collection.add(timer))
        assert {timer.to_timer() if isinstance(timer, IdentifiableTimer) else timer for timer in EXAMPLE_TIMERS} == {
            timer.to_timer() for timer in added_timers
        }

    def test_add_with_duplicate_id(self, timers_collection: IdentifiableTimersCollection):
        timers_collection.add(EXAMPLE_IDENTIFIABLE_TIMER_1)
        with pytest.raises(ValueError):
            timers_collection.add(EXAMPLE_IDENTIFIABLE_TIMER_1)

    def test_get(self, timers_collection: IdentifiableTimersCollection):
        timers_collection.add(EXAMPLE_IDENTIFIABLE_TIMER_1)
        assert timers_collection.get(EXAMPLE_IDENTIFIABLE_TIMER_1.id) == EXAMPLE_IDENTIFIABLE_TIMER_1

    def test_get_timer_when_does_not_exist(self, timers_collection: IdentifiableTimersCollection):
        with pytest.raises(KeyError):
            timers_collection.get(TimerId(123))

    def test_remove(self, timers_collection: IdentifiableTimersCollection):
        added_timers = []
        for timer in EXAMPLE_TIMERS:
            added_timers.append(timers_collection.add(timer))
        timers_collection.remove(added_timers[1].id)
        assert set(timers_collection) == {
            added_timers[0],
            *added_timers[2:],
        }

    def test_remove_when_does_not_exist(self, timers_collection: IdentifiableTimersCollection):
        assert not timers_collection.remove(EXAMPLE_IDENTIFIABLE_TIMER_1.id)

    def test_contains(self, timers_collection: IdentifiableTimersCollection):
        added_timers = []
        for timer in EXAMPLE_TIMERS:
            added_timers.append(timers_collection.add(timer))
        for timer in added_timers:
            assert timer in timers_collection

    def test_contains_when_not_present(self, timers_collection: IdentifiableTimersCollection):
        assert EXAMPLE_IDENTIFIABLE_TIMER_1 not in timers_collection

    def test_contains_when_not_exists(self, timers_collection: IdentifiableTimersCollection):
        assert TimerId(123) not in timers_collection
