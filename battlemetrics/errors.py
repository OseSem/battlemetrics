from typing import Any

from aiohttp import ClientResponse

__all__ = (
    "BMConnectionError",
    "BMException",
    "BMTimeoutError",
    "BadRequest",
    "Forbidden",
    "HTTPException",
    "NotFound",
    "RateLimited",
    "ServerError",
    "Unauthorized",
)


class BMException(Exception):
    """Base exception class for all BattleMetrics errors."""


class BMConnectionError(BMException):
    """Raised when a network/connection error occurs reaching the API."""


class BMTimeoutError(BMException):
    """Raised when a request times out."""


class HTTPException(BMException):
    """Exception that's raised when an HTTP request operation fails.

    Attributes
    ----------
    response: :class:`aiohttp.ClientResponse`
        The response of the failed HTTP request.
    text: :class:`str`
        The error message text. May be empty if the body wasn't parseable.
    status: :class:`int`
        The status code of the HTTP request.
    code: :class:`int`
        The BattleMetrics-reported status code from the JSON:API error object,
        or 0 if the body did not contain one.
    title: :class:`str`
        The short error title from the JSON:API error object.
    """

    def __init__(
        self,
        response: ClientResponse,
        message: str | dict[str, Any] | list[Any] | None,
    ) -> None:
        self.response: ClientResponse = response
        self.status: int = response.status
        self.code: int = 0
        self.text: str = ""
        self.title: str = ""
        if isinstance(message, dict):
            errors_list: list[dict[str, Any]] = message.get("errors") or []
            error: dict[str, Any] = errors_list[0] if errors_list else {}
            status_raw = str(error.get("status", ""))
            self.code = int(status_raw) if status_raw.isdigit() else 0
            self.text = error.get("detail", "") or error.get("title", "")
            self.title = error.get("title", "")
        else:
            self.text = str(message) if message else ""

        fmt = "{0.status} {0.reason}"
        if self.text:
            fmt += ": {1}"

        super().__init__(fmt.format(self.response, self.text))


class BadRequest(HTTPException):
    """Raised when status code 400 occurs."""


class Unauthorized(HTTPException):
    """Raised when status code 401 occurs."""


class Forbidden(HTTPException):
    """Raised when status code 403 occurs."""


class NotFound(HTTPException):
    """Raised when status code 404 occurs."""


class RateLimited(HTTPException):
    """Raised when status code 429 occurs.

    Attributes
    ----------
    retry_after: :class:`float` | None
        The number of seconds to wait before retrying, parsed from the
        ``Retry-After`` response header. ``None`` if the server did not
        provide one.
    """

    def __init__(
        self,
        response: ClientResponse,
        message: str | dict[str, Any] | list[Any] | None,
    ) -> None:
        super().__init__(response, message)
        retry_after = response.headers.get("Retry-After")
        self.retry_after: float | None = (
            float(retry_after)
            if retry_after and retry_after.replace(".", "", 1).isdigit()
            else None
        )


class ServerError(HTTPException):
    """Raised when a 5xx status code occurs."""
