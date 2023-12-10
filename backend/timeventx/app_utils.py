from pathlib import Path
from typing import Callable, Optional

from microdot_asyncio import Request, Response

from timeventx.configuration import Configuration


class HttpStatus:
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    BAD_REQUEST = 400
    UNAUTHORISED = 401
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


_FILE_EXTENSION_TO_CONTENT_TYPE = {
    ".css": ContentType.CSS,
    ".html": ContentType.HTML,
    ".js": ContentType.JAVASCRIPT,
    ".json": ContentType.JSON,
    ".png": ContentType.PNG,
    ".svg": ContentType.SVG,
    ".txt": ContentType.TEXT,
    ".jpg": ContentType.JPG,
}

_BASIC_AUTH_HEADER = ("WWW-Authenticate", 'Basic realm="timeventx"')


# mimetypes module does not exist for MicroPython
def get_content_type(path: Path) -> str:
    try:
        return _FILE_EXTENSION_TO_CONTENT_TYPE[path.suffix]
    except KeyError:
        return ContentType.OCTET_STREAM


# TODO: consider decorator instead
def create_content_type_header(content_type: str) -> dict:
    return {"Content-Type": content_type}


def require_authorisation(func: Callable):
    def wrapped(request, *args, **kwargs):
        authorised, unauthorised_response = _handle_authorisation(request)
        print(authorised, unauthorised_response)
        if not authorised:
            return unauthorised_response
        return func(request, *args, **kwargs)

    return wrapped


def _handle_authorisation(request: Request) -> tuple[bool, Optional[Response]]:
    base64_encoded_credentials = request.app.configuration.get(Configuration.BASE64_ENCODED_CREDENTIALS)
    if base64_encoded_credentials is None:
        return True, None

    authorisation_header = request.headers.get("Authorization")
    if not authorisation_header:
        return False, Response("No credentials provided", HttpStatus.UNAUTHORISED, dict((_BASIC_AUTH_HEADER,)))

    client_base64_encoded_credentials = authorisation_header.split(" ")[1]
    if client_base64_encoded_credentials not in base64_encoded_credentials:
        return False, Response("Invalid credentials", HttpStatus.UNAUTHORISED, dict((_BASIC_AUTH_HEADER,)))

    return True, None
