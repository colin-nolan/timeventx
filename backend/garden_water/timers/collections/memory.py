from typing import Iterable, Iterator

from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.timers import IdentifiableTimer, Timer, TimerId


class InMemoryIdentifiableTimersCollection(IdentifiableTimersCollection):
    def __init__(self, timers: Iterable[IdentifiableTimer] = ()):
        self._timers = {timer.id: timer for timer in timers}

    def __len__(self) -> int:
        return len(self._timers)

    def __iter__(self) -> Iterator[IdentifiableTimer]:
        return iter(self._timers.values())

    def get(self, timer_id: TimerId) -> IdentifiableTimer:
        return self._timers[timer_id]

    def add(self, timer: Timer) -> IdentifiableTimer:
        if isinstance(timer, IdentifiableTimer):
            if timer.id in self._timers:
                raise ValueError(f"Timer with id {timer.id} already exists")
            self._timers[timer.id] = timer
            return timer
        else:
            timer_id = self._create_timer_id()
            identifiable_timer = IdentifiableTimer.from_timer(timer, timer_id)
            return self.add(identifiable_timer)

    def remove(self, timer_id: TimerId) -> bool:
        try:
            del self._timers[timer_id]
            return True
        except KeyError:
            return False

    def _create_timer_id(self) -> TimerId:
        timer_ids = sorted(timer.id for timer in self)
        if len(timer_ids) == 0:
            return TimerId(0)
        for i in range(len(timer_ids)):
            if timer_ids[i] != i:
                return TimerId(i)
        return TimerId(i + 1)
