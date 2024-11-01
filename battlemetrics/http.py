from __future__ import annotations

import asyncio
from logging import getLogger
from typing import TYPE_CHECKING, Any, ClassVar, Literal

import aiohttp
import yarl

from battlemetrics.errors import (
    BMException,
    Forbidden,
    HTTPException,
    NotFound,
    Unauthorized,
)

from . import utils
from .note import Note
from .types.note import Note as NotePayload
from .types.note import NoteAttributes, NoteRelationships

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

_log = getLogger(__name__)

SUCCESS_STATUS = [200, 201, 204]


async def json_or_text(
    response: aiohttp.ClientResponse,
) -> dict[str, Any] | list[dict[str, Any]] | str:
    """
    Process an `aiohttp.ClientResponse` to return either a JSON object or raw text.

    This function attempts to parse the response as JSON. If the content type of the response is not
    application/json or parsing fails, it falls back to returning the raw text of the response.

    Parameters
    ----------
    response : aiohttp.ClientResponse
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
    url : str
        The URL for the route.
    parameters : int | str | bool
        Optional parameters for the route.
    """

    BASE: ClassVar[str] = "https://api.battlemetrics.com"

    def __init__(
        self,
        method: METHODS,
        path: str | None = None,
        url: str | None = None,
        **parameters: int | str | bool,
    ) -> None:
        if not path and not url:
            msg = "Either path or url must be provided."
            raise ValueError(msg)
        if path and url:
            msg = "Only one of path or url can be provided."
            raise ValueError(msg)

        if path:
            self.endpoint = self.BASE + path
        elif url:
            self.endpoint = self.BASE + url

        self.method: str = method
        yurl = yarl.URL(self.endpoint)
        if parameters:
            yurl = yurl.update_query(**parameters)
        self.url: str = yurl.human_repr()


class HTTPClient:
    """Represent an HTTP Client used for making requests to APIs."""

    def __init__(
        self,
        api_key: str,
        connector: aiohttp.BaseConnector | None = None,
        *,
        loop: AbstractEventLoop | None = None,
    ) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.connector = connector

        self.__session: aiohttp.ClientSession = None  # type: ignore[reportAttributeAccessIssue]

        self.api_key: str = api_key

        self.ensure_session()

    def ensure_session(self) -> None:
        """
        Ensure that an :class:`aiohttp.ClientSession` is created and open.

        If a session does not exist, this method creates a new :class:`aiohttp.ClientSession`
        using the provided connector and loop.
        """
        if not self.__session or self.__session.closed:
            self.__session = aiohttp.ClientSession(connector=self.connector, loop=self.loop)

    async def close(self) -> None:
        """Close the :class:`aiohttp.ClientSession` if it exists and is open."""
        if self.__session:
            await self.__session.close()

    async def request(
        self,
        route: Route,
        headers: dict[str, str] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> dict[str, Any] | list[dict[str, Any]] | str:
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
        errors.HTTPException
            Will raise if the request fails or the response indicates an error.
        """
        self.ensure_session()

        method = route.method
        url = route.url

        _headers = {"Accept": "application/json"}

        if headers:
            _headers.update(**headers)

        # TODO: Add a check for the api key.
        if self.api_key:
            _headers["Authorization"] = f"Bearer {self.api_key}"

        async with self.__session.request(method, url, headers=_headers, **kwargs) as response:
            _log.debug(f"{method} {url} returned {response.status}")

            # errors typically have text involved, so this should be safe 99.5% of the time.
            data = await json_or_text(response)
            _log.debug(f"{method} {url} has received {data}")

            await self.close()

            if response.status in SUCCESS_STATUS:
                return data

            if isinstance(data, dict):
                if response.status == 401:
                    raise Unauthorized(response, data)
                if response.status == 403:
                    raise Forbidden(response, data)
                if response.status == 404:
                    raise NotFound(response, data)
                if response.status == 429:
                    _log.debug("Being ratelimited..")

                raise HTTPException(response, data)

            raise BMException

    async def get_note(self, player_id: int, note_id: int) -> Note:
        """Return a note based on player ID and note ID.

        Parameters
        ----------
        player_id : int
            The ID of the player.
        note_id : int
            The ID of the note.
        """
        url = f"/players/{player_id}/relationships/notes/{note_id}"
        data = await self.request(
            Route(
                method="GET",
                path=url,
            ),
        )
        if isinstance(data, dict):
            data = data.get("data")

        return Note(
            data=NotePayload(
                id=data.get("id"),  # type: ignore[reportAttributeAccessIssue]
                type=data.get("type"),  # type: ignore[reportAttributeAccessIssue]
                attributes=NoteAttributes(
                    **data.get("attributes", {}),  # type: ignore[reportAttributeAccessIssue]
                ),
                relationships=NoteRelationships(
                    **utils.format_relationships(data.get("relationships", {})),  # type: ignore[reportAttributeAccessIssue]
                ),
            ),
            http=self,
        )

    async def delete_note(self, player_id: int, note_id: int) -> None:
        """Delete an existing note.

        Parameters
        ----------
            player_id (int): The battlemetrics ID of the player the note is attached to.
            note_id (int): The note's ID

        Returns
        -------
            dict: Response from server.
        """
        url = f"/players/{player_id}/relationships/notes/{note_id}"
        await self.request(
            Route(
                method="DELETE",
                path=url,
            ),
        )

    # TODO: (PLR0913): Add attributes instead of a variable for each parameter.
    async def update_note(
        self,
        player_id: int,
        note_id: int,
        attributes: NoteAttributes,
        *,
        append: bool | None = False,
    ) -> Note:
        """Update an existing note.

        Parameters
        ----------
            player_id (int): The battlemetrics ID of the user.
            note_id (int): The ID of the note.
            content (str): The new content of the note.
            clearancelevel (int): The new clearance level of the note.
            shared (bool): Whether this note should be shared.
            append (bool): Whether to append the new content to the existing note.

        Returns
        -------
            dict: Response from server.
        """
        if existing := await self.get_note(player_id=player_id, note_id=note_id):
            existing_content = existing.content
        else:
            msg = "Note does not exist."
            raise ValueError(msg)

        url = f"/players/{player_id}/relationships/notes/{note_id}"

        content = (
            f"{existing_content}\n{attributes.get("note")}" if append else attributes.get("note")
        )

        data = {
            "data": {
                "type": "playerNote",
                "id": "example",
                "attributes": {
                    "clearanceLevel": f"{attributes.get("clearanceLevel")}",
                    "note": f"{content}",
                    "shared": f"{str(attributes.get("shared")).lower()}",
                },
            },
        }

        result = await self.request(
            Route(
                method="PATCH",
                path=url,
            ),
            json_dict=data,
        )
        return Note(
            data=NotePayload(
                id=result.get("id"),  # type: ignore[reportAttributeAccessIssue]
                type=result.get("type"),  # type: ignore[reportAttributeAccessIssue]
                attributes=result.get("attributes"),  # type: ignore[reportAttributeAccessIssue]
                relationships=NoteRelationships(
                    *utils.format_relationships(result.get("relationships")),  # type: ignore[reportAttributeAccessIssue]
                ),
            ),
            http=self,
        )
