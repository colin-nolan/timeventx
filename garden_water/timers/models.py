from dataclasses import dataclass
from datetime import timedelta
from time import struct_time
from typing import NewType

START_TIME_FORMAT = "%H:%M:%S"

TimerId = NewType("TimerId", int)


@dataclass(frozen=True)
class Timer:
    name: str
    start_time: struct_time
    duration: timedelta
    enabled: bool


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
            enabled=timer.enabled,
        )

    def to_timer(self):
        return Timer(
            name=self.name,
            start_time=self.start_time,
            duration=self.duration,
            enabled=self.enabled,
        )





