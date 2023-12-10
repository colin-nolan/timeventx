import json
from datetime import timedelta
from pathlib import Path
from typing import TypeAlias

from microdot_asyncio import Microdot, Request, Response, abort, send_file
from microdot_cors import CORS

from timeventx._common import RP2040_DETECTED, resolve_path
from timeventx._logging import clear_logs, flush_file_logs, get_logger
from timeventx.app_utils import (
    ContentType,
    HttpStatus,
    create_content_type_header,
    get_content_type,
    handle_authorisation,
)
from timeventx.configuration import Configuration, ConfigurationNotFoundError
from timeventx.rp2040 import get_disk_usage, get_memory_usage
from timeventx.timers.serialisation import (
    deserialise_daytime,
    serialise_daytime,
    timer_to_json,
)
from timeventx.timers.timers import IdentifiableTimer, Timer, TimerId

API_VERSION = "v1"

EndpointResponse: TypeAlias = Response | str | tuple[str, int] | tuple[str, int, dict[str, str]]

logger = get_logger(__name__)
app = Microdot()
CORS(app, allowed_origins="*", allow_credentials=True)


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


@app.get(f"/api/{API_VERSION}/healthcheck")
# Deliberately put behind auth check
async def get_healthcheck(request: Request) -> EndpointResponse:
    return json.dumps(True), HttpStatus.OK, create_content_type_header(ContentType.JSON)


@app.get(f"/api/{API_VERSION}/timers")
@handle_authorisation
async def get_timers(request: Request) -> EndpointResponse:
    return (
        json.dumps([timer_to_json(timer) for timer in request.app.database]),
        HttpStatus.OK,
        create_content_type_header(ContentType.JSON),
    )


@app.post(f"/api/{API_VERSION}/timer")
@handle_authorisation
async def post_timer(request: Request) -> EndpointResponse:
    timer = _create_timer_from_request(request)

    if isinstance(timer, IdentifiableTimer):
        abort(HttpStatus.FORBIDDEN, f"Timer cannot be posted with an ID (it will be automatically assigned)")

    identifiable_timer = request.app.database.add(timer)
    return (
        json.dumps(timer_to_json(identifiable_timer)),
        HttpStatus.CREATED,
        create_content_type_header(ContentType.JSON),
    )


@app.put(f"/api/{API_VERSION}/timer/<int:timer_id>")
@handle_authorisation
async def put_timer(request: Request, timer_id: TimerId) -> EndpointResponse:
    timer = _create_timer_from_request(request)
    request.app.database.remove(timer_id)
    request.app.database.add(timer)
    return json.dumps(timer_to_json(timer)), HttpStatus.CREATED, create_content_type_header(ContentType.JSON)


def _create_timer_from_request(request: Request) -> Timer | IdentifiableTimer:
    if request.content_type is None:
        # request.json is only available if content type is set (it assumes a lot of the client!)
        request.content_type = ContentType.JSON

    try:
        serialised_timer = request.json
    except json.JSONDecodeError:
        abort(HttpStatus.BAD_REQUEST, f"Invalid JSON")
    if serialised_timer is None:
        abort(HttpStatus.BAD_REQUEST, f"Timer attributes must be set")
    try:
        start_time = deserialise_daytime(serialised_timer["startTime"])
    except (KeyError, ValueError, TypeError) as e:
        abort(HttpStatus.BAD_REQUEST, f"Invalid start_time: {e}")

    arguments = dict(
        name=serialised_timer["name"],
        start_time=start_time,
        duration=timedelta(seconds=int(serialised_timer["duration"])),
    )
    timer_type = Timer
    if serialised_timer.get("id") is not None:
        arguments["timer_id"] = serialised_timer["id"]
        timer_type = IdentifiableTimer

    try:
        return timer_type(**arguments)
    except (TypeError, KeyError, ValueError) as e:
        abort(HttpStatus.BAD_REQUEST, f"Invalid timer attributes: {e}")


