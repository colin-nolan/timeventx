import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import Awaitable, Callable, Generic, Iterable, TypeVar
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
) -> tuple[TimerRunner, MutableItem[DayTime], MagicMock, MagicMock]:
    timers = (create_example_timer(start_time, duration) for start_time, duration in start_duration_pairs)
    time_setter = TimeSetter(current_time)

    on_action = MagicMock()
    off_action = MagicMock()

    def current_time_getter() -> DayTime:
        return time_setter.value

    return (
        TimerRunner(
            ListenableTimersCollection(InMemoryIdentifiableTimersCollection(timers)),
            on_action,
            off_action,
            current_time_getter=current_time_getter,
        ),
        time_setter,
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
    async def test_run_no_timers(self):
        await self._test_run(
            (),
            lambda *_: short_sleep(),
            assert_no_magic_mocks_called,
        )

    @pytest.mark.asyncio
    async def test_run_timer_in_future_on_start(self):
        start_time = DayTime(0, 0, 0)

        await self._test_run(
            ((start_time + timedelta(seconds=1), timedelta(seconds=1)),),
            lambda *_: short_sleep(),
            assert_no_magic_mocks_called,
            start_time,
        )

    @pytest.mark.asyncio
    async def test_run_timer_in_future_after_start(self):
        start_time = DayTime(0, 0, 0)

        async def actions_during_run(timer_runner: TimerRunner, *_):
            await short_sleep()
            timer_runner.timers.add(create_example_timer(start_time + timedelta(seconds=1), timedelta(seconds=1)))
            await short_sleep()

        await self._test_run(
            (),
            actions_during_run,
            assert_no_magic_mocks_called,
            start_time,
        )

    @pytest.mark.asyncio
    async def test_run_timer_reached_on_start(self):
        start_time = DayTime(0, 0, 0)

        async def actions_during_run(
            timer_runner: TimerRunner, time_setter: TimeSetter, on_action: MagicMock, off_action: MagicMock
        ):
            on_event = asyncio.Event()
            on_action.side_effect = on_event.set
            time_setter.value = DayTime(0, 0, 1)
            await on_event.wait()

            off_event = asyncio.Event()
            off_action.side_effect = off_event.set
            time_setter.value = DayTime(0, 0, 3)
            await off_event.wait()

        await self._test_run(
            ((start_time + timedelta(seconds=1), timedelta(seconds=1)),),
            actions_during_run,
            start_time=start_time,
        )

    @pytest.mark.asyncio
    async def test_run_timer_reached_after_start(self):
        start_time = DayTime(0, 0, 0)

        async def actions_during_run(
            timer_runner: TimerRunner, time_setter: TimeSetter, on_action: MagicMock, off_action: MagicMock
        ):
            timer_runner.timers.add(create_example_timer(start_time + timedelta(seconds=1), timedelta(seconds=1)))

            on_event = asyncio.Event()
            on_action.side_effect = on_event.set
            time_setter.value = DayTime(0, 0, 1)
            await on_event.wait()

            off_event = asyncio.Event()
            off_action.side_effect = off_event.set
            time_setter.value = DayTime(0, 0, 3)
            await off_event.wait()

        await self._test_run(
            actions_during_run=actions_during_run,
            start_time=start_time,
        )

    @pytest.mark.asyncio
    async def test_run_timer_removed_when_on(self):
        start_time = DayTime(0, 0, 0)

        async def actions_during_run(
            timer_runner: TimerRunner, _: TimeSetter, on_action: MagicMock, off_action: MagicMock
        ):
            timer = create_example_timer(start_time, timedelta(seconds=1))
            timer_runner.timers.add(timer)

            on_event = asyncio.Event()
            on_action.side_effect = on_event.set
            await on_event.wait()

            # Expect off event without timer change when timer is removed
            off_event = asyncio.Event()
            off_action.side_effect = off_event.set
            timer_runner.timers.remove(timer.id)
            await off_event.wait()

        await self._test_run(
            actions_during_run=actions_during_run,
            start_time=start_time,
        )

    @pytest.mark.asyncio
    async def test_run_timer_replaced_when_on(self):
        start_time = DayTime(0, 0, 0)

        async def actions_during_run(
            timer_runner: TimerRunner, _: TimeSetter, on_action: MagicMock, off_action: MagicMock
        ):
            on_event = asyncio.Event()
            on_action.side_effect = on_event.set
            timer = create_example_timer(start_time, timedelta(seconds=10))
            timer_runner.timers.add(timer)
            await on_event.wait()

            replacement_timer = create_example_timer(start_time, timedelta(seconds=5))
            timer_runner.timers.add(replacement_timer)
            timer_runner.timers.remove(timer)
            await short_sleep()
            off_action.assert_not_called()

        await self._test_run(
            actions_during_run=actions_during_run,
            start_time=start_time,
        )

    @pytest.mark.asyncio
    async def test_run_misses_off_time(self):
        start_time = DayTime(0, 0, 0)

        async def actions_during_run(
            timer_runner: TimerRunner, time_setter: TimeSetter, on_action: MagicMock, off_action: MagicMock
        ):
            on_event = asyncio.Event()
            off_event = asyncio.Event()
            on_action.side_effect = on_event.set
            off_event = asyncio.Event()
            off_action.side_effect = off_event.set

            timer = create_example_timer(start_time, timedelta(seconds=1))
            timer_runner.timers.add(timer)
            await on_event.wait()

            time_setter.value = start_time + timedelta(hours=1)
            await off_event.wait()

        await self._test_run(
            actions_during_run=actions_during_run,
            start_time=start_time,
        )

    async def _test_run(
        self,
        start_duration_pairs: StartDurationPairsIterable = (),
        actions_during_run: Callable[
            [TimerRunner, TimeSetter, MagicMock, MagicMock], Awaitable[None]
        ] = lambda *_: None,
        action_assertions: Callable[[MagicMock, MagicMock], None] = lambda *_: None,
        start_time: DayTime = DayTime(0, 0, 0),
    ):
        timer_runner, time_setter, on_action, off_action = _create_timer_runner(start_duration_pairs, start_time)

        stop_event = asyncio.Event()
        task = asyncio.create_task(timer_runner.run(stop_event, timedelta(microseconds=1)))

        await actions_during_run(timer_runner, time_setter, on_action, off_action)

        stop_event.set()
        # Trigger re-evaluation of stop event
        timer_runner.timers_change_event.set()
        await task

        action_assertions(on_action, off_action)


async def short_sleep():
    await asyncio.sleep(0.05)


def assert_no_magic_mocks_called(*magic_mocks: tuple[MagicMock, ...]):
    for magic_mock in magic_mocks:
        magic_mock.assert_not_called()
