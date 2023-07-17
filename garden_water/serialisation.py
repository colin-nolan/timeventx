from dataclasses import fields
from datetime import timedelta
from time import strftime, strptime, struct_time

from garden_water.models import START_TIME_FORMAT, Timer


def serialise_start_time(start_time: struct_time) -> str:
    return strftime(START_TIME_FORMAT, start_time)


def deserialise_start_time(start_time: str) -> struct_time:
    return strptime(start_time, START_TIME_FORMAT)


def timer_to_json(timer: Timer) -> dict:
    serialisable = {}
    for field in fields(timer):
        field_name = field.name
        field_value = getattr(timer, field_name)
        if isinstance(field_value, struct_time):
            serialisable_field_value = serialise_start_time(field_value)
        elif isinstance(field_value, timedelta):
            serialisable_field_value = field_value.total_seconds()
        else:
            serialisable_field_value = field_value
        serialisable[field_name] = serialisable_field_value
    return serialisable
