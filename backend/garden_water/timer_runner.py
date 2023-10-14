from datetime import timedelta
from time import sleep
from typing import Callable, Optional

from garden_water._logging import flush_file_logs, get_logger
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
        on_action: Callable,
        off_action: Callable,
        current_time_getter: Callable[[], DayTime] = DayTime.now,
    ):
        assert issubclass(type(timers), ListenableTimersCollection)

        self.timers = timers
        self.on_action = on_action
        self.off_action = off_action
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
                if self._turned_on:
                    self._do_off_action()

                logger.debug(f"Waiting for timers change event, currently: {self.timers_change_event.is_set()}")
                # Wait for timers to change
                await self.timers_change_event.wait()
                # FIXME: need to lock before doing this as it's possible length has changed in the meantime?
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
                if self._turned_on:
                    self._do_off_action()

                logger.info(f"Waiting for next interval start time: {next_interval.start_time}")

                def on_time_missed_condition(current_time: DayTime) -> bool:
                    if self.run_stop_event.is_set():
                        return
                    # `True` when the start time has been missed and we've "gone around the clock"
                    return (
                        False
                        if current_time == first_encounter_time
                        else TimeInterval(current_time, first_encounter_time).duration
                        < TimeInterval(current_time, next_interval.start_time).duration
                    )

                timers_changed = await self._wait_for_time(
                    next_interval.start_time, on_time_missed_condition, "on action"
                )
                if timers_changed:
                    continue

            def off_time_missed_condition(current_time: DayTime) -> bool:
                if self.run_stop_event.is_set():
                    return
                # `True` when the end time has been missed and we've "gone around the clock"
                return (
                    False
                    if current_time == first_encounter_time
                    else TimeInterval(current_time, first_encounter_time).duration
                    < TimeInterval(current_time, next_interval.end_time).duration
                )

            if off_time_missed_condition(self._current_time_getter()):
                logger.warning(f"Timer window has been missed, skipping: {next_interval}")
                continue

            if not self._turned_on:
                self._do_on_action()

            logger.debug(f"Waiting for interval end time: {next_interval.end_time}")
            timers_changed = await self._wait_for_time(next_interval.end_time, off_time_missed_condition, "off action")
            if timers_changed:
                continue

            self._do_off_action()

        self._running = False

    async def _wait_for_time(
        self, waiting_for: DayTime, early_exit_condition: callable, wait_description: str = "wait time"
    ) -> bool:
        """
        Waits until the specified time is reached, returning early if the timers collection changes.
        :param waiting_for: the time to wait for
        :param early_exit_condition: exit early if condition ever returns `True`. Passed current time as first and only arg
        :param wait_description: description of the wait for logging purposes
        :returns: `True` if the timers have changed and subsequently exited early
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
                return False

            if self.timers_change_event.is_set():
                logger.debug(f"Timers changed whilst waiting for {wait_description}")
                return True

            if early_exit_condition(current_time):
                return False

            await asyncio.sleep(self.minimum_time_accuracy.total_seconds())

    def _calculate_on_off_intervals(self) -> tuple[TimeInterval, ...]:
        return merge_and_sort_intervals(tuple(map(lambda timer: timer.interval, self.timers)))

    def _do_on_action(self):
        logger.info("Performing on action!")
        self.on_action()
        self._turned_on = True

    def _do_off_action(self):
        logger.info("Performing off action!")
        self.off_action()
        self._turned_on = False
