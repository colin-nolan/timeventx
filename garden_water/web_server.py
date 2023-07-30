
import sys
sys.path.insert(0, "/home/colin/projects/garden-watering/build/any/lib")
import os
from datetime import timedelta
from time import sleep

from MicroWebSrv2 import GET, POST, HttpRequest
from MicroWebSrv2 import MicroWebSrv2 as MicroWebSrv2Class
from MicroWebSrv2 import WebRoute

from garden_water.timers.collections.database import TimersDatabase
from garden_water.timers.serialisation import deserialise_daytime, timer_to_json
from garden_water.timers.timers import Timer

DATABASE_LOCATION_ENVIRONMENT_VARIABLE = "GARDEN_WATER_DATABASE_LOCATION"
DEFAULT_DATABASE_LOCATION = "sqlite:///garden-water.sqlite"

_TIMERS_DATABASE_SINGLETONS: dict[str, TimersDatabase] = {}
_HTTP_CODE_BAD_RESPONSE = 400
_HTTP_CODE_FORBIDDEN_RESPONSE = 403


def get_timers_database() -> TimersDatabase:
    """
    Gets timers database singleton for the database location specified via the `DATABASE_LOCATION_ENVIRONMENT_VARIABLE`
    environment variable.
    :return: the database
    """
    database_location = os.getenv(DATABASE_LOCATION_ENVIRONMENT_VARIABLE, DEFAULT_DATABASE_LOCATION)
    database = _TIMERS_DATABASE_SINGLETONS.get(database_location)
    if database is None:
        database = TimersDatabase(database_location)
        _TIMERS_DATABASE_SINGLETONS[database_location] = database
    return database


@WebRoute(GET, "/healthcheck")
def get_health(microWebSrv2: MicroWebSrv2Class, request: HttpRequest):
    request.Response.ReturnOkJSON(True)


@WebRoute(GET, "/timers")
def get_timers(microWebSrv2: MicroWebSrv2Class, request: HttpRequest):
    request.Response.ReturnOkJSON([timer_to_json(timer) for timer in get_timers_database()])


@WebRoute(POST, "/timer")
def post_timer(microWebSrv2: MicroWebSrv2Class, request: HttpRequest):
    serialised_timer = request.GetPostedJSONObject()
    if serialised_timer is None:
        request.Response.Return(_HTTP_CODE_BAD_RESPONSE, f"Timer attributes must be set")
        return
    if serialised_timer.get("id") is not None:
        request.Response.Return(_HTTP_CODE_FORBIDDEN_RESPONSE, f"Timer cannot be posted with an ID")
        return
    try:
        start_time = deserialise_daytime(serialised_timer["start_time"])
    except (KeyError, ValueError) as e:
        request.Response.Return(_HTTP_CODE_BAD_RESPONSE, f"Invalid start_time: {e}")
        return

    try:
        timer = Timer(
            name=serialised_timer["name"],
            start_time=start_time,
            duration=timedelta(seconds=int(serialised_timer["duration"])),
        )
    except TypeError | KeyError as e:
        request.Response.Return(_HTTP_CODE_BAD_RESPONSE, f"Invalid timer attributes: {e}")
        return
    identifiable_timer = get_timers_database().add(timer)
    request.Response.ReturnOkJSON(timer_to_json(identifiable_timer))


def create_web_server(port: int, interface: str = "0.0.0.0") -> MicroWebSrv2Class:
    web_server = MicroWebSrv2Class()
    web_server.SetEmbeddedConfig()
    web_server.CORSAllowAll = True
    web_server.AllowAllOrigins = True
    web_server.BindAddress = (interface, port)
    # web_server._bindAddr = socket.getaddrinfo(interface, port)[0][-1]
    return web_server


def main():
    web_server = create_web_server(8080)
    web_server.StartManaged()

    try:
        while web_server.IsRunning:
            sleep(1)
    except KeyboardInterrupt:
        pass

    web_server.Stop()


if __name__ == "__main__":
    main()
