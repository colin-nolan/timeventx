from collections import defaultdict
from typing import Callable, Iterator

from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.timers import IdentifiableTimer, Timer, TimerId

try:
    from typing import TypeAlias

    AddListener: TypeAlias = Callable[[IdentifiableTimer], None]
    RemoveListener: TypeAlias = Callable[[TimerId], None]
except ImportError:
    AddListener = Callable[[IdentifiableTimer], None]
    RemoveListener = Callable[[TimerId], None]


# Not using enum because it is not available in MicroPython (or installable using `mip`)
class Event:
    TIMER_ADDED = "added"
    TIMER_REMOVED = "removed"


class ListenableTimersCollection(IdentifiableTimersCollection):
    """
    Timers collection that can be listened to for changes.

    Not (p)thread safe.
    """

    def __init__(self, timers_collection: IdentifiableTimersCollection):
        """
        Constructor.

        All updates to the timer collection must be made in the same process thread as the listeners.
        :param timers_collection: timers collection to initialise with
        """
        self._timers_collection = timers_collection
        self.listeners: dict[Event, list[AddListener | RemoveListener]] = defaultdict(list)

    def __len__(self) -> int:
        return len(self._timers_collection)

    def __iter__(self) -> Iterator[IdentifiableTimer]:
        return iter(self._timers_collection)

    def get(self, timer_id: TimerId) -> IdentifiableTimer:
        return self._timers_collection.get(timer_id)

    def add(self, timer: Timer | IdentifiableTimer) -> IdentifiableTimer:
        added_timer = self._timers_collection.add(timer)

        for listener in self.listeners[Event.TIMER_ADDED]:
            listener(added_timer)

        return added_timer

    def remove(self, timer_id: TimerId) -> bool:
        removed = self._timers_collection.remove(timer_id)
        if removed:
            for listener in self.listeners[Event.TIMER_REMOVED]:
                listener(timer_id)
        return removed

    def add_listener(self, event: Event, listener: AddListener | RemoveListener):
        self.listeners[event].append(listener)
