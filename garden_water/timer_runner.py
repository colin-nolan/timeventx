from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.collections.listenable import ListenableTimersCollection
from garden_water.timers.timers import DayTime, TimeInterval


class TimerRunner:
    def __init__(self, timers: IdentifiableTimersCollection):
        self.timers = ListenableTimersCollection(timers)
        self.calculate_on_off_times()

    # TODO: create on-off dataclass to make this tidier
    def calculate_on_off_times(self) -> tuple[TimeInterval, ...]:
        if len(self.timers) == 0:
            return ()

        timers_by_start_time = sorted(self.timers, key=lambda timer: timer.start_time)
        intervals = [timers_by_start_time[0].interval]
        timers_by_start_time.pop(0)

        for timer in timers_by_start_time:
            last_interval = intervals[-1]
            last_on_off_wrapped_around_midnight = last_interval.end_time < last_interval.start_time
            interval = timer.interval
            on_off_wrapped_around_midnight = interval.end_time < interval.start_time

            start_time = interval.start_time
            end_time = interval.end_time

            if (
                interval.start_time < last_interval.end_time
                and not last_on_off_wrapped_around_midnight
                or interval.start_time > last_interval.end_time
                and last_on_off_wrapped_around_midnight
            ):
                # Timer overlaps with last timer so merging the two
                start_time = min(interval.start_time, last_interval.start_time)
                end_time = (
                    max(interval.end_time, last_interval.end_time)
                    if last_on_off_wrapped_around_midnight == on_off_wrapped_around_midnight
                    else min(interval.end_time, last_interval.end_time)
                )
                intervals.pop()

            if on_off_wrapped_around_midnight:
                # Timer wraps around midnight
                for loop_interval in tuple(intervals):
                    # loop_on_time, loop_off_time = loop_interval
                    if interval.end_time < loop_interval.start_time:
                        # On/Off time at the start happens after the new wrap around on/off time
                        break
                    else:
                        # New wrapped around on/off time will replace this one at the start
                        end_time = max(interval.end_time, loop_interval.end_time)
                        intervals.remove(loop_interval)

            if interval.start_time == interval.end_time:
                raise ValueError(
                    f"timers overlap such that they never turn off - noticed when adding timer "
                    f"({timer.start_time}, {timer.end_time}) to: {intervals}"
                )

            # Timer does not overlap with last timer so adding it to the list
            intervals.append(TimeInterval(start_time, end_time))

        return tuple(intervals)

    def run(self):
        pass
