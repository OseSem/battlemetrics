from typing import Any

from aiohttp import ClientResponse

__all__ = ("BMException", "HTTPException", "Unauthorized", "Forbidden", "NotFound")


class BMException(Exception):
    """Base exception class for all BattleMetrics errors."""


class HTTPException(BMException):
    """Exception that's raised when an HTTP request operation fails.

    Attributes
    ----------
    response: :class:`aiohttp.ClientResponse`
        The response of the failed HTTP request. This is an
        instance of :class:`aiohttp.ClientResponse`. In some cases
        this could also be a :class:`requests.Response`.

    text: :class:`str`
        The text of the error. Could be an empty string.
    status: :class:`int`
        The status code of the HTTP request.
    code: :class:`int`
        The Discord specific error code for the failure.
    """

    def __init__(self, response: ClientResponse, message: str | dict[str, Any] | None) -> None:
        self.response: ClientResponse = response
        self.status: int = response.status  # type: ignore[reportAccessAttributeIssue]
        self.code: int
        self.text: str
        if isinstance(message, dict):
            self.code = message.get("code", 0)
            self.text = message.get("message", "")
        else:
            self.text = message or ""
            self.code = 0

        fmt = "{0.status} {0.reason} (error code: {1})"
        if len(self.text):
            fmt += ": {2}"

        super().__init__(fmt.format(self.response, self.code, self.text))


class Unauthorized(HTTPException):
    """Exception that's raised for when status code 401 occurs."""


class Forbidden(HTTPException):
    """Exception that's raised for when status code 403 occurs."""


class NotFound(HTTPException):
    """Exception that's raised for when status code 404 occurs."""
