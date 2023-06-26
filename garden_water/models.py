from abc import ABC, abstractmethod
from collections.abc import Container
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import NewType, cast

TimerId = NewType("TimerId", int)


@dataclass(frozen=True)
class Timer:
    id: TimerId
    name: str
    start_time: datetime
    duration: timedelta
    enabled: bool


class TimersContainer(ABC, Container[Timer]):
    @abstractmethod
    def get_all(self) -> tuple[Timer]:
        """
        Gets all timers.
        :return: timers, unordered
        """

    @abstractmethod
    def get(self, timer_id: TimerId) -> Timer:
        """
        Get timer by ID.
        :param timer_id: id of timer to get
        :return: timer with the given ID
        :raises KeyError: if timer does not exist
        """

    @abstractmethod
    def add(self, timer: Timer):
        """
        Adds the given timer to the collection.
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
        if not issubclass(type(item), Timer):
            return False
        item = cast(Timer, item)
        try:
            return self.get(item.id) == item
        except KeyError:
            return False
