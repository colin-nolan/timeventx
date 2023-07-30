from datetime import timedelta
from typing import Any, cast

START_TIME_FORMAT = "%H:%M:%S"

try:
    from typing import NewType

    TimerId = NewType("TimerId", int)
except ImportError:
    TimerId = int


# Not using `total_ordering` or `dataclass` because they are not available in MicroPython (or installable using `mip`)
# @total_ordering
# @dataclass(frozen=True)
class DayTime:
    @staticmethod
    def now() -> "DayTime":
        # FIXME: implement
        return DayTime(0, 0, 0)

    def __init__(self, hour: int, minute: int, second: int):
        if second < 0 or second >= 60:
            raise ValueError("second must be between 0 and 59")
        if minute < 0 or minute >= 60:
            raise ValueError("minute must be between 0 and 59")
        if hour < 0 or hour >= 24:
            raise ValueError("hour must be between 0 and 23")

        self.hour = hour
        self.minute = minute
        self.second = second

    def __hash__(self):
        return hash((self.hour, self.minute, self.second))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, DayTime)
            and self.hour == other.hour
            and self.minute == other.minute
            and self.second == other.second
        )

    def __ne__(self, other: Any):
        return not self.__eq__(other)

    def __lt__(self, other: Any) -> bool:
        if not issubclass(type(other), DayTime):
            raise TypeError(f"'<' not supported between instances of 'DayTime' and '{type(other).__name__}'")
        other = cast(DayTime, other)
        return self.as_seconds() < other.as_seconds()

    def __gt__(self, other: Any):
        return not self.__lt__(other) and not self.__eq__(other)

    def __le__(self, other: Any):
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other: Any):
        return self.__gt__(other) or self.__eq__(other)

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


# Not using dataclass because it is not available in MicroPython
# @dataclass(frozen=True)
class Timer:
    def __init__(self, name: str, start_time: DayTime, duration: timedelta):
        if duration > timedelta(days=1):
            raise ValueError("timer duration cannot be longer than 24 hours")
        elif duration == timedelta(seconds=0):
            raise ValueError("timer duration cannot be zero")

        self.name = name
        self.start_time = start_time
        self.duration = duration

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Timer)
            and self.name == other.name
            and self.start_time == other.start_time
            and self.duration == other.duration
        )

    def __hash__(self):
        return hash((self.name, self.start_time, self.duration))

    @property
    def end_time(self) -> DayTime:
        return self.start_time + self.duration

    @property
    # Avoiding circular dependency
    # def interval(self) -> "TimeInterval:
    def interval(self):
        from garden_water.timers.intervals import TimeInterval

        return TimeInterval(self.start_time, self.end_time)


# Not using dataclass because it is not available in MicroPython
# @dataclass(frozen=True)
class IdentifiableTimer(Timer):
    def __init__(self, timer_id: TimerId, name: str, start_time: DayTime, duration: timedelta):
        super().__init__(name=name, start_time=start_time, duration=duration)
        self.id = timer_id

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, IdentifiableTimer)
            and self.id == other.id
            and self.name == other.name
            and self.start_time == other.start_time
            and self.duration == other.duration
        )

    def __hash__(self):
        return hash((super().__hash__(), self.id))

    @staticmethod
    def from_timer(timer: Timer, identifier: TimerId) -> "IdentifiableTimer":
        return IdentifiableTimer(
            timer_id=identifier,
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
