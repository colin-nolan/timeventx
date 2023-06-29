import os
from time import sleep, strptime

from MicroWebSrv2 import GET, POST, HttpRequest
from MicroWebSrv2 import MicroWebSrv2 as MicroWebSrv2Class
from MicroWebSrv2 import WebRoute

from garden_water.database import TimersDatabase
from garden_water.models import Timer

DATABASE_LOCATION = os.getenv("GARDEN_WATER_DATABASE_LOCATION", "sqlite:///garden-water.sqlite")
TIMERS_CONTAINER_SINGLETON = TimersDatabase(DATABASE_LOCATION)

_HTTP_CODE_BAD_RESPONSE = 400


@WebRoute(GET, "/hello")
def RequestTestRedirect(microWebSrv2: MicroWebSrv2Class, request: HttpRequest):
    request.Response.ReturnOk("Hello World")


@WebRoute(GET, "/timers")
def get_timers(microWebSrv2: MicroWebSrv2Class, request: HttpRequest):
    timers = TIMERS_CONTAINER_SINGLETON.get_all()
    request.Response.ReturnOkJSON(timers)


@WebRoute(POST, "/timer")
def post_timer(microWebSrv2: MicroWebSrv2Class, request: HttpRequest):
    serialised_timer = request.GetPostedJSONObject()
    if serialised_timer is None:
        request.Response.Return(_HTTP_CODE_BAD_RESPONSE, f"Timer attributes must be set")
        return
    try:
        start_time = strptime(serialised_timer["start_time"], "%H:%M:%S")
    except KeyError | ValueError as e:
        request.Response.Return(_HTTP_CODE_BAD_RESPONSE, f"Invalid start_time: {e}")
        return

    try:
        timer = Timer(name=serialised_timer["name"], start_time=start_time, duration=serialised_timer["duration"], enabled=serialised_timer["enabled"])
    except TypeError | KeyError as e:
        request.Response.Return(_HTTP_CODE_BAD_RESPONSE, f"Invalid timer attributes: {e}")
        return
    identifier = TIMERS_CONTAINER_SINGLETON.add(timer)
    request.Response.ReturnOkJSON(identifier)


def create_web_server(port: int, interface: str = "0.0.0.0") -> MicroWebSrv2Class:
    web_server = MicroWebSrv2Class()
    web_server.SetEmbeddedConfig()
    web_server.CORSAllowAll = True
    web_server.AllowAllOrigins = True
    web_server.BindAddress = (interface, port)
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
