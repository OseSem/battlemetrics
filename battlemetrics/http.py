from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from logging import getLogger
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    Any,
    ClassVar,
    Coroutine,
    Literal,
    TypeVar,
)

import aiohttp
import yarl

from .errors import BMException, Forbidden, HTTPException, NotFound, Unauthorized
from .note import Note
from .organization import Organization
from .server import Server
from .types.organization import OrganizationPlayerStats

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

    from aiohttp import BaseConnector, ClientResponse, ClientSession
    from yarl import URL

    from .types.note import NoteAttributes
    from .types.server import ServerSearch

    T = TypeVar("T")
    Response = Coroutine[Any, Any, T]

_log = getLogger(__name__)


SUCCESS_STATUS = [200, 201, 204]


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
        path: str | None = None,
        url: str | URL | None = None,
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
            self.endpoint = self.BASE + url if isinstance(url, str) else url.human_repr()

        self.method: str = method
        yurl = yarl.URL(self.endpoint)
        if parameters:
            yurl = yurl.update_query(**parameters)
        self.url: URL = yurl


class HTTPClient:
    """Represent an HTTP Client used for making requests to APIs."""

    def __init__(
        self,
        api_key: str,
        connector: BaseConnector | None = None,
        *,
        loop: AbstractEventLoop | None = None,
    ) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.connector = connector

        self.__session: ClientSession = None  # type: ignore[reportAttributeAccessIssue]

        self.api_key: str = api_key

        self.ensure_session()

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
        headers: dict[str, str] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> Any:  # noqa: ANN401
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

        _headers = {"Accept": "application/json"}

        if headers:
            _headers.update(**headers)

        # TODO: Add a check for the api key.
        if self.api_key:
            _headers["Authorization"] = f"Bearer {self.api_key}"

        async with self.__session.request(method, url, headers=_headers, **kwargs) as response:
            _log.debug("%s %s returned %s", method, path, response.status)

            # errors typically have text involved, so this should be safe 99.5% of the time.
            data = await json_or_text(response)

            await self.close()

            if response.status in SUCCESS_STATUS:
                return data

            if isinstance(data, dict):
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

        return Note(
            data=data.get("data"),
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
            existing_content: str = str(existing)
        else:
            fmt = "Note does not exist."
            raise ValueError(fmt)

        url = f"/players/{player_id}/relationships/notes/{note_id}"

        content: str = (
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
            data=result.get("data"),
            http=self,
        )

    async def get_server(self, server_id: int) -> Server:
        """Return information about a server.

        Parameters
        ----------
            server_id (int): The server ID

        Returns
        -------
            dict: The server information.
        """
        data = {
            "include": (
                "player,identifier,session,serverEvent,uptime:7,uptime:30,uptime:90,"
                "serverGroup,serverDescription,organization,orgDescription,orgGroupDescription"
            ),
        }

        request = await self.request(Route(method="GET", path=f"/servers/{server_id}"), params=data)
        return Server(
            request.get("data"),
            http=self,
        )

    async def search_server(
        self,
        search: ServerSearch,
    ) -> list[Server] | Server:
        """Search for a server.

        Parameters
        ----------
        search : ServerSearch
            The search parameters to use.
        """
        blueprints_uuid = "ce84a17d-a52b-11ee-a465-1798067d9f03"  # Boolean
        pve_uuid = "689d22c2-66f4-11ea-8764-e7fb71d2bf20"  # boolean
        kits_uuid = "ce84a17c-a52b-11ee-a465-1fcfab67c57a"  # Boolean

        mapsize_uuid = "689d22c3-66f4-11ea-8764-5723d5d7cfba"  # 1:9999999
        grouplimit_uuid = "ce84a17e-a52b-11ee-a465-a3c586d9e374"  # 1:255
        gatherrate_uuid = "ce84a17f-a52b-11ee-a465-33d2d6d4f5ea"  # 1:255

        data = {}
        data["page[size]"] = search.page_size
        data["include"] = "serverGroup"
        data["filter[rcon]"] = str(search.rcon).lower()
        data["sort"] = "rank" if search.sort_rank else "-rank"
        data["filter[search]"] = search.search
        data["filter[game]"] = search.game if search.game else "rust"
        data[f"filter[features][{grouplimit_uuid}]"] = (
            f"{search.group_size_min}:{search.group_size_max}"
        )
        data[f"filter[features][{mapsize_uuid}]"] = f"{search.map_size_min}:{search.map_size_max}"
        data[f"filter[features][{gatherrate_uuid}]"] = (
            f"{search.gather_rate_min}:{search.gather_rate_max}"
        )

        if search.countries:
            data["filter[countries][or][0]"] = search.countries
        if search.blacklist:
            data["filter[ids][blacklist]"] = search.blacklist
        if search.whitelist:
            data["filter[ids][whitelist]"] = search.whitelist
        if search.organization:
            data["filter[organizations]"] = search.organization
        if isinstance(search.pve, bool):
            data[f"filter[features][{pve_uuid}]"] = str(search.pve).lower()
        if isinstance(search.kits, bool):
            data[f"filter[features][{kits_uuid}]"] = str(search.kits).lower()
        if isinstance(search.blueprints, bool):
            data[f"filter[features][{blueprints_uuid}]"] = str(search.blueprints).lower()

        request = await self.request(
            Route(
                method="GET",
                path="/servers",
            ),
            params=data,
        )
        request = request.get("data")

        if len(request) == 0:
            fmt = "No servers found."
            raise ValueError(fmt)

        if len(request) > 1:
            return [
                Server(
                    data=x,
                    http=self,
                )
                for x in request
            ]

        return Server(
            data=request,
            http=self,
        )

    async def server_rank_history(
        self,
        server_id: int,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """Return the history of where your server is ranked."""
        if not start_time:
            now = datetime.now(tz=UTC)
            start_time = now - timedelta(days=0)
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not end_time:
            end_time = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {
            "start": (
                start_time
                if isinstance(start_time, str)
                else start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
            "stop": (
                end_time if isinstance(end_time, str) else end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
        }
        return await self.request(
            Route(
                method="GET",
                path=f"/servers/{server_id}/rank-history",
            ),
            params=data,
        )

    async def server_time_played_history(
        self,
        server_id: int,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """Return the servers time played history."""
        if not start_time:
            now = datetime.now(tz=UTC)
            start_time = now - timedelta(days=0)
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not end_time:
            end_time = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {
            "start": (
                start_time
                if isinstance(start_time, str)
                else start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
            "stop": (
                end_time if isinstance(end_time, str) else end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
        }
        return await self.request(
            Route(
                method="GET",
                path=f"/servers/{server_id}/time-played-history",
            ),
            params=data,
        )

    async def server_first_time_played_history(
        self,
        server_id: int,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """First Time Player History."""
        if not start_time:
            now = datetime.now(tz=UTC)
            start_time = now - timedelta(days=0)
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not end_time:
            end_time = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {
            "start": (
                start_time
                if isinstance(start_time, str)
                else start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
            "stop": (
                end_time if isinstance(end_time, str) else end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
        }
        return await self.request(
            Route(
                method="GET",
                path=f"/servers/{server_id}/first-time-history",
            ),
            params=data,
        )

    async def server_unique_players_history(
        self,
        server_id: int,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """Return the unique players history on a server."""
        if not start_time:
            now = datetime.now(tz=UTC)
            start_time = now - timedelta(days=0)
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not end_time:
            end_time = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {
            "start": (
                start_time
                if isinstance(start_time, str)
                else start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
            "stop": (
                end_time if isinstance(end_time, str) else end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
        }
        return await self.request(
            Route(
                method="GET",
                path=f"/servers/{server_id}/unique-player-history",
            ),
            params=data,
        )

    async def server_player_count_history(
        self,
        server_id: int,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
        resolution: str = "raw",
    ) -> dict[str, Any]:
        """Return the player count history.

        Parameters
        ----------
            server_id (int): The server ID
            start_time (str, optional): The UTC start time. Defaults to 1 day ago.
            end_time (str, optional): The UTC end time. Defaults to today/now.
            resolution (str, optional): One of: "raw" or "30" or "60" or "1440". Defaults to "raw"

        Returns
        -------
            dict: A datapoint of the player count history.
        """
        if not start_time:
            now = datetime.now(tz=UTC)
            start_time = now - timedelta(days=0)
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not end_time:
            end_time = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {
            "start": (
                start_time
                if isinstance(start_time, str)
                else start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
            "stop": (
                end_time if isinstance(end_time, str) else end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
            "resolution": resolution,
        }
        return await self.request(
            Route(
                method="GET",
                path=f"/servers/{server_id}/unique-player-history",
            ),
            params=data,
        )

    async def server_session_history(
        self,
        server_id: int,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """Return the session history of a server."""
        if not start_time:
            now = datetime.now(tz=UTC)
            start_time = now - timedelta(days=0)
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not end_time:
            end_time = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {
            "start": (
                start_time
                if isinstance(start_time, str)
                else start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
            "stop": (
                end_time if isinstance(end_time, str) else end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
            "include": "player",
        }
        return await self.request(
            Route(
                method="GET",
                path=f"/servers/{server_id}/relationships/sessions",
            ),
            params=data,
        )

    async def server_outage_history(
        self,
        server_id: int,
        uptime: str = "90",
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """Outage History.

        Outages are periods of time that the server did not respond to queries.
        Outage history stored and available for 89 days.
        """
        if not start_time:
            now = datetime.now(tz=UTC)
            start_time = now - timedelta(days=0)
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not end_time:
            end_time = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        start_time = (
            start_time if isinstance(start_time, str) else start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        end_time = (
            end_time if isinstance(end_time, str) else end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        data = {
            "page[size]": "90",
            "filter[range]": f"{start_time}:{end_time}",
            "include": f"uptime:{uptime}",
        }
        return await self.request(
            Route(method="GET", path=f"/servers/{server_id}/relationships/outages"),
            params=data,
        )

    async def server_downtime_history(
        self,
        server_id: int,
        resolution: str = "60",
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """Downtime History."""
        if not start_time:
            now = datetime.now(tz=UTC)
            start_time = now - timedelta(days=0)
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not end_time:
            end_time = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {
            "start": (
                start_time
                if isinstance(start_time, str)
                else start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
            "stop": (
                end_time if isinstance(end_time, str) else end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
            "resolution": resolution,
        }
        return await self.request(
            Route(
                method="GET",
                path=f"/servers/{server_id}/relationships/downtime",
            ),
            params=data,
        )

    async def server_force_update(self, server_id: int) -> dict[str, Any]:
        """Force Update will cause us to immediately queue the server to be queried and updated.

        This is limited to subscribers and users who belong to the organization
        that owns the server if it is claimed.

        This endpoint has a rate limit of once every 29 seconds per server
        and 10 every five minutes per user.
        """
        return await self.request(Route(method="POST", path=f"/servers/{server_id}/force-update"))

    async def send_chat(
        self,
        server_id: int,
        message: str,
        sender_name: str,
    ) -> dict[str, Any]:
        """Send a message on the server.

        Parameters
        ----------
            server_id (int): The server you want the command to run on.
            message (str): The message you wish to send
            sender_name (str): The name of the user that sends the message.

        Returns
        -------
            dict: If it was successful or not.
        """
        chat = {
            "data": {
                "type": "rconCommand",
                "attributes": {
                    "command": "rust:globalChat",
                    "options": {
                        "message": f"{sender_name}: {message}",
                    },
                },
            },
        }
        return await self.request(
            Route(method="POST", path=f"/servers/{server_id}/relationships/leaderboards/time"),
            json=chat,
        )

    async def console_command(
        self,
        server_id: int,
        command: str,
    ) -> dict[str, Any]:
        """Send a raw server console command.

        Parameters
        ----------
            server_id (int): The server you want the command to run on.
            command (str): The command you want to run.

        Returns
        -------
            dict: If it was successful or not.
        """
        data = {
            "data": {
                "type": "rconCommand",
                "attributes": {
                    "command": "raw",
                    "options": {
                        "raw": f"{command}",
                    },
                },
            },
        }
        return await self.request(
            Route(method="POST", path=f"/servers{server_id}/command"),
            json=data,
        )

    async def delete_rcon(self, server_id: int) -> dict[str, Any]:
        """Delete the RCON for your server.

        Parameters
        ----------
            server_id (int): The server ID.

        Returns
        -------
            dict: Response from the server.
        """
        return await self.request(Route(method="DELETE", path=f"/servers/{server_id}/rcon"))

    async def disconnect_rcon(self, server_id: int) -> dict[str, Any]:
        """Disconnect RCON from your server.

        Parameters
        ----------
            server_id (int): Server ID
        Returns:
            dict: Response from the server.
        """
        return await self.request(
            Route(method="DELETE", path=f"/servers/{server_id}/rcon/disconnect"),
        )

    async def connect_rcon(self, server_id: int) -> dict[str, Any]:
        """Connect RCON to your server.

        Parameters
        ----------
            server_id (int): Server ID

        Returns
        -------
            dict: Response from the server.
        """
        return await self.request(
            Route(method="DELETE", path=f"/servers/{server_id}/rcon/connect"),
        )

    async def server_info(self, server_id: int) -> dict[str, Any] | None:
        """Return information about a server.

        Parameters
        ----------
            server_id (int): The server ID

        Returns
        -------
            dict: The server information.
        """
        data = {
            "include": (
                "player,identifier,session,serverEvent,uptime:7,uptime:30,uptime:90,"
                "serverGroup,serverDescription,organization,orgDescription,orgGroupDescription"
            ),
        }
        return await self.request(Route(method="GET", path=f"/servers/{server_id}"), params=data)

    async def get_organization(self, organization_id: int) -> Organization:
        """Return information about an organization.

        Parameters
        ----------
            organization_id (int): The organization ID

        Returns
        -------
            dict: The organization information.
        """
        data = await self.request(Route(method="GET", path=f"/organizations/{organization_id}"))
        return Organization(data=data.get("data"), http=self)

    async def organization_player_stats(
        self,
        organization_id: int,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
        game: str | None = None,
    ) -> OrganizationPlayerStats:
        """Get a players stats for the organization.

        Parameters
        ----------
            organization_id (int): Organization ID
            start (str): UTC start time. Defaults to 7 days ago.
            end (str): UTC end time. Defaults to today.
            game (str, optional): Targeted game, example: rust. Defaults to None.

        Returns
        -------
            dict: Player stats for the organization.
        """
        if not start_time:
            now = datetime.now(tz=UTC)
            start_time = now - timedelta(days=0)
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not end_time:
            end_time = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        start = (
            start_time if isinstance(start_time, str) else start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        end = end_time if isinstance(end_time, str) else end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        data = {
            "filter[range]": f"{start}:{end}",
        }
        if game:
            data["filter[game]"] = game

        r = await self.request(
            Route(method="GET", path=f"/organizations/{organization_id}/stats/players"),
            params=data,
        )
        return OrganizationPlayerStats(**r.get("data").get("attributes"))

    async def organization_friends_list(
        self,
        organization_id: int,
        *,
        filter_name: str | None = None,
        filter_accepted: bool = True,
        filter_origin: bool = True,
        filter_reciprocated: bool = True,
    ) -> dict[str, Any]:
        """Get all the organization friends.

        Parameters
        ----------
            organization_id (str): Your organization ID
            filter_accepted (bool, optional): Whether they have accepted.
            filter_origin (bool, optional): True or False. Defaults to True.
            filter_name (str, optional): Name of a specific organization. Defaults to None.
            filter_reciprocated (bool, optional): True or False. Are the feelings mutual?

        Returns
        -------
            dict: Returns all the friendship information based on the paramaters set.
        """
        data = {
            "include": "organization",
            "filter[accepted]": str(filter_accepted).lower(),
            "filter[origin]": str(filter_origin).lower(),
            "filter[reciprocated]": str(filter_reciprocated).lower(),
        }
        if filter_name:
            data["filter[name]"] = filter_name

        return await self.request(
            Route(method="GET", path=f"/organizations/{organization_id}/relationships/friends"),
            params=data,
        )
