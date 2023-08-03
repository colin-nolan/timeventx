import json
from datetime import timedelta
from typing import Optional

from microdot_asyncio import Microdot, Request, Response, abort

from garden_water._logging import get_logger
from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.collections.database import TimersDatabase
from garden_water.timers.serialisation import deserialise_daytime, timer_to_json
from garden_water.timers.timers import Timer

_TIMERS_DATABASE_SINGLETON: Optional[TimersDatabase] = None

_HTTP_CODE_BAD_RESPONSE = 400
_HTTP_CODE_FORBIDDEN_RESPONSE = 403
_CONTENT_TYPE_APPLICATION_JSON = "application/json"


Response.default_content_type = _CONTENT_TYPE_APPLICATION_JSON

logger = get_logger(__name__)
app = Microdot()


def set_timers_database(timers_database: IdentifiableTimersCollection):
    global _TIMERS_DATABASE_SINGLETON
    _TIMERS_DATABASE_SINGLETON = timers_database


def get_timers_database() -> IdentifiableTimersCollection:
    if _TIMERS_DATABASE_SINGLETON is None:
        raise RuntimeError("Timers database single has not been set")
    return _TIMERS_DATABASE_SINGLETON


@app.get("/healthcheck")
def get_health(request: Request):
    return json.dumps(True)


@app.get("/timers")
def get_timers(request: Request):
    return json.dumps([timer_to_json(timer) for timer in get_timers_database()])


@app.post("/timer")
def post_timer(request: Request):
    if request.content_type is None:
        # request.json is only available if content type is set (it assumes a lot of the client!)
        request.content_type = _CONTENT_TYPE_APPLICATION_JSON

    serialised_timer = request.json
    if serialised_timer is None:
        abort(_HTTP_CODE_BAD_RESPONSE, f"Timer attributes must be set")
    if serialised_timer.get("id") is not None:
        abort(_HTTP_CODE_FORBIDDEN_RESPONSE, f"Timer cannot be posted with an ID")
    try:
        start_time = deserialise_daytime(serialised_timer["start_time"])
    except (KeyError, ValueError) as e:
        abort(_HTTP_CODE_BAD_RESPONSE, f"Invalid start_time: {e}")

    try:
        timer = Timer(
            name=serialised_timer["name"],
            start_time=start_time,
            duration=timedelta(seconds=int(serialised_timer["duration"])),
        )
    except TypeError | KeyError as e:
        abort(_HTTP_CODE_BAD_RESPONSE, f"Invalid timer attributes: {e}")
    identifiable_timer = get_timers_database().add(timer)
    return json.dumps(timer_to_json(identifiable_timer))


@app.route("/stats")
async def index(request: Request):
    import gc

    output = _get_memory_usage()
    gc.collect()
    output = f"{output}<br>{_get_memory_usage()}"

    return output, 200, {"Content-Type": "text/html"}


def _get_memory_usage() -> str:
    import gc

    allocated_memory = gc.mem_alloc()
    free_memory = gc.mem_free()
    total_memory = allocated_memory + free_memory

    return f"{allocated_memory} / {total_memory} bytes ({(allocated_memory / total_memory) * 100}%), {free_memory} bytes free"


# import os
# import machine
#
# s = os.statvfs('/')
# logger.info(f"Free storage: {s[0] * s[3] / 1024} KB")
# logger.info(f"CPU Freq: {machine.freq() / 1000000}Mhz")


# TODO: a reset endpoint that resets the device
