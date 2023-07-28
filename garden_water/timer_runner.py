from datetime import timedelta

from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.collections.listenable import ListenableTimersCollection
from garden_water.timers.timers import TimeInterval


class TimerRunner:
    def __init__(self, timers: IdentifiableTimersCollection):
        self.timers = ListenableTimersCollection(timers)
        self.calculate_on_off_times()

    def calculate_on_off_times(self) -> tuple[TimeInterval, ...]:
        if len(self.timers) == 0:
            return ()

        timers_by_start_time = sorted(self.timers, key=lambda timer: timer.start_time)
        intervals = [timers_by_start_time[0].interval]
        timers_by_start_time.pop(0)

        for timer in timers_by_start_time:
            last_interval = intervals[-1]
            interval = timer.interval

            start_time = interval.start_time
            end_time = interval.end_time

            if (
                interval.start_time < last_interval.end_time
                and not last_interval.spans_midnight()
                or interval.start_time > last_interval.end_time
                and last_interval.spans_midnight()
            ):
                # XXX: Timers overlap. Taking "brute force" approach and generating all possible intervals from the
                # overlapping intervals and then picking the longest one. There is undoubtedly a more efficient way to
                # calculate this but the midnight wrap around makes it very confusing (consider converting to a linear
                # representation?).
                superset_interval = TimeInterval(interval.start_time, interval.end_time)
                earlier_interval = TimeInterval(interval.start_time, last_interval.end_time)
                later_interval = TimeInterval(last_interval.start_time, interval.end_time)
                subset_interval = TimeInterval(last_interval.start_time, last_interval.end_time)
                longest_interval = max(
                    (superset_interval, earlier_interval, later_interval, subset_interval), key=lambda x: x.duration
                )

                # The above method does not work if the combined intervals result in no gap (i.e. there is no turn off).
                # The concept of no off time is not supported. Detecting this case by checking if any of the intervals
                # intersect with the gap, indicating the longest interval could have been longer.
                gap_interval = TimeInterval(longest_interval.end_time, longest_interval.start_time)
                if interval.intersects(gap_interval) or last_interval.intersects(gap_interval):
                    raise ValueError("Timers overlap such that they never turn off")

                start_time = longest_interval.start_time
                end_time = longest_interval.end_time
                intervals.pop()

            if interval.spans_midnight():
                # Timer wraps around midnight so need to check if it overlaps with any of the timers at the start
                for loop_interval in tuple(intervals):
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

            new_interval = TimeInterval(start_time, end_time)
            if new_interval.duration >= timedelta(days=1):
                raise ValueError("timers overlap such that they never turn off")
            # Timer does not overlap with last timer so adding it to the list
            intervals.append(new_interval)

        return tuple(intervals)

    def run(self):
        pass
