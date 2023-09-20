from dataclasses import dataclass
from datetime import timedelta
from typing import Generic, Iterable, TypeVar

import pytest

from garden_water.tests._common import EXAMPLE_TIMERS, create_example_timer
from garden_water.timer_runner import NoTimersError, TimerRunner
from garden_water.timers.collections.listenable import ListenableTimersCollection
from garden_water.timers.collections.memory import InMemoryIdentifiableTimersCollection
from garden_water.timers.intervals import TimeInterval
from garden_water.timers.serialisation import deserialise_daytime
from garden_water.timers.timers import DayTime

T = TypeVar("T")


@dataclass
class MutableItem(Generic[T]):
    value: T


EXAMPLE_TIME_INTERVALS = (
    ("00:00:00", timedelta(hours=1)),
    ("01:30:00", timedelta(hours=1)),
    ("23:00:00", timedelta(hours=2)),
    ("12:00:00", timedelta(hours=1)),
)


def _create_timer_runner(
    start_duration_pairs: Iterable[tuple[str, timedelta]]
) -> tuple[TimerRunner, MutableItem[DayTime]]:
    timers = (create_example_timer(start_time, duration) for start_time, duration in start_duration_pairs)
    current_time = MutableItem[DayTime](DayTime(0, 0, 0))
    return (
        TimerRunner(
            ListenableTimersCollection(InMemoryIdentifiableTimersCollection(timers)),
            lambda: None,
            lambda: None,
            current_time_getter=lambda: current_time.value,
        ),
        current_time,
    )


def _create_interval(start_time: str, duration: timedelta) -> TimeInterval:
    start_time = deserialise_daytime(start_time)
    return TimeInterval(start_time, start_time + duration)


class TestTimerRunner:
    def test_on_off_intervals_no_timers(self):
        timer_runner, _ = _create_timer_runner(())
        assert timer_runner.on_off_intervals == ()

    def test_on_off_intervals(self):
        timer_runner, _ = _create_timer_runner(EXAMPLE_TIME_INTERVALS)
        assert timer_runner.on_off_intervals == (
            _create_interval("01:30:00", timedelta(hours=1)),
            _create_interval("12:00:00", timedelta(hours=1)),
            _create_interval("23:00:00", timedelta(hours=2)),
        )

    def test_is_on_no_timers(self):
        timer_runner, _ = _create_timer_runner(())
        assert not timer_runner.is_on()

    def test_is_on_when_is(self):
        timer_runner, time_setter = _create_timer_runner(EXAMPLE_TIME_INTERVALS)
        for time in (DayTime(0, 0, 0), DayTime(1, 59, 0), DayTime(12, 15, 0), DayTime(23, 0, 0), DayTime(23, 59, 0)):
            time_setter.value = time
            assert timer_runner.is_on()

    def test_is_on_when_not(self):
        timer_runner, time_setter = _create_timer_runner(EXAMPLE_TIME_INTERVALS)
        for time in (DayTime(2, 35, 0), DayTime(22, 30, 0), DayTime(11, 30, 0)):
            time_setter.value = time
            assert not timer_runner.is_on()

    def test_next_interval_no_timers(self):
        timer_runner, _ = _create_timer_runner(())
        with pytest.raises(NoTimersError):
            timer_runner.next_interval()

    def test_next_interval_when_current(self):
        timer_runner, time_setter = _create_timer_runner(EXAMPLE_TIME_INTERVALS)
        time_setter.value = DayTime(0, 0, 0)
        assert timer_runner.next_interval() == (timer_runner.on_off_intervals[2], True)
        time_setter.value = DayTime(1, 59, 0)
        assert timer_runner.next_interval() == (timer_runner.on_off_intervals[0], True)
        time_setter.value = DayTime(12, 15, 0)
        assert timer_runner.next_interval() == (timer_runner.on_off_intervals[1], True)
        time_setter.value = DayTime(23, 0, 0)
        assert timer_runner.next_interval() == (timer_runner.on_off_intervals[2], True)
        time_setter.value = DayTime(23, 59, 0)
        assert timer_runner.next_interval() == (timer_runner.on_off_intervals[2], True)

    def test_next_interval_when_not_current(self):
        timer_runner, time_setter = _create_timer_runner(EXAMPLE_TIME_INTERVALS)
        time_setter.value = DayTime(2, 35, 0)
        assert timer_runner.next_interval() == (timer_runner.on_off_intervals[1], False)
        time_setter.value = DayTime(22, 30, 0)
        assert timer_runner.next_interval() == (timer_runner.on_off_intervals[2], False)
        time_setter.value = DayTime(11, 30, 0)
        assert timer_runner.next_interval() == (timer_runner.on_off_intervals[1], False)
        time_setter.value = DayTime(1, 15, 0)
        assert timer_runner.next_interval() == (timer_runner.on_off_intervals[0], False)
