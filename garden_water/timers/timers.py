from dataclasses import dataclass
from datetime import timedelta
from functools import cached_property, total_ordering
from typing import NewType, cast

START_TIME_FORMAT = "%H:%M:%S"

TimerId = NewType("TimerId", int)


@total_ordering
@dataclass(frozen=True)
class DayTime:
    hour: int
    minute: int
    second: int

    def __post_init__(self):
        if self.second < 0 or self.second >= 60:
            raise ValueError("second must be between 0 and 59")
        if self.minute < 0 or self.minute >= 60:
            raise ValueError("minute must be between 0 and 59")
        if self.hour < 0 or self.hour >= 24:
            raise ValueError("hour must be between 0 and 23")

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, DayTime)
            and self.hour == other.hour
            and self.minute == other.minute
            and self.second == other.second
        )

    def __lt__(self, other: object) -> bool:
        if not issubclass(type(other), DayTime):
            raise TypeError(f"'<' not supported between instances of 'DayTime' and '{type(other).__name__}'")
        other = cast(DayTime, other)
        return self.as_seconds() < other.as_seconds()

    def __add__(self, other: object) -> "DayTime":
        if not issubclass(type(other), timedelta):
            raise TypeError(f"unsupported operand type(s) for +: 'DayTime' and '{type(other).__name__}'")

        time_to_add: timedelta = cast(timedelta, other)
        hours_to_add = time_to_add.seconds // 3600
        minutes_to_add = time_to_add.seconds // 60 - hours_to_add * 60
        seconds_to_add = time_to_add.seconds - hours_to_add * 3600 - minutes_to_add * 60

        new_second_overflowed = self.second + seconds_to_add
        new_minute_overflowed = self.minute + minutes_to_add + new_second_overflowed // 60
        new_hour_overflowed = self.hour + hours_to_add + new_minute_overflowed // 60

        return DayTime(
            hour=new_hour_overflowed % 24, minute=new_minute_overflowed % 60, second=new_second_overflowed % 60
        )

    def __repr__(self):
        return f"{self.hour:02}:{self.minute:02}:{self.second:02}"

    def as_seconds(self) -> int:
        return self.second + self.minute * 60 + self.hour * 3600


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


@dataclass(frozen=True)
class Timer:
    name: str
    start_time: DayTime
    duration: timedelta

    # Safe to cache as the timer is frozen
    @cached_property
    def end_time(self) -> DayTime:
        return self.start_time + self.duration

    @cached_property
    def interval(self) -> TimeInterval:
        return TimeInterval(self.start_time, self.end_time)

    def __post_init__(self):
        if self.duration > timedelta(days=1):
            raise ValueError("timer duration cannot be longer than 24 hours")
        elif self.duration == timedelta(seconds=0):
            raise ValueError("timer duration cannot be zero")


@dataclass(frozen=True)
class IdentifiableTimer(Timer):
    id: TimerId

    @staticmethod
    def from_timer(timer: Timer, identifier: TimerId) -> "IdentifiableTimer":
        return IdentifiableTimer(
            id=identifier,
            name=timer.name,
            start_time=timer.start_time,
            duration=timer.duration,
        )

    def to_timer(self):
        return Timer(
            name=self.name,
            start_time=self.start_time,
            duration=self.duration,
        )
