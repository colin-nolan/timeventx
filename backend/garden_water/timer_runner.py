from datetime import timedelta
from typing import Callable

from garden_water._logging import get_logger
from garden_water.actions.actions import ActionController
from garden_water.timers.collections.listenable import Event, ListenableTimersCollection
from garden_water.timers.intervals import TimeInterval, merge_and_sort_intervals
from garden_water.timers.timers import DayTime

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

logger = get_logger(__name__)

_NO_TIMEOUT = -1


class NoTimersError(RuntimeError):
    """
    Raised when the timers runner has no timers.
    """


class TimerRunner:
    @property
    def on_off_intervals(self) -> tuple[TimeInterval, ...]:
        return self._on_off_intervals

    def __init__(
        self,
        timers: ListenableTimersCollection,
        action_controller: ActionController,
        current_time_getter: Callable[[], DayTime] = DayTime.now,
    ):
        assert issubclass(type(timers), ListenableTimersCollection)

        self.timers = timers
        self.action_controller = action_controller
        self._turned_on = False
        self._current_time_getter = current_time_getter
        self._on_off_intervals = self._calculate_on_off_intervals()
        self.timers_change_event = asyncio.Event()

        self._running = False
        self._running_lock = asyncio.Lock()
        self.run_stop_event = asyncio.Event()
        self.minimum_time_accuracy: timedelta = timedelta(seconds=1)

        def on_timers_change(*args) -> None:
            self._on_off_intervals = self._calculate_on_off_intervals()
            self.timers_change_event.set()

        self.timers.add_listener(Event.TIMER_ADDED, on_timers_change)
        self.timers.add_listener(Event.TIMER_REMOVED, on_timers_change)

    def is_on(self) -> bool:
        try:
            return self.next_interval()[1]
        except NoTimersError:
            return False

    def next_interval(self) -> tuple[TimeInterval, bool]:
        if len(self._on_off_intervals) == 0:
            raise NoTimersError("No timers")

        now = self._current_time_getter()
        now_interval = TimeInterval(now, now + timedelta(seconds=1))

        for i, interval in enumerate(self._on_off_intervals):
            if interval.intersects(now_interval):
                return interval, True
            elif interval.start_time >= now:
                if i == 0 and self._on_off_intervals[-1].intersects(now_interval):
                    # May intersect with the interval at the end of the list if it spans midnight
                    return self._on_off_intervals[-1], True
                else:
                    return interval, False
        return self._on_off_intervals[0], False

    async def run(self):
        async with self._running_lock:
            if self._running:
                raise RuntimeError("Already running in another thread")
            self._running = True
        if self.run_stop_event.is_set():
            raise RuntimeError("Run stop event must be cleared before running")

        while not self.run_stop_event.is_set():
            while len(self.timers) == 0:
                self._set_off()

                logger.debug(f"Waiting for timers change event, currently: {self.timers_change_event.is_set()}")
                await self.timers_change_event.wait()
                self.timers_change_event.clear()

                if self.run_stop_event.is_set():
                    return

            self.timers_change_event.clear()

            try:
                next_interval, on_now = self.next_interval()
            except NoTimersError:
                # Since getting the lock it is possible that the timers have been updated!
                continue

            first_encounter_time = self._current_time_getter()
            logger.debug(f"Got next interval at {first_encounter_time}: {next_interval}")

            if not on_now:
                self._set_off()

                logger.info(f"Waiting for next interval start time: {next_interval.start_time}")

                def on_time_missed_condition(current_time: DayTime) -> bool:
                    # `True` when the start time has been missed and we've "gone around the clock"
                    return (
                        False
                        if current_time == first_encounter_time
                        else TimeInterval(current_time, first_encounter_time).duration
                        < TimeInterval(current_time, next_interval.start_time).duration
                    )

                wait_completed = await self._wait_for_time(
                    next_interval.start_time, on_time_missed_condition, "on action"
                )
                if not wait_completed:
                    continue

            def off_time_missed_condition(current_time: DayTime) -> bool:
                # `True` when the end time has been missed and we've "gone around the clock"
                return (
                    False
                    if current_time == first_encounter_time
                    else TimeInterval(current_time, first_encounter_time).duration
                    < TimeInterval(current_time, next_interval.end_time).duration
                )

            self._set_on()

            logger.debug(f"Waiting for interval end time: {next_interval.end_time}")
            wait_completed = await self._wait_for_time(next_interval.end_time, off_time_missed_condition, "off action")
            if not wait_completed:
                continue

            self._set_off()

        self._running = False
        # Default to off state
        self._set_off()

    async def _wait_for_time(
        self, waiting_for: DayTime, exit_condition: callable, wait_description: str = "wait time"
    ) -> bool:
        """
        Waits until the specified time is reached, returning early if the wait was interrupted by a change in the timers
        or the run stop event being set.
        :param waiting_for: the time to wait for
        :param exit_condition: exit as wait completed if condition ever returns `True`. Passed current time as first
                               and only argument
        :param wait_description: description of the wait for logging purposes
        :returns: `True` if the wait was completed
        """
        # Unfortunately, timeouts aren't implemented on asyncio events:
        # https://docs.micropython.org/en/v1.14/library/uasyncio.html#class-lock
        # Therefore, the implementation polls the event every second until the time is reached or the event is triggered
        while True:
            current_time = self._current_time_getter()
            difference_in_seconds = (
                0 if current_time == waiting_for else TimeInterval(current_time, waiting_for).duration.seconds
            )
            logger.debug(f"Seconds to {wait_description}: {difference_in_seconds} ({current_time} => {waiting_for})")

            if difference_in_seconds <= 0:
                return True

            if self.timers_change_event.is_set():
                logger.debug(f"Timers changed whilst waiting for {wait_description}")
                return False

            if exit_condition(current_time):
                return True

            if self.run_stop_event.is_set():
                return False

            await asyncio.sleep(self.minimum_time_accuracy.total_seconds())

    def _calculate_on_off_intervals(self) -> tuple[TimeInterval, ...]:
        return merge_and_sort_intervals(tuple(map(lambda timer: timer.interval, self.timers)))

    def _set_on(self):
        if not self._turned_on:
            logger.info("Performing on action!")
            asyncio.create_task(self.action_controller.on_action())
            self._turned_on = True

    def _set_off(self):
        if self._turned_on:
            logger.info("Performing off action!")
            asyncio.create_task(self.action_controller.off_action())
            self._turned_on = False
