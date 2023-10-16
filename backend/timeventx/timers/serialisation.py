from datetime import timedelta

from timeventx.timers.timers import DayTime, IdentifiableTimer, Timer, TimerId


def serialise_daytime(start_time: DayTime) -> str:
    return f"{start_time.hour:02}:{start_time.minute:02}:{start_time.second:02}"


def deserialise_daytime(start_time: str) -> DayTime:
    return DayTime(int(start_time[0:2]), int(start_time[3:5]), int(start_time[6:8]))


def timer_to_json(timer: Timer | IdentifiableTimer) -> dict:
    base = {"id": timer.id} if isinstance(timer, IdentifiableTimer) else {}
    # Note: don't merge dicts using double splat operator as MicroPython does not like it
    return base | {
        "name": timer.name,
        "startTime": serialise_daytime(timer.start_time),
        "duration": timer.duration.total_seconds(),
    }


def json_to_identifiable_timer(timer_json: dict) -> IdentifiableTimer:
    return IdentifiableTimer(
        timer_id=TimerId(timer_json["id"]),
        name=timer_json["name"],
        start_time=deserialise_daytime(timer_json["startTime"]),
        duration=timedelta(seconds=timer_json["duration"]),
    )
