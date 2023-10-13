import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import Awaitable, Callable, Generic, Iterable, Optional, TypeVar
from unittest.mock import MagicMock

import pytest

from garden_water.tests._common import (
    EXAMPLE_TIMER_1,
    EXAMPLE_TIMERS,
    create_example_timer,
)
from garden_water.timer_runner import NoTimersError, TimerRunner
from garden_water.timers.collections.listenable import ListenableTimersCollection
from garden_water.timers.collections.memory import InMemoryIdentifiableTimersCollection
from garden_water.timers.intervals import TimeInterval
from garden_water.timers.serialisation import deserialise_daytime
from garden_water.timers.timers import DayTime

EXAMPLE_TIME_INTERVALS = (
    ("00:00:00", timedelta(hours=1)),
    ("01:30:00", timedelta(hours=1)),
    ("23:00:00", timedelta(hours=2)),
    ("12:00:00", timedelta(hours=1)),
)
T = TypeVar("T")


@dataclass
class MutableItem(Generic[T]):
    value: T


StartDurationPairsIterable = Iterable[tuple[str, timedelta]]
TimeSetter = MutableItem[DayTime]


def _create_timer_runner(
    start_duration_pairs: StartDurationPairsIterable = (), current_time: DayTime = DayTime(0, 0, 0)
) -> tuple[TimerRunner, MutableItem[DayTime], asyncio.Semaphore, MagicMock, MagicMock]:
    timers = (create_example_timer(start_time, duration) for start_time, duration in start_duration_pairs)
    time_setter = TimeSetter(current_time)
    time_request_semaphore = asyncio.Semaphore()

    on_action = MagicMock()
    off_action = MagicMock()

    def current_time_getter() -> DayTime:
        time_request_semaphore.release()
        return time_setter.value

    return (
        TimerRunner(
            ListenableTimersCollection(InMemoryIdentifiableTimersCollection(timers)),
            on_action,
            off_action,
            current_time_getter=current_time_getter,
        ),
        time_setter,
        time_request_semaphore,
        on_action,
        off_action,
    )


def _create_interval(start_time: str, duration: timedelta) -> TimeInterval:
    start_time = deserialise_daytime(start_time)
    return TimeInterval(start_time, start_time + duration)


class TestTimerRunner:
    def test_on_off_intervals_no_timers(self):
        timer_runner, *_ = _create_timer_runner()
        assert timer_runner.on_off_intervals == ()

    def test_on_off_intervals(self):
        timer_runner, *_ = _create_timer_runner(EXAMPLE_TIME_INTERVALS)
        assert timer_runner.on_off_intervals == (
            _create_interval("01:30:00", timedelta(hours=1)),
            _create_interval("12:00:00", timedelta(hours=1)),
            _create_interval("23:00:00", timedelta(hours=2)),
        )

    def test_is_on_no_timers(self):
        timer_runner, *_ = _create_timer_runner()
        assert not timer_runner.is_on()

    def test_is_on_when_is(self):
        timer_runner, time_setter, *_ = _create_timer_runner(EXAMPLE_TIME_INTERVALS)
        for time in (DayTime(0, 0, 0), DayTime(1, 59, 0), DayTime(12, 15, 0), DayTime(23, 0, 0), DayTime(23, 59, 0)):
            time_setter.value = time
            assert timer_runner.is_on()

    def test_is_on_when_not(self):
        timer_runner, time_setter, *_ = _create_timer_runner(EXAMPLE_TIME_INTERVALS)
        for time in (DayTime(2, 35, 0), DayTime(22, 30, 0), DayTime(11, 30, 0)):
            time_setter.value = time
            assert not timer_runner.is_on()

    def test_next_interval_no_timers(self):
        timer_runner, *_ = _create_timer_runner()
        with pytest.raises(NoTimersError):
            timer_runner.next_interval()

    def test_next_interval_when_current(self):
        timer_runner, time_setter, *_ = _create_timer_runner(EXAMPLE_TIME_INTERVALS)
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
        timer_runner, time_setter, *_ = _create_timer_runner(EXAMPLE_TIME_INTERVALS)
        time_setter.value = DayTime(2, 35, 0)
        assert timer_runner.next_interval() == (timer_runner.on_off_intervals[1], False)
        time_setter.value = DayTime(22, 30, 0)
        assert timer_runner.next_interval() == (timer_runner.on_off_intervals[2], False)
        time_setter.value = DayTime(11, 30, 0)
        assert timer_runner.next_interval() == (timer_runner.on_off_intervals[1], False)
        time_setter.value = DayTime(1, 15, 0)
        assert timer_runner.next_interval() == (timer_runner.on_off_intervals[0], False)

    @pytest.mark.asyncio
    async def test_run_no_timers2(self):
        await self._test_run(
            (),
            lambda *_: short_sleep(),
            lambda on_action, off_action: (on_action.assert_not_called(), off_action.assert_not_called()),
        )

    @pytest.mark.asyncio
    async def test_run_timer_in_future_on_start(self):
        current_time = DayTime(0, 0, 0)

        await self._test_run(
            ((current_time + timedelta(seconds=1), timedelta(seconds=1)),),
            lambda *_: short_sleep(),
            lambda on_action, off_action: (on_action.assert_not_called(), off_action.assert_not_called()),
            current_time,
        )

    @pytest.mark.asyncio
    async def test_run_timer_in_future_after_start(self):
        current_time = DayTime(0, 0, 0)

        async def actions_during_run(timer_runner: TimerRunner, *_):
            await asyncio.sleep(0.05)
            timer_runner.timers.add(create_example_timer(current_time + timedelta(seconds=1), timedelta(seconds=1)))
            await asyncio.sleep(0.05)

        await self._test_run(
            (),
            actions_during_run,
            lambda on_action, off_action: (on_action.assert_not_called(), off_action.assert_not_called()),
            current_time,
        )

    async def _test_run(
        self,
        start_duration_pairs: StartDurationPairsIterable,
        actions_during_run: Callable[[TimerRunner, TimeSetter], Awaitable[None]],
        action_assertions: Callable[[MagicMock, MagicMock], None],
        start_time: DayTime = DayTime(0, 0, 0),
    ):
        timer_runner, time_setter, time_setter_semaphore, on_action, off_action = _create_timer_runner(
            start_duration_pairs, start_time
        )

        stop_event = asyncio.Event()
        task = asyncio.create_task(timer_runner.run(stop_event))

        await actions_during_run(timer_runner, time_setter)

        stop_event.set()
        # Trigger re-evaluation of stop event
        timer_runner.timers_change_event.set()
        await task

        action_assertions(on_action, off_action)


async def short_sleep():
    await asyncio.sleep(0.05)
