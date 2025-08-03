from __future__ import annotations

import asyncio
import uuid
from logging import getLogger
from typing import TYPE_CHECKING, Any, ClassVar, Literal

import aiohttp
import yarl

from .errors import BMException, Forbidden, HTTPException, NotFound, Unauthorized

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from types import TracebackType

    from aiohttp import BaseConnector, ClientResponse, ClientSession
    from yarl import URL


_log = getLogger(__name__)


IDENTIFIERS = Literal[
    "steamID",
    "BEGUID",
    "legacyBEGUID",
    "ip",
    "name",
    "survivorName",
    "steamFamilyShareOwner",
    "conanCharName",
    "egsID",
    "funcomID",
    "playFabID",
    "mcUUID",
    "7dtdEOS",
    "battlebitHWID",
]


async def json_or_text(
    response: ClientResponse,
) -> dict[str, Any] | list[dict[str, Any]] | str:
    """
    Process a `ClientResponse` to return either a JSON object or raw text.

    This function attempts to parse the response as JSON. If the content type of the response is not
    application/json or parsing fails, it falls back to returning the raw text of the response.

    Parameters
    ----------
    response : ClientResponse
        The response object to process.

    Returns
    -------
    dict[str, t.Any] | list[dict[str, t.Any]] | str
        The parsed JSON object as a dictionary or list of dictionaries, or the raw response text.
    """
    try:
        if "application/json" in response.headers["content-type"].lower():
            return await response.json()
    except KeyError:
        # Thanks Cloudflare
        pass

    return await response.text(encoding="utf-8")


METHODS = Literal[
    "GET",
    "HEAD",
    "OPTIONS",
    "TRACE",
    "PUT",
    "DELETE",
    "POST",
    "PATCH",
    "CONNECT",
]


class Route:
    """Represents a route for the BattleMetrics API.

    This method requires either one of path or url.

    Parameters
    ----------
    method : str
        The HTTP method for the route.
    path : str
        The path for the route.
    url : str | URL
        The URL for the route.
    parameters : int | str | bool
        Optional parameters for the route.
    """

    BASE: ClassVar[str] = "https://api.battlemetrics.com"

    def __init__(
        self,
        method: METHODS,
        path: str,
        **parameters: int | str | bool,
    ) -> None:
        self.method: str = method
        url = path if path.startswith(("http://", "https://")) else f"{self.BASE}{path}"
        self.url: URL = yarl.URL(url).update_query(**parameters) if parameters else yarl.URL(url)


class HTTPClient:
    """Represent an HTTP Client used for making requests to APIs."""

    def __init__(
        self,
        api_key: str,
        *,
        connector: BaseConnector | None = None,
        loop: AbstractEventLoop | None = None,
        proxy: str | None = None,
        proxy_auth: aiohttp.BasicAuth | None = None,
    ) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.connector = connector
        self.proxy = proxy
        self.proxy_auth = proxy_auth

        self.__session: ClientSession = None  # type: ignore[reportAttributeAccessIssue]

        self.api_key: str = api_key

        self.ensure_session()

    def __aexit__(
        self,
        exc_type: BaseException | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the HTTP client when exiting."""
        return self.close()

    def ensure_session(self) -> None:
        """
        Ensure that an :class:`ClientSession` is created and open.

        If a session does not exist, this method creates a new :class:`ClientSession`
        using the provided connector and loop.
        """
        if not self.__session or self.__session.closed:
            self.__session = aiohttp.ClientSession(connector=self.connector, loop=self.loop)

    async def close(self) -> None:
        """Close the :class:`ClientSession` if it exists and is open."""
        if self.__session:
            await self.__session.close()

    async def request(
        self,
        route: Route,
        *,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Send a request to the specified route and returns the response.

        This method constructs and sends an HTTP request based on the specified route and headers.
        It processes the response to return JSON data or raw text, handling errors as needed.

        Parameters
        ----------
        route : Route
            The route object containing the method and URL for the request.
        headers : dict[str, str] | None, optional
            Optional headers to include with the request. Defaults to None.

        Returns
        -------
        dict[str, t.Any] | list[dict[str, t.Any]] | str
            The response data as a parsed JSON object or list, or raw text if JSON parsing is
            not applicable.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
            Might raise a more specific exception if the response status code is known.
        """
        self.ensure_session()

        method = route.method
        url = route.url
        path = route.url.path

        headers = {
            "Accept": "application/json",
            **(headers or {}),
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if "json" in kwargs:
            headers["Content-Type"] = "application/json"

        kwargs["headers"] = headers

        if self.proxy:
            kwargs["proxy"] = self.proxy
        if self.proxy_auth:
            kwargs["proxy_auth"] = self.proxy_auth

        async with self.__session.request(method, url, **kwargs) as response:
            _log.debug("%s %s returned %s", method, path, response.status)

            # errors typically have text involved, so this should be safe 99.5% of the time.
            data = await json_or_text(response)

            await self.close()

            if 200 <= response.status < 300:
                return data

            if isinstance(data, dict):
                print(data)
                if response.status == 401:
                    _log.warning(
                        "Path %s returned 401, your API key may be invalid.",
                        path,
                    )
                    raise Unauthorized(response, data)
                if response.status == 403:
                    _log.warning(
                        "Path %s returned 403, check whether you have valid permissions.",
                        path,
                    )
                    raise Forbidden(response, data)
                if response.status == 404:
                    _log.warning(
                        "Path %s returned 404, check whether the path is correct.",
                        path,
                    )
                    raise NotFound(response, data)
                if response.status == 429:
                    _log.warning(
                        "We're being rate limited. You are limited to %s requests per minute.",
                        response.headers.get("X-Rate-Limit-Limit"),
                    )

                raise HTTPException(response, data)

            raise BMException

    # HTTP Requests

    async def create_ban(
        self,
        player_id: int,
        *,
        reason: str,
        note: str | None,
        banlist_id: str,
        organization_id: int,
        server_id: int,
        org_wide: bool = True,
        auto_add_enabled: bool = True,
        native_enabled: bool = True,
        expires: str | None = None,
    ) -> Any:
        """
        Create a ban with all required and optional parameters.

        Parameters match the BattleMetrics API documentation.
        """
        data: dict[str, Any] = {
            "data": {
                "type": "ban",
                "attributes": {
                    "uid": str(uuid.uuid4())[:14],
                    "reason": reason,
                    "note": note,
                    "expires": expires,
                    "identifiers": [],  # TODO: Add identifiers after get_player is implemented
                    "orgWide": org_wide,
                    "autoAddEnabled": auto_add_enabled,
                    "nativeEnabled": native_enabled,
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}",
                        },
                    },
                    "server": {
                        "data": {
                            "type": "server",
                            "id": f"{server_id}",
                        },
                    },
                    "player": {
                        "data": {
                            "type": "player",
                            "id": f"{player_id}",
                        },
                    },
                    "banList": {
                        "data": {
                            "type": "banList",
                            "id": f"{banlist_id}",
                        },
                    },
                },
            },
        }

        route = Route(
            method="POST",
            path="/bans",
        )
        return await self.request(route, json=data)
