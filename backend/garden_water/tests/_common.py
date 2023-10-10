from datetime import timedelta
from threading import Lock
from uuid import uuid4

from garden_water._logging import reset_logging
from garden_water.timers.serialisation import deserialise_daytime
from garden_water.timers.timers import IdentifiableTimer, Timer, TimerId

EXAMPLE_TIMER_1 = Timer("test-1", deserialise_daytime("00:01:02"), timedelta(minutes=10))
EXAMPLE_IDENTIFIABLE_TIMER_1 = IdentifiableTimer(
    TimerId(666),
    "test-identifiable-1",
    deserialise_daytime("09:09:09"),
    timedelta(minutes=100),
)
EXAMPLE_TIMER_2 = Timer("test-2", deserialise_daytime("09:08:07"), timedelta(minutes=1000))
EXAMPLE_IDENTIFIABLE_TIMER_2 = IdentifiableTimer(
    TimerId(6660),
    "test-identifiable-2",
    deserialise_daytime("06:09:07"),
    timedelta(minutes=1000),
)

EXAMPLE_TIMERS = (EXAMPLE_TIMER_1, EXAMPLE_TIMER_2, EXAMPLE_IDENTIFIABLE_TIMER_1, EXAMPLE_IDENTIFIABLE_TIMER_2)

_TEST_LOCK = Lock()


def create_example_timer(start_time: str, duration: timedelta) -> IdentifiableTimer:
    return IdentifiableTimer(TimerId(uuid4().int), "test", deserialise_daytime(start_time), duration)


# To be used for tests that interact with logging globals, and hence cannot be ran in parallel
def changes_logging_test(wrappable: callable):
    def wrapper(*args, **kwargs):
        with _TEST_LOCK:
            reset_logging()
            return wrappable(*args, **kwargs)

    return wrapper
