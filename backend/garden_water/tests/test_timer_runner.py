import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import Awaitable, Callable, Generic, Iterable, TypeVar
from unittest.mock import MagicMock

import pytest

from garden_water.actions import ActionController
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


class MockActionController(ActionController):
    def __init__(self):
        super().__init__()
        self.on_action_mock = MagicMock()
        self.on_action_called_event = asyncio.Event()
        self.off_action_mock = MagicMock()
        self.off_action_called_event = asyncio.Event()

    async def on_action(self):
        self.on_action_mock()
        self.on_action_called_event.set()

    async def off_action(self):
        self.off_action_mock()
        self.off_action_called_event.set()

    def assert_actions_called(self, on_action: bool = True, off_action: bool = True):
        if on_action:
            self.on_action_mock.assert_called()
        else:
            self.on_action_mock.assert_not_called()
        if off_action:
            self.off_action_mock.assert_called()
        else:
            self.off_action_mock.assert_not_called()


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
            actions_during_run=lambda *_: _short_sleep(),
            action_assertions=lambda action_controller: action_controller.assert_actions_called(False, False),
        )

    @pytest.mark.asyncio
    async def test_run_when_already_running(self):
        timer_runner, *_ = _create_timer_runner()
        run_tasks = []
        with pytest.raises(RuntimeError):
            try:
                run_tasks.extend((asyncio.create_task(timer_runner.run()), asyncio.create_task(timer_runner.run())))
                await asyncio.gather(*run_tasks)
            finally:
                for task in run_tasks:
                    task.cancel()

    @pytest.mark.asyncio
    async def test_run_when_stop_flag_set(self):
        timer_runner, *_ = _create_timer_runner()
        timer_runner.run_stop_event.set()
        with pytest.raises(RuntimeError):
            await timer_runner.run()

    @pytest.mark.asyncio
    async def test_run_timer_in_future_on_start(self):
        start_time = DayTime(0, 0, 0)

        await self._test_run(
            ((start_time + timedelta(seconds=1), timedelta(seconds=1)),),
            lambda *_: _short_sleep(),
            lambda action_controller: action_controller.assert_actions_called(False, False),
            start_time,
        )

    @pytest.mark.asyncio
    async def test_run_timer_in_future_after_start(self):
        start_time = DayTime(0, 0, 0)

        async def actions_during_run(timer_runner: TimerRunner, *_):
            await _short_sleep()
            timer_runner.timers.add(create_example_timer(start_time + timedelta(seconds=1), timedelta(seconds=1)))
            await _short_sleep()

        await self._test_run(
            (),
            actions_during_run,
            lambda action_controller: action_controller.assert_actions_called(False, False),
            start_time,
        )

    @pytest.mark.asyncio
    async def test_run_timer_reached_on_start(self):
        start_time = DayTime(0, 0, 0)

        async def actions_during_run(
            timer_runner: TimerRunner, time_setter: TimeSetter, action_controller: MockActionController
        ):
            await action_controller.on_action_called_event.wait()
            time_setter.value = DayTime(0, 0, 1)
            await action_controller.off_action_called_event.wait()

        await self._test_run(
            ((start_time, timedelta(seconds=1)),),
            actions_during_run,
            lambda action_controller: action_controller.assert_actions_called(),
            start_time,
        )

    @pytest.mark.asyncio
    async def test_run_timer_reached_after_start(self):
        start_time = DayTime(0, 0, 0)

        async def actions_during_run(
            timer_runner: TimerRunner, time_setter: TimeSetter, action_controller: MockActionController
        ):
            timer_runner.timers.add(create_example_timer(start_time + timedelta(seconds=1), timedelta(seconds=1)))

            time_setter.value = DayTime(0, 0, 1)
            await action_controller.on_action_called_event.wait()

            time_setter.value = DayTime(0, 0, 2)
            await action_controller.off_action_called_event.wait()

        await self._test_run(
            actions_during_run=actions_during_run,
            start_time=start_time,
        )

    @pytest.mark.asyncio
    async def test_run_timer_removed_when_on(self):
        start_time = DayTime(0, 0, 0)

        async def actions_during_run(
            timer_runner: TimerRunner, time_setter: TimeSetter, action_controller: MockActionController
        ):
            timer = create_example_timer(start_time, timedelta(seconds=1))
            timer_runner.timers.add(timer)
            await action_controller.on_action_called_event.wait()

            timer_runner.timers.remove(timer.id)

            await action_controller.off_action_called_event.wait()

        await self._test_run(
            actions_during_run=actions_during_run,
            start_time=start_time,
        )

    @pytest.mark.asyncio
    async def test_run_timer_on_replaced_with_on(self):
        start_time = DayTime(0, 0, 0)

        async def actions_during_run(
            timer_runner: TimerRunner, time_setter: TimeSetter, action_controller: MockActionController
        ):
            timer = create_example_timer(start_time, timedelta(seconds=10))
            timer_runner.timers.add(timer)
            await action_controller.on_action_called_event.wait()

            replacement_timer = create_example_timer(start_time, timedelta(seconds=5))
            timer_runner.timers.add(replacement_timer)
            timer_runner.timers.remove(timer.id)
            await _short_sleep()
            action_controller.off_action_mock.assert_not_called()

        await self._test_run(
            actions_during_run=actions_during_run,
            start_time=start_time,
        )

    @pytest.mark.asyncio
    async def test_run_timer_on_replaced_with_off(self):
        start_time = DayTime(0, 0, 0)

        async def actions_during_run(
            timer_runner: TimerRunner, time_setter: TimeSetter, action_controller: MockActionController
        ):
            timer = create_example_timer(start_time, timedelta(seconds=10))
            timer_runner.timers.add(timer)
            await action_controller.on_action_called_event.wait()

            replacement_timer = create_example_timer(timer.end_time + timedelta(seconds=1), timedelta(seconds=1))
            timer_runner.timers.add(replacement_timer)
            timer_runner.timers.remove(timer.id)
            await action_controller.off_action_called_event.wait()

        await self._test_run(
            actions_during_run=actions_during_run,
            action_assertions=lambda action_controller: action_controller.assert_actions_called(),
            start_time=start_time,
        )

    @pytest.mark.asyncio
    async def test_run_misses_off_time(self):
        start_time = DayTime(0, 0, 0)

        async def actions_during_run(
            timer_runner: TimerRunner, time_setter: TimeSetter, action_controller: MockActionController
        ):
            await action_controller.on_action_called_event.wait()
            time_setter.value = start_time + timedelta(hours=1)
            await action_controller.off_action_called_event.wait()

        await self._test_run(
            ((start_time, timedelta(seconds=1)),),
            actions_during_run=actions_during_run,
            start_time=start_time,
        )

    @pytest.mark.asyncio
    async def test_run_stop_when_on(self):
        start_time = DayTime(0, 0, 0)

        async def actions_during_run(
            timer_runner: TimerRunner, time_setter: TimeSetter, action_controller: MockActionController
        ):
            await action_controller.on_action_called_event.wait()
            timer_runner.run_stop_event.set()
            await action_controller.off_action_called_event.wait()

        await self._test_run(
            ((start_time, timedelta(seconds=1)),),
            actions_during_run=actions_during_run,
            start_time=start_time,
        )

    async def _test_run(
        self,
        start_duration_pairs: StartDurationPairsIterable = (),
        actions_during_run: Callable[
            [TimerRunner, TimeSetter, MockActionController], Awaitable[None]
        ] = lambda *_: None,
        action_assertions: Callable[[MockActionController], None] = lambda *_: None,
        start_time: DayTime = DayTime(0, 0, 0),
    ):
        timer_runner, time_setter, action_controller = _create_timer_runner(start_duration_pairs, start_time)

        timer_runner.minimum_time_accuracy = timedelta(microseconds=1)
        task = asyncio.create_task(timer_runner.run())

        await actions_during_run(timer_runner, time_setter, action_controller)

        timer_runner.run_stop_event.set()
        # Trigger re-evaluation of stop event
        timer_runner.timers_change_event.set()
        await task

        action_assertions(action_controller)


def _create_timer_runner(
    start_duration_pairs: StartDurationPairsIterable = (), current_time: DayTime = DayTime(0, 0, 0)
) -> tuple[TimerRunner, MutableItem[DayTime], MockActionController]:
    timers = (create_example_timer(start_time, duration) for start_time, duration in start_duration_pairs)
    time_setter = TimeSetter(current_time)
    action_controller = MockActionController()

    def current_time_getter() -> DayTime:
        return time_setter.value

    return (
        TimerRunner(
            ListenableTimersCollection(InMemoryIdentifiableTimersCollection(timers)),
            action_controller,
            current_time_getter=current_time_getter,
        ),
        time_setter,
        action_controller,
    )


def _create_interval(start_time: str, duration: timedelta) -> TimeInterval:
    start_time = deserialise_daytime(start_time)
    return TimeInterval(start_time, start_time + duration)


async def _short_sleep():
    await asyncio.sleep(0.05)
