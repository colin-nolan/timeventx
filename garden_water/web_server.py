import json
import os
from time import sleep
from types import MappingProxyType

from garden_water.database import TimersDatabase
from garden_water.models import Timer
from vendored.MicroWebSrv.microWebSrv import MicroWebSrv

DATABASE_LOCATION = os.getenv("GARDEN_WATER_DATABASE_LOCATION", "sqlite:///garden-water.sqlite")
TIMERS_CONTAINER_SINGLETON = TimersDatabase(DATABASE_LOCATION)

_CONTENT_TYPE_APPLICATION_JSON = "application/json"
_CONTENT_TYPE_TEXT_PLAIN = "text/plain"
_CONTENT_CHARSET_UTF8 = "UTF-8"

_HTTP_CODE_OK = 200
_HTTP_CODE_BAD_RESPONSE = 400


def _write_error_response(http_response, code, message):
    _write_response(http_response, content=message, code=code, content_type=_CONTENT_TYPE_TEXT_PLAIN)


def _write_response(
    http_response,
    content: str,
    code: int = _HTTP_CODE_OK,
    headers: dict = MappingProxyType({}),
    content_type: str = _CONTENT_TYPE_APPLICATION_JSON,
):
    headers = {"Access-Control-Allow-Origin": "*", **headers}
    http_response.WriteResponse(code, headers, content_type, _CONTENT_CHARSET_UTF8, content)


@MicroWebSrv.route("/timers", "GET")
def get_timers(httpClient, httpResponse):
    timers = TIMERS_CONTAINER_SINGLETON.get_all()
    # FIXME: very likely requires conversion to dict
    _write_response(httpResponse, json.dumps(timers))


@MicroWebSrv.route("/timer", "POST")
def _httpHandlerTestPost(httpClient, httpResponse):
    serialised_timer = httpClient.ReadRequestContentAsJSON()
    try:
        timer = Timer(**serialised_timer)
    except TypeError as e:
        _write_error_response(httpResponse, _HTTP_CODE_BAD_RESPONSE, f"Invalid timer attributes: {e}")
        return
    identifier = TIMERS_CONTAINER_SINGLETON.add(timer)
    _write_response(httpResponse, str(identifier))


# @MicroWebSrv.route("/edit/<index>")  # <IP>/edit/123           ->   args['index']=123
# @MicroWebSrv.route("/edit/<index>/abc/<foo>")  # <IP>/edit/123/abc/bar   ->   args['index']=123  args['foo']='bar'
# @MicroWebSrv.route("/edit")  # <IP>/edit               ->   args={}
# def _httpHandlerEditWithArgs(httpClient, httpResponse, args={}):


srv = MicroWebSrv(webPath="www/", port=8080)
srv.MaxWebSocketRecvLen = 256
srv.WebSocketThreaded = True
srv.Start(threaded=True)

print("Hello world")

while True:
    sleep(999999)

# ----------------------------------------------------------------------------
