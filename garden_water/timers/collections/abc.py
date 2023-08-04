from abc import abstractmethod
from typing import Collection, cast, Iterable

from garden_water.timers.timers import IdentifiableTimer, Timer, TimerId

try:
    from typing import TypeAlias

    IdentifiableTimerCollection: TypeAlias = Collection[IdentifiableTimer]
except ImportError:
    IdentifiableTimerCollection = Collection


# TODO: `Sized` and `Iterable`
class IdentifiableTimersCollection(IdentifiableTimerCollection):
    @abstractmethod
    def get(self, timer_id: TimerId) -> IdentifiableTimer:
        """
        Get timer by ID.
        :param timer_id: id of timer to get
        :return: timer with the given ID
        :raises KeyError: if timer does not exist
        """

    # Could not get the `singledispatch` annotation to work
    @abstractmethod
    def add(self, timer: Timer | IdentifiableTimer) -> IdentifiableTimer:
        """
        Adds the given timer to the collection.

        A model of the timer added is returned
        :param timer: timer to add
        :raises ValueError: if timer with the same ID already exists
        """

    @abstractmethod
    def remove(self, timer_id: TimerId) -> bool:
        """
        Removes the timer with the given ID.
        :param timer_id: ID of the timer to remove
        :return: `True` if a timer with the given ID was removed
        """

    @abstractmethod
    def __iter__(self) -> Iterable[IdentifiableTimer]:
        """
        Gets an iterator over the timers in the collection.
        :return: iterator over timers in the collection
        """

    @abstractmethod
    def __len__(self) -> int:
        """
        Gets the number of timers in the collection.
        :return: number of timers in the collection
        """

    def __contains__(self, item: object) -> bool:
        if not issubclass(type(item), IdentifiableTimer):
            return False
        item = cast(IdentifiableTimer, item)
        try:
            self.get(item.id)
            return True
        except KeyError:
            return False
