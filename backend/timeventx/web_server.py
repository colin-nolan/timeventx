import json
from datetime import timedelta
from pathlib import Path

from microdot_asyncio import Microdot, Request, Response, abort, send_file
from microdot_cors import CORS

from timeventx._common import RP2040_DETECTED, resolve_path
from timeventx._logging import clear_logs, flush_file_logs, get_logger
from timeventx.configuration import Configuration, ConfigurationNotFoundError
from timeventx.rp2040 import get_disk_usage, get_memory_usage
from timeventx.timers.serialisation import (
    deserialise_daytime,
    serialise_daytime,
    timer_to_json,
)
from timeventx.timers.timers import IdentifiableTimer, Timer, TimerId


class HTTPStatus:
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    BAD_REQUEST = 400
    NOT_FOUND = 404
    FORBIDDEN = 403
    NOT_IMPLEMENTED = 501


class ContentType:
    CSS = "text/css"
    HTML = "text/html"
    JAVASCRIPT = "application/javascript"
    JSON = "application/json"
    PNG = "image/png"
    SVG = "image/svg+xml"
    TEXT = "text/plain"
    JPG = "image/jpeg"
    OCTET_STREAM = "application/octet-stream"


FILE_EXTENSION_TO_CONTENT_TYPE = {
    ".css": ContentType.CSS,
    ".html": ContentType.HTML,
    ".js": ContentType.JAVASCRIPT,
    ".json": ContentType.JSON,
    ".png": ContentType.PNG,
    ".svg": ContentType.SVG,
    ".txt": ContentType.TEXT,
    ".jpg": ContentType.JPG,
}

API_VERSION = "v1"


logger = get_logger(__name__)
app = Microdot()
CORS(app, allowed_origins="*", allow_credentials=True)


# TODO: consider decorator instead
def _create_content_type_header(content_type: str) -> dict:
    return {"Content-Type": content_type}


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
    return json.dumps(True), HTTPStatus.OK, _create_content_type_header(ContentType.JSON)


@app.get(f"/api/{API_VERSION}/timers")
async def get_timers(request: Request):
    return (
        json.dumps([timer_to_json(timer) for timer in request.app.database]),
        HTTPStatus.OK,
        _create_content_type_header(ContentType.JSON),
    )


@app.post(f"/api/{API_VERSION}/timer")
async def post_timer(request: Request):
    timer = _create_timer_from_request(request)

    if isinstance(timer, IdentifiableTimer):
        abort(HTTPStatus.FORBIDDEN, f"Timer cannot be posted with an ID (it will be automatically assigned)")

    identifiable_timer = request.app.database.add(timer)
    return (
        json.dumps(timer_to_json(identifiable_timer)),
        HTTPStatus.CREATED,
        _create_content_type_header(ContentType.JSON),
    )


@app.put(f"/api/{API_VERSION}/timer/<int:timer_id>")
async def put_timer(request: Request, timer_id: TimerId):
    timer = _create_timer_from_request(request)
    request.app.database.remove(timer_id)
    request.app.database.add(timer)
    return json.dumps(timer_to_json(timer)), HTTPStatus.CREATED, _create_content_type_header(ContentType.JSON)


def _create_timer_from_request(request: Request) -> Timer | IdentifiableTimer:
    if request.content_type is None:
        # request.json is only available if content type is set (it assumes a lot of the client!)
        request.content_type = ContentType.JSON

    try:
        serialised_timer = request.json
    except json.JSONDecodeError:
        abort(HTTPStatus.BAD_REQUEST, f"Invalid JSON")
    if serialised_timer is None:
        abort(HTTPStatus.BAD_REQUEST, f"Timer attributes must be set")
    try:
        start_time = deserialise_daytime(serialised_timer["startTime"])
    except (KeyError, ValueError, TypeError) as e:
        abort(HTTPStatus.BAD_REQUEST, f"Invalid start_time: {e}")

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
        abort(HTTPStatus.BAD_REQUEST, f"Invalid timer attributes: {e}")


