from datetime import timedelta
from typing import Callable

from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.collections.listenable import Event, ListenableTimersCollection
from garden_water.timers.intervals import TimeInterval, merge_and_sort_intervals
from garden_water.timers.timers import DayTime


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
        timers: IdentifiableTimersCollection,
        on_action: Callable,
        off_action: Callable,
        current_time_getter: Callable[[], DayTime] = DayTime.now,
    ):
        self.timers = ListenableTimersCollection(timers)
        self.on_action = on_action
        self.off_action = off_action
        self.current_time_getter = current_time_getter
        self._on_off_intervals = self._calculate_on_off_intervals()

        def on_timers_change(*args) -> None:
            self._calculate_on_off_intervals()

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

        now = self.current_time_getter()
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

    def run(self):
        pass

    def _calculate_on_off_intervals(self) -> tuple[TimeInterval, ...]:
        return merge_and_sort_intervals(tuple(map(lambda timer: timer.interval, self.timers)))
