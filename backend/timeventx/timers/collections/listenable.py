from collections import defaultdict
from typing import Callable, Iterator, TypeAlias

from timeventx.timers.collections.abc import IdentifiableTimersCollection
from timeventx.timers.timers import IdentifiableTimer, Timer, TimerId

AddListener: TypeAlias = Callable[[IdentifiableTimer], None]
RemoveListener: TypeAlias = Callable[[TimerId], None]
EventEnum: TypeAlias = str


# Not using enum because it is not available in MicroPython (or installable using `mip`)
class Event:
    TIMER_ADDED: EventEnum = "added"
    TIMER_REMOVED: EventEnum = "removed"


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
        self.listeners: dict[str, list[AddListener | RemoveListener]] = defaultdict(list)

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

    def add_listener(self, event: EventEnum, listener: AddListener | RemoveListener):
        self.listeners[event].append(listener)
