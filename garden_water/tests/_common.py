from datetime import timedelta
from uuid import uuid4

from garden_water.timers.serialisation import deserialise_daytime
from garden_water.timers.timers import IdentifiableTimer, Timer, TimerId

EXAMPLE_TIMER_1 = Timer("test-1", deserialise_daytime("00:01:02"), timedelta(minutes=10))
EXAMPLE_TIMER_2 = Timer("test-2", deserialise_daytime("09:08:07"), timedelta(minutes=1000))
EXAMPLE_IDENTIFIABLE_TIMER_1 = IdentifiableTimer(
    "test-identifiable-1",
    deserialise_daytime("09:09:09"),
    timedelta(minutes=100),
    id=TimerId(666),
)
EXAMPLE_IDENTIFIABLE_TIMER_2 = IdentifiableTimer(
    "test-identifiable-2",
    deserialise_daytime("06:09:07"),
    timedelta(minutes=1000),
    id=TimerId(6660),
)

EXAMPLE_TIMERS = (EXAMPLE_TIMER_1, EXAMPLE_TIMER_2, EXAMPLE_IDENTIFIABLE_TIMER_1, EXAMPLE_IDENTIFIABLE_TIMER_2)


def create_example_timer(start_time: str, duration: timedelta) -> IdentifiableTimer:
    return IdentifiableTimer("test", deserialise_daytime(start_time), duration, id=TimerId(uuid4().int))