@app.delete(f"/api/{API_VERSION}/timer/<int:timer_id>")
@handle_authorisation
async def delete_timer(request: Request, timer_id: TimerId) -> EndpointResponse:
    removed = request.app.database.remove(timer_id)
    return (
        json.dumps(removed),
        HttpStatus.OK if removed else HttpStatus.NOT_FOUND,
        create_content_type_header(ContentType.JSON),
    )


@app.get(f"/api/{API_VERSION}/intervals")
@handle_authorisation
async def get_intervals(request: Request) -> EndpointResponse:
    return (
        json.dumps(
            [
                {"startTime": serialise_daytime(interval.start_time), "endTime": serialise_daytime(interval.end_time)}
                for interval in request.app.timer_runner.on_off_intervals
            ]
        ),
        HttpStatus.OK,
        create_content_type_header(ContentType.JSON),
    )


@app.get(f"/api/{API_VERSION}/stats")
@handle_authorisation
async def get_stats(request: Request) -> EndpointResponse:
    if not RP2040_DETECTED:
        abort(HttpStatus.NOT_IMPLEMENTED, "Not implemented on non-RP2040 devices")

    output = f"Memory: {get_memory_usage()}\nStorage: {get_disk_usage()}"

    return output, HttpStatus.OK, create_content_type_header(ContentType.TEXT)


@app.post(f"/api/{API_VERSION}/reset")
@handle_authorisation
async def post_reset(request: Request) -> EndpointResponse:
    if not RP2040_DETECTED:
        abort(HttpStatus.NOT_IMPLEMENTED, "Not implemented on non-RP2040 devices")

    def reset_device():
        import machine

        logger.info("Resetting device")
        flush_file_logs()
        machine.reset()

    reset_device()

    # TODO: schedule the reset to allow a 202 to be returned, instead of dropping the connection


@app.get(f"/api/{API_VERSION}/logs")
@handle_authorisation
async def get_logs(request: Request) -> EndpointResponse:
    try:
        log_location = request.app.configuration[Configuration.LOG_FILE_LOCATION]
    except ConfigurationNotFoundError:
        abort(HttpStatus.NOT_IMPLEMENTED, "Logs not being saved to file")
    flush_file_logs()

    if log_location.exists():
        return send_file(str(log_location), max_age=0, content_type=ContentType.TEXT)
    else:
        return "", HttpStatus.OK, create_content_type_header(ContentType.TEXT)


@app.delete(f"/api/{API_VERSION}/logs")
@handle_authorisation
async def delete_logs(request: Request) -> EndpointResponse:
    try:
        request.app.configuration[Configuration.LOG_FILE_LOCATION]
    except ConfigurationNotFoundError:
        abort(HttpStatus.NOT_IMPLEMENTED, "Logs not being saved to file")

    clear_logs()

    return "", HttpStatus.OK, create_content_type_header(ContentType.TEXT)


@app.post(f"/api/{API_VERSION}/shutdown")
@handle_authorisation
async def post_shutdown(request: Request) -> EndpointResponse:
    logger.info("Server shutting down")
    flush_file_logs()
    # TODO: delay shutdown to allow a 202 to be returned, instead of dropping the connection
    request.app.shutdown()
    return "Shutting down...", HttpStatus.ACCEPTED


@app.get(f"/")
@handle_authorisation
async def get_root(request: Request) -> EndpointResponse:
    return serve_ui(request, Path("index.html"))


# This route MUST be defined last
@app.get(f"/<re:.*:path>")
@handle_authorisation
async def get_file(request: Request, path: str) -> EndpointResponse:
    return serve_ui(request, Path(path))


def serve_ui(request: Request, path: Path):
    # MicroPython `pathlib` implementation does not support `is_absolute`
    if str(path).startswith("/"):
        abort(HttpStatus.NOT_FOUND, "Path should not start with double slash //")

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
        abort(HttpStatus.NOT_FOUND)

    if (
        not str(full_path).startswith(str(frontend_location))
        or "../" in str(full_path)
        or not full_path.exists()
        or not full_path.is_file()
    ):
        abort(HttpStatus.NOT_FOUND)

    content_type = get_content_type(full_path)

    logger.info(f"Serving {full_path}")
    return send_file(str(full_path), max_age=0, content_type=content_type)
