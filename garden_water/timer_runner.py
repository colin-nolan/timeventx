from garden_water.models import TimersContainer, ImmutableTimersContainer


class TimerRunner:
    def __init__(self, timers: ImmutableTimersContainer):
        self.timers = TimersContainer(timers)

    def run(self):
        pass
