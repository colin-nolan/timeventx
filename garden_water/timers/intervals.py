from dataclasses import dataclass
from datetime import timedelta
from functools import cached_property
from typing import Collection

from garden_water.timers.timers import DayTime


@dataclass(frozen=True)
class TimeInterval:
    start_time: DayTime
    end_time: DayTime

    # Safe to cache as the time interval is frozen
    @cached_property
    def duration(self) -> timedelta:
        return (
            timedelta(seconds=self.end_time.as_seconds() - self.start_time.as_seconds())
            if not self.spans_midnight()
            else timedelta(seconds=60 * 60 * 24 - self.start_time.as_seconds() + self.end_time.as_seconds())
        )

    def __post_init__(self):
        if self.start_time == self.end_time:
            raise ValueError("Interval must be non-zero")

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, TimeInterval) and self.start_time == other.start_time and self.end_time == other.end_time
        )

    def __repr__(self):
        return repr([self.start_time, self.end_time])

    def spans_midnight(self) -> bool:
        return self.start_time > self.end_time

    def intersects(self, other: "TimeInterval") -> bool:
        earlier_interval, later_interval = sorted((self, other), key=lambda interval: interval.start_time)

        if earlier_interval.spans_midnight():
            if later_interval.spans_midnight():
                # Both intervals cross midnight, so they at least overlap at midnight
                return True
            earlier_interval, later_interval = later_interval, earlier_interval

        if later_interval.spans_midnight():
            return (
                later_interval.start_time < earlier_interval.end_time
                or later_interval.end_time > earlier_interval.start_time
            )
        else:
            return (
                later_interval.start_time < earlier_interval.end_time
                and later_interval.end_time > earlier_interval.start_time
            )


def merge_and_sort_intervals(intervals: Collection[TimeInterval]) -> tuple[TimeInterval, ...]:
    if len(intervals) == 0:
        return ()

    intervals_by_start_time = sorted(intervals, key=lambda interval: interval.start_time)
    intervals = [intervals_by_start_time[0]]
    intervals_by_start_time.pop(0)

    for interval in intervals_by_start_time:
        last_interval = intervals[-1]

        start_time = interval.start_time
        end_time = interval.end_time

        if (
            interval.start_time < last_interval.end_time
            and not last_interval.spans_midnight()
            or interval.start_time > last_interval.end_time
            and last_interval.spans_midnight()
        ):
            # XXX: Intervals overlap. Taking "brute force" approach and generating all possible intervals from the
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
                raise ValueError("Intervals overlap such that there is no end time")

            start_time = longest_interval.start_time
            end_time = longest_interval.end_time
            intervals.pop()

        if interval.spans_midnight():
            # Interval wraps around midnight so need to check if it overlaps with any of the intervals at the start
            for loop_interval in tuple(intervals):
                if interval.end_time < loop_interval.start_time:
                    # On/Off time at the start happens after the new wrap around on/off time
                    break
                else:
                    # New wrapped around on/off time will replace this one at the start
                    end_time = max(interval.end_time, loop_interval.end_time)
                    intervals.remove(loop_interval)

        new_interval = TimeInterval(start_time, end_time)
        intervals.append(new_interval)

    return tuple(intervals)
