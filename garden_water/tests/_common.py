from datetime import timedelta

from garden_water.timers.models import Timer, IdentifiableTimer, TimerId
from garden_water.timers.serialisation import deserialise_start_time

EXAMPLE_TIMER_1 = Timer("test-1", deserialise_start_time("00:01:02"), timedelta(minutes=10), True)
EXAMPLE_TIMER_2 = Timer("test-2", deserialise_start_time("09:08:07"), timedelta(minutes=1000), True)
EXAMPLE_IDENTIFIABLE_TIMER_1 = IdentifiableTimer(
    "test-identifiable-1",
    deserialise_start_time("09:09:09"),
    timedelta(minutes=100),
    False,
    id=TimerId(666),
)
EXAMPLE_IDENTIFIABLE_TIMER_2 = IdentifiableTimer(
    "test-identifiable-2",
    deserialise_start_time("06:09:07"),
    timedelta(minutes=1000),
    False,
    id=TimerId(6660),
)

EXAMPLE_TIMERS = (EXAMPLE_TIMER_1, EXAMPLE_TIMER_2, EXAMPLE_IDENTIFIABLE_TIMER_1, EXAMPLE_IDENTIFIABLE_TIMER_2)