@app.delete(f"/api/{API_VERSION}/timer/<int:timer_id>")
async def delete_timer(request: Request, timer_id: TimerId):
    removed = request.app.database.remove(timer_id)
    return (
        json.dumps(removed),
        HTTPStatus.OK if removed else HTTPStatus.NOT_FOUND,
        _create_content_type_header(ContentType.JSON),
    )


@app.get(f"/api/{API_VERSION}/intervals")
async def get_intervals(request: Request):
    return (
        json.dumps(
            [
                {"startTime": serialise_daytime(interval.start_time), "endTime": serialise_daytime(interval.end_time)}
                for interval in request.app.timer_runner.on_off_intervals
            ]
        ),
        HTTPStatus.OK,
        _create_content_type_header(ContentType.JSON),
    )


@app.get(f"/api/{API_VERSION}/stats")
async def get_stats(request: Request):
    if not RP2040_DETECTED:
        abort(HTTPStatus.NOT_IMPLEMENTED, "Not implemented on non-RP2040 devices")

    output = f"Memory: {get_memory_usage()}\nStorage: {get_disk_usage()}"

    return output, HTTPStatus.OK, _create_content_type_header(ContentType.TEXT)


@app.post(f"/api/{API_VERSION}/reset")
async def post_reset(request: Request):
    if not RP2040_DETECTED:
        abort(HTTPStatus.NOT_IMPLEMENTED, "Not implemented on non-RP2040 devices")

    def reset_device():
        import machine

        logger.info("Resetting device")
        flush_file_logs()
        machine.reset()

    reset_device()

    # TODO: schedule the reset to allow a 202 to be returned, instead of dropping the connection


@app.get(f"/api/{API_VERSION}/logs")
async def get_logs(request: Request):
    try:
        log_location = request.app.configuration[Configuration.LOG_FILE_LOCATION]
    except ConfigurationNotFoundError:
        abort(HTTPStatus.NOT_IMPLEMENTED, "Logs not being saved to file")
    flush_file_logs()

    if log_location.exists():
        return send_file(str(log_location), max_age=0, content_type=ContentType.TEXT)
    else:
        return "", HTTPStatus.OK, _create_content_type_header(ContentType.TEXT)


@app.delete(f"/api/{API_VERSION}/logs")
async def delete_logs(request: Request):
    try:
        request.app.configuration[Configuration.LOG_FILE_LOCATION]
    except ConfigurationNotFoundError:
        abort(HTTPStatus.NOT_IMPLEMENTED, "Logs not being saved to file")

    clear_logs()

    return "", HTTPStatus.OK, _create_content_type_header(ContentType.TEXT)


# FIXME: secure!
@app.post(f"/api/{API_VERSION}/shutdown")
async def post_shutdown(request):
    logger.info("Server shutting down")
    flush_file_logs()
    # TODO: delay shutdown to allow a 202 to be returned, instead of dropping the connection
    request.app.shutdown()
    return "Shutting down...", HTTPStatus.ACCEPTED


@app.get(f"/")
async def get_root(request: Request):
    return serve_ui(request, Path("index.html"))


# This route MUST be defined last
@app.get(f"/<re:.*:path>")
async def get_file(request: Request, path: str):
    return serve_ui(request, Path(path))


def serve_ui(request: Request, path: Path):
    # MicroPython `pathlib` implementation does not support `is_absolute`
    if str(path).startswith("/"):
        abort(HTTPStatus.NOT_FOUND, "Path should not start with double slash //")

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
        abort(HTTPStatus.NOT_FOUND)

    if (
        not str(full_path).startswith(str(frontend_location))
        or "../" in str(full_path)
        or not full_path.exists()
        or not full_path.is_file()
    ):
        abort(HTTPStatus.NOT_FOUND)

    content_type = _get_content_type(full_path)

    logger.info(f"Serving {full_path}")
    return send_file(str(full_path), max_age=0, content_type=content_type)


# mimetypes module does not exist for MicroPython
def _get_content_type(path: Path) -> str:
    try:
        return FILE_EXTENSION_TO_CONTENT_TYPE[path.suffix]
    except KeyError:
        return ContentType.OCTET_STREAM
