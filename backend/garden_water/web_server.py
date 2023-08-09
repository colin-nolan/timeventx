import _thread
import json
import os
from datetime import timedelta
from pathlib import Path

from microdot_asyncio import Microdot, Request, abort, send_file, Response

from garden_water._common import RP2040_DETECTED, resolve_path
from garden_water._logging import (
    get_logger,
    flush_file_logs,
)
from garden_water.configuration import Configuration, ConfigurationNotFoundError
from garden_water.timers.serialisation import deserialise_daytime, timer_to_json
from garden_water.timers.timers import Timer

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

# TODO: make constants of class like standard lib
# http module is not available in MicroPython
_HTTP_CODE_OK_RESPONSE = 200
_HTTP_CODE_ACCEPTED_RESPONSE = 202
_HTTP_CODE_BAD_RESPONSE = 400
_HTTP_CODE_NOT_FOUND = 404
_HTTP_CODE_FORBIDDEN_RESPONSE = 403
_HTTP_CODE_NOT_IMPLEMENTED = 501
_CONTENT_TYPE_APPLICATION_JSON = "application/json"

_KNOWN_CONTENT_TYPES = {
    ".css": "text/css",
    ".html": "text/html",
    ".js": "application/javascript",
    ".json": "application/json",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".txt": "text/plain",
    ".jpg": "image/jpeg",
}

API_VERSION = "v1"


logger = get_logger(__name__)
app = Microdot()


@app.before_request
def _before_request(request: Request):
    logger.debug(f"{request.method} {request.path}")


@app.after_request
def _after_request(request: Request, response: Response):
    logger.info(f"{response.status_code} {request.method} {request.path}")
    return response


@app.after_error_request
def _after_error_request(request: Request, response: Response):
    return _after_request(request, response)


# TODO: return type
@app.get(f"/api/{API_VERSION}/healthcheck")
async def get_healthcheck(request: Request):
    return json.dumps(True)


@app.get(f"/api/{API_VERSION}/timers")
async def get_timers(request: Request):
    return json.dumps([timer_to_json(timer) for timer in request.app.database])


@app.post(f"/api/{API_VERSION}/timer")
async def post_timer(request: Request):
    if request.content_type is None:
        # request.json is only available if content type is set (it assumes a lot of the client!)
        request.content_type = _CONTENT_TYPE_APPLICATION_JSON

    serialised_timer = request.json
    if serialised_timer is None:
        abort(_HTTP_CODE_BAD_RESPONSE, f"Timer attributes must be set")
        raise
    if serialised_timer.get("id") is not None:
        abort(_HTTP_CODE_FORBIDDEN_RESPONSE, f"Timer cannot be posted with an ID")
        raise
    try:
        start_time = deserialise_daytime(serialised_timer["start_time"])
    except (KeyError, ValueError) as e:
        abort(_HTTP_CODE_BAD_RESPONSE, f"Invalid start_time: {e}")
        raise

    try:
        timer = Timer(
            name=serialised_timer["name"],
            start_time=start_time,
            duration=timedelta(seconds=int(serialised_timer["duration"])),
        )
    except TypeError | KeyError as e:
        abort(_HTTP_CODE_BAD_RESPONSE, f"Invalid timer attributes: {e}")
        raise
    identifiable_timer = request.app.database.add(timer)

    return json.dumps(timer_to_json(identifiable_timer))


@app.route(f"/api/{API_VERSION}/stats")
async def get_stats(request: Request):
    if not RP2040_DETECTED:
        abort(_HTTP_CODE_NOT_IMPLEMENTED, "Not implemented on non-RP2040 devices")

    output = f"Memory: {_get_memory_usage()}<br>Storage: {_get_disk_usage()}"

    return output, _HTTP_CODE_OK_RESPONSE, {"Content-Type": "text/html"}


# TODO: This should be a post
@app.route(f"/api/{API_VERSION}/reset")
async def get_reset(request: Request):
    # Shutdown after a slight delay in order to allow the response to be returned
    def delayed_shutdown():
        import time

        time.sleep(1)
        logger.info("Shutting down")
        request.app.shutdown()

    # Shutdown in another thread to allow response to return
    _thread.start_new_thread(delayed_shutdown, ())

    return "Resetting device", _HTTP_CODE_ACCEPTED_RESPONSE, {"Content-Type": "text/html"}


@app.route(f"/api/{API_VERSION}/logs")
async def get_logs(request: Request):
    try:
        log_location = request.app.configuration[Configuration.LOG_FILE_LOCATION]
    except ConfigurationNotFoundError:
        abort(_HTTP_CODE_NOT_IMPLEMENTED, "Logs not being saved to file")
        raise
    flush_file_logs()
    return send_file(str(log_location), max_age=0, content_type="text/plain")


@app.route(f"/")
async def get_root(request: Request):
    return serve_ui(request, Path("index.html"))


# This route MUST be defined last
@app.route(f"/<re:.*:path>")
async def get(request: Request, path: str):
    return serve_ui(request, Path(path))


def serve_ui(request: Request, path: Path):
    # MicroPython `pathlib` implementation does not support `is_absolute`
    if str(path).startswith("/"):
        abort(_HTTP_CODE_NOT_FOUND)
        raise

    try:
        frontend_location = request.app.configuration[Configuration.FRONTEND_ROOT_DIRECTORY]
    except ConfigurationNotFoundError:
        # The pathlib library in use with MicroPython has a bug where `Path.resolve` returns a `str` instead of a `Path`
        frontend_location = Path(Path(__file__).resolve()).parent / "../../frontend/dist"
    frontend_location = resolve_path(frontend_location)

    try:
        # `Path.__truediv__` is not implemented in `pathlib` module in use with MicroPython
        full_path = resolve_path(Path(f"{frontend_location}/{path}"))
    except OSError:
        abort(_HTTP_CODE_NOT_FOUND)
        raise

    if not str(full_path).startswith(str(frontend_location)) or "../" in str(full_path):
        abort(_HTTP_CODE_NOT_FOUND)
        raise

    if not full_path.exists() or not full_path.is_file():
        abort(_HTTP_CODE_NOT_FOUND)
        raise

    content_type = _get_content_type(full_path)

    logger.info(f"Serving {full_path}")
    return send_file(str(full_path), max_age=0, content_type=content_type)


def _get_memory_usage() -> str:
    import gc

    # MicroPython only calls the GC when it runs low on memory so collect needs to be called before getting a reading of
    # non-garbaged memory usage
    gc.collect()
    allocated_memory = gc.mem_alloc()
    free_memory = gc.mem_free()
    total_memory = allocated_memory + free_memory

    return f"{allocated_memory} / {total_memory} bytes ({(allocated_memory / total_memory) * 100}%), {free_memory} bytes free"


def _get_disk_usage() -> str:
    storage = os.statvfs("/")
    free_kb = storage[0] * storage[3] / 1024
    total_kb = storage[0] * storage[2] / 1024
    used_kb = total_kb - free_kb

    return f"{used_kb} / {total_kb} KB ({used_kb / total_kb * 100}%), {free_kb} KB free"


# mimetypes module does not exist for MicroPython
def _get_content_type(path: Path) -> str:
    try:
        return _KNOWN_CONTENT_TYPES[path.suffix]
    except KeyError:
        return "application/octet-stream"
