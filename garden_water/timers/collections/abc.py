from abc import abstractmethod
from typing import Collection, cast

from garden_water.timers.timers import IdentifiableTimer, Timer, TimerId


class IdentifiableTimersCollection(Collection[IdentifiableTimer]):
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

    def __contains__(self, item: object) -> bool:
        if not issubclass(type(item), IdentifiableTimer):
            return False
        item = cast(IdentifiableTimer, item)
        try:
            self.get(item.id)
            return True
        except KeyError:
            return False
