from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

import pytest

from timeventx.tests._common import (
    EXAMPLE_IDENTIFIABLE_TIMER_1,
    EXAMPLE_TIMER_1,
    EXAMPLE_TIMER_2,
    EXAMPLE_TIMERS,
)
from timeventx.timers.collections.abc import IdentifiableTimersCollection
from timeventx.timers.collections.database import TimersDatabase
from timeventx.timers.collections.listenable import Event, ListenableTimersCollection
from timeventx.timers.collections.memory import InMemoryIdentifiableTimersCollection
from timeventx.timers.timers import IdentifiableTimer, TimerId


def timers_database() -> TimersDatabase:
    # Create temporary database in temp directory
    with TemporaryDirectory() as tmpdir:
        yield TimersDatabase(Path(tmpdir) / "test.db")


def in_memory_timers_collection() -> InMemoryIdentifiableTimersCollection:
    yield InMemoryIdentifiableTimersCollection()


def listenable_timers_collection() -> ListenableTimersCollection:
    yield ListenableTimersCollection(InMemoryIdentifiableTimersCollection())


@pytest.fixture(params=[timers_database, in_memory_timers_collection, listenable_timers_collection])
def timers_collection(request: pytest.FixtureRequest):
    yield from request.param()


@pytest.fixture
def listenable() -> ListenableTimersCollection:
    return next(listenable_timers_collection())


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


class TestListenableTimersCollection:
    def test_timer_add_listener(self, listenable: ListenableTimersCollection):
        listener = MagicMock()
        other_listener = MagicMock()

        listenable.add_listener(Event.TIMER_ADDED, listener)
        listenable.add_listener(Event.TIMER_REMOVED, other_listener)
        listenable.add(EXAMPLE_TIMER_1)

        other_listener.assert_not_called()
        listener.assert_called_once()
        assert listener.call_args.args[0].name == EXAMPLE_TIMER_1.name

    def test_timer_remove_listener(self, listenable: ListenableTimersCollection):
        listener = MagicMock()
        other_listener = MagicMock()

        listenable.add_listener(Event.TIMER_REMOVED, listener)
        added_timer = listenable.add(EXAMPLE_TIMER_1)
        listenable.add_listener(Event.TIMER_ADDED, other_listener)
        listenable.remove(added_timer.id)

        other_listener.assert_not_called()
        listener.assert_called_once()
        assert listener.call_args.args[0] == added_timer.id
