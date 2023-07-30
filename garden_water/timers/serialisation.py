from garden_water.timers.timers import DayTime, IdentifiableTimer, Timer


def serialise_daytime(start_time: DayTime) -> str:
    return f"{start_time.hour:02}:{start_time.minute:02}:{start_time.second:02}"


def deserialise_daytime(start_time: str) -> DayTime:
    return DayTime(int(start_time[0:2]), int(start_time[3:5]), int(start_time[6:8]))


def timer_to_json(timer: Timer | IdentifiableTimer) -> dict:
    base = {"id": timer.id} if isinstance(timer, IdentifiableTimer) else {}
    # Note: don't merge dicts using double splat operator as MicroPython does not like it
    return base | {
        "name": timer.name,
        "start_time": serialise_daytime(timer.start_time),
        "duration": timer.duration.total_seconds(),
    }
