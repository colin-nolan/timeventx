import json
from datetime import timedelta

from microdot_asyncio import Microdot, Request, Response, abort

from garden_water._logging import get_logger
from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.collections.database import TimersDatabase
from garden_water.timers.collections.memory import InMemoryIdentifiableTimersCollection
from garden_water.timers.serialisation import deserialise_daytime, timer_to_json
from garden_water.timers.timers import Timer

# DATABASE_LOCATION_ENVIRONMENT_VARIABLE = "GARDEN_WATER_DATABASE_LOCATION"
# DEFAULT_DATABASE_LOCATION = "sqlite:///garden-water.sqlite"

_TIMERS_DATABASE_SINGLETONS: dict[str, TimersDatabase] = {}
_HTTP_CODE_BAD_RESPONSE = 400
_HTTP_CODE_FORBIDDEN_RESPONSE = 403


Response.default_content_type = "application/json"


logger = get_logger(__name__)

app = Microdot()


_TEMP_IN_MEMORY_TIMERS_COLLECTION = InMemoryIdentifiableTimersCollection()


def get_timers_database() -> IdentifiableTimersCollection:
    """
    Gets timers database singleton for the database location specified via the `DATABASE_LOCATION_ENVIRONMENT_VARIABLE`
    environment variable.
    :return: the database
    """
    # database_location = os.getenv(DATABASE_LOCATION_ENVIRONMENT_VARIABLE, DEFAULT_DATABASE_LOCATION)
    # database = _TIMERS_DATABASE_SINGLETONS.get(database_location)
    # if database is None:
    #     database = TimersDatabase(database_location)
    #     _TIMERS_DATABASE_SINGLETONS[database_location] = database
    # return database
    return _TEMP_IN_MEMORY_TIMERS_COLLECTION


@app.get("/healthcheck")
def get_health(request: Request):
    return json.dumps(True)


@app.get("/timers")
def get_timers(request):
    return json.dumps([timer_to_json(timer) for timer in get_timers_database()])


@app.post("/timer")
def post_timer(request):
    serialised_timer = request.GetPostedJSONObject()
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
async def index(request):
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


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()


# import os
# import machine
#
# s = os.statvfs('/')
# logger.info(f"Free storage: {s[0] * s[3] / 1024} KB")
# logger.info(f"CPU Freq: {machine.freq() / 1000000}Mhz")


# TODO: a reset endpoint that resets the device
