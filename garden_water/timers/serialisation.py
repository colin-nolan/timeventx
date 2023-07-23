from dataclasses import fields
from datetime import timedelta
from time import strftime, strptime

from garden_water.timers.timers import START_TIME_FORMAT, Timer, DayTime


def serialise_daytime(start_time: DayTime) -> str:
    return f"{start_time.hour:02}:{start_time.minute:02}:{start_time.second:02}"


def deserialise_daytime(start_time: str) -> DayTime:
    return DayTime(int(start_time[0:2]), int(start_time[3:5]), int(start_time[6:8]))


def timer_to_json(timer: Timer) -> dict:
    serialisable = {}
    for field in fields(timer):
        field_name = field.name
        field_value = getattr(timer, field_name)
        if isinstance(field_value, DayTime):
            serialisable_field_value = serialise_daytime(field_value)
        elif isinstance(field_value, timedelta):
            serialisable_field_value = field_value.total_seconds()
        else:
            serialisable_field_value = field_value
        serialisable[field_name] = serialisable_field_value
    return serialisable
