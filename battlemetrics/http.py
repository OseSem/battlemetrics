from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from logging import getLogger
from typing import TYPE_CHECKING, Any, ClassVar, Literal

import aiohttp
import yarl

from . import utils
from .banlist import BanList
from .errors import BMException, Forbidden, HTTPException, NotFound, Unauthorized
from .flag import Flag
from .note import Note
from .organization import Organization
from .player import Player
from .server import Server
from .session import Session
from .types.banlist import BanListExemption, BanListInvite
from .types.organization import OrganizationPlayerStats

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

    from aiohttp import BaseConnector, ClientResponse, ClientSession
    from yarl import URL

    from .types.note import NoteAttributes


_log = getLogger(__name__)


SUCCESS_STATUS = [200, 201, 204]
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
            f'{existing_content}\n{attributes.get("note")}' if append else attributes.get("note")
        )

        data = {
            "data": {
                "type": "playerNote",
                "id": "example",
                "attributes": {
                    "clearanceLevel": f'{attributes.get("clearanceLevel")}',
                    "note": f"{content}",
                    "shared": f'{str(attributes.get("shared")).lower()}',
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
        search: str | None = None,
        *,
        countries: list[str] | None = None,  # TODO: Add countries type
        game: str | None = None,
        blacklist: list[str] | None = None,
        whitelist: list[str] | None = None,
        organization: str | None = None,
        gather_rate_min: int = 1,
        gather_rate_max: int = 20,
        group_size_min: int | None = 1,
        group_size_max: int | None = 16,
        map_size_min: int | None = 1,
        map_size_max: int | None = 6000,
        blueprints: bool | Literal["both"] = "both",
        pve: bool | Literal["both"] = "both",
        kits: bool | Literal["both"] = "both",
        status: Literal["offline", "online", "dead", "invalid", "unknown"] = "online",
        page_size: int = 100,
        sort_rank: bool = True,
        rcon: bool = True,
    ) -> list[Server] | Server:
        """Search for a server.

        Parameters
        ----------
        search (str, optional): The search query. Defaults to None.
        countries (list[str], optional): The countries to search for. Defaults to None.
        game (str, optional): The game to search for. Defaults to None.
        blacklist (list[str], optional): The blacklist to search for. Defaults to None.
        whitelist (list[str], optional): The whitelist to search for. Defaults to None.
        organization (str, optional): The organization to search for. Defaults to None.
        gather_rate_min (int, optional): The minimum gather rate. Defaults to 1.
        gather_rate_max (int, optional): The maximum gather rate. Defaults to 20.
        group_size_min (int, optional): The minimum group size. Defaults to 1.
        group_size_max (int, optional): The maximum group size. Defaults to 16.
        map_size_min (int, optional): The minimum map size. Defaults to 1.
        map_size_max (int, optional): The maximum map size. Defaults to 6000.
        blueprints (bool, optional): Whether blueprints are enabled. Defaults to "both".
        pve (bool, optional): Whether PVE is enabled. Defaults to "both".
        kits (bool, optional): Whether kits are enabled. Defaults to "both".
        status (str, optional): The status of the server. Defaults to "online".
        page_size (int, optional): The page size. Defaults to 100.
        sort_rank (bool, optional): Whether to sort by rank. Defaults to True.
        rcon (bool, optional): Whether RCON is enabled. Defaults to True.
        """
        blueprints_uuid = "ce84a17d-a52b-11ee-a465-1798067d9f03"  # Boolean
        pve_uuid = "689d22c2-66f4-11ea-8764-e7fb71d2bf20"  # boolean
        kits_uuid = "ce84a17c-a52b-11ee-a465-1fcfab67c57a"  # Boolean

        mapsize_uuid = "689d22c3-66f4-11ea-8764-5723d5d7cfba"  # 1:9999999
        grouplimit_uuid = "ce84a17e-a52b-11ee-a465-a3c586d9e374"  # 1:255
        gatherrate_uuid = "ce84a17f-a52b-11ee-a465-33d2d6d4f5ea"  # 1:255

        data = {}
        data["page[size]"] = page_size
        data["include"] = "serverGroup"
        data["filter[rcon]"] = str(rcon).lower()
        data["sort"] = "rank" if sort_rank else "-rank"
        data["filter[search]"] = search
        data["filter[game]"] = game if game else "rust"
        data["filter[status]"] = status
        data[f"filter[features][{grouplimit_uuid}]"] = f"{group_size_min}:{group_size_max}"
        data[f"filter[features][{mapsize_uuid}]"] = f"{map_size_min}:{map_size_max}"
        data[f"filter[features][{gatherrate_uuid}]"] = f"{gather_rate_min}:{gather_rate_max}"

        if countries:
            data["filter[countries][or][0]"] = countries
        if blacklist:
            data["filter[ids][blacklist]"] = blacklist
        if whitelist:
            data["filter[ids][whitelist]"] = whitelist
        if organization:
            data["filter[organizations]"] = organization
        if isinstance(pve, bool):
            data[f"filter[features][{pve_uuid}]"] = str(pve).lower()
        if isinstance(kits, bool):
            data[f"filter[features][{kits_uuid}]"] = str(kits).lower()
        if isinstance(blueprints, bool):
            data[f"filter[features][{blueprints_uuid}]"] = str(blueprints).lower()

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

    async def match_identifiers(
        self,
        identifier: str | int,
        identifier_type: IDENTIFIERS | None = None,
    ) -> dict[str, Any]:
        """Search for one or more identifiers.

        This API method is only available to authenticated users.

        It is rate limited to one request a second.

        Parameters
        ----------
            identifier (str): The specific identifier.
            type (str, optional): The type of identifier you provided.

        Returns
        -------
            dict: Dictionary response of any matches.
        """
        data = {
            "data": [
                {
                    "type": "identifier",
                    "attributes": {
                        "type": identifier_type,
                        "identifier": f"{identifier}",
                    },
                },
            ],
        }
        params = {"include": "player,server,identifier,playerFlag,flagPlayer"}
        return await self.request(
            Route(method="POST", path="/players/match"),
            json=data,
            params=params,
        )

    async def quick_match(
        self,
        identifier: str,
        identifier_type: IDENTIFIERS | None = None,
    ) -> dict[str, Any]:
        """Player Quick Match Identifiers.

        Searches for one or more identifiers.
        This API method is only available to authenticated users.
        It is also rate limited to 10 requests per second.
        Enterprise users have a higher rate limit of 30 requests per second.
        The servers filter limits which servers you get when including server information
        it does not filter players by server.

        Results will be returned sorted by the player's id.

        Parameters
        ----------
            identifier (str): The specific identifier.
            type (str, optional): The type of identifier you provided.

        Returns
        -------
            dict: Dictionary response of any matches.
        """
        data = {
            "data": [
                {
                    "type": "identifier",
                    "attributes": {
                        "type": identifier_type,
                        "identifier": f"{identifier}",
                    },
                },
            ],
        }
        return await self.request(
            Route(method="POST", path="/players/quick-match"),
            json=data,
        )

    async def player_identifiers(self, player_id: int) -> dict[str, Any]:
        """Get player identifiers and related players and identifiers.

        Parameters
        ----------
            player_id (int): The player battlemetrics Identifier.

        Returns
        -------
            dict: Players related identifiers.
        """
        data = {
            "include": "player,identifier",
            "page[size]": "100",
        }
        return await self.request(
            Route(method="GET", path=f"/players/{player_id}/relationships/related-identifiers"),
            params=data,
        )

    async def search_player(
        self,
        search: str | None = None,
        *,
        filter_game: str | None = None,
        filter_servers: int | None = None,
        filter_organization: int | None = None,
        filter_online: bool = False,
        filter_public: bool = False,
        flag: str | None = None,
    ) -> Player:
        """Grab a list of players based on the filters provided.

        Parameters
        ----------
            search (str, optional): Search for specific player. Defaults to None.
            filter_online (bool, optional): Online or offline players. Defaults to True.
            filter_servers (int, optional): Server IDs, comma separated. Defaults to None.
            filter_organization (int, optional): Organization ID. Defaults to None.
            filter_public (bool, optional): Public or private results? (RCON or Not).
            filter_game (str, optional): Filters the results to specific game.

        Returns
        -------
            dict: A dictionary response of all the players.
        """
        data = {
            "page[size]": "100",
            "include": "server,identifier,playerFlag,flagPlayer",
        }
        if search:
            data["filter[search]"] = search
        if filter_servers:
            data["filter[server]"] = str(filter_servers)
        if filter_organization:
            data["filter[organization]"] = str(filter_organization)
        if flag:
            data["filter[playerFlags]"] = flag
        if filter_game:
            data["filter[server][game]"] = filter_game.lower()

        data["filter[online]"] = "true" if filter_online else "false"
        data["filter[public]"] = "true" if filter_public else "false"

        r = await self.request(Route(method="GET", path="/players"), params=data)
        return Player(r.get("data"), http=self)

    async def get_player(self, player_id: int) -> Player:
        """Retrieve the battlemetrics player information.

        Parameters
        ----------
            identifier (int): The Battlemetrics ID of the targeted player.

        Returns
        -------
            dict: Returns everything you can view in a DICT form.

        """
        data = {
            "include": "identifier,server,playerCounter,playerFlag,flagPlayer",
        }
        r = await self.request(Route(method="GET", path=f"/players/{player_id}"), params=data)
        return Player(r.get("data"), http=self)

    async def play_history(
        self,
        player_id: int,
        server_id: int,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """Return the data we use for rendering time played history charts.

        Start and stop are truncated to the date.

        Parameters
        ----------
            player_id (int): The battlemetrics player ID.
            server_id (int): The server ID
            start_time (str): The UTC start. defaults to 5 days ago.
            end_time (str): The UTC end. Defaults to now.

        Returns
        -------
            dict: Dictionary of Datapoints.
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
        }
        return await self.request(
            Route(method="GET", path=f"/players/{player_id}/time-played-history/{server_id}"),
            params=data,
        )

    async def player_server_info(self, player_id: int, server_id: int) -> dict[str, Any]:
        """Return server specifics for the given player and server.

        Parameters
        ----------
            player_id (int): The battlemetrics player ID.
            server_id (int): The server ID
        Returns:
            dict: Response from the server showing the player server info.
        """
        return await self.request(
            Route(method="GET", path=f"/players/{player_id}/servers/{server_id}"),
        )

    async def player_session_history(
        self,
        player_id: int,
        *,
        filter_server: str | None = None,
        filter_organization: str | None = None,
    ) -> dict[str, Any]:
        """Return player's session history.

        Parameters
        ----------
            player_id (int): The battlemetrics player id
            filter_server (str, optional): The specific server ID. Defaults to None.
            filter_organization (str, optional): The specific organization ID. Defaults to None.

        Returns
        -------
            dict: Returns a players session history.
        """
        data = {
            "include": "identifier,server",
            "page[size]": "100",
        }
        if filter_server:
            data["filter[servers]"] = filter_server
        if filter_organization:
            data["filter[organizations]"] = filter_organization

        return await self.request(
            Route(method="GET", path=f"/players/{player_id}/relationships/sessions"),
            params=data,
        )

    async def player_flags(self, player_id: int) -> list[Flag]:
        """Return all the flags on a players profile.

        Parameters
        ----------
            player_id (int): Battlemetrics ID of the targeted player.

        Returns
        -------
            dict: The profile with all the flags.
        """
        data = {
            "page[size]": "100",
            "include": "playerFlag",
        }

        r = await self.request(
            Route(method="GET", path=f"/players/{player_id}/relationships/flags"),
            params=data,
        )
        return [Flag(data=flag, http=self) for flag in r.get("included")]

    async def add_flag(self, player_id: int, flag_id: str | None = None) -> dict[str, Any]:
        """Create or add a flag to the targeted players profile.

        Parameters
        ----------
            player_id (int): Battlemetrics ID of the player.
            flag_id (str, optional): An existing flag ID. Defaults to None.

        Returns
        -------
            dict: Player profile relating to the new flag.
        """
        data = {
            "data": [
                {
                    "type": "playerFlag",
                },
            ],
        }
        if flag_id:
            data["data"][0]["id"] = flag_id

        return await self.request(
            Route(method="POST", path=f"/players/{player_id}/relationships/flags"),
            json_dict=data,
        )

    async def remove_flag(self, player_id: int, flag_id: str) -> None:
        """Delete a targeted flag from a targeted player ID.

        Parameters
        ----------
            player_id (int): Battlemetrics ID of the player.
            flag_id (str): The ID of the flag to remove.

        Returns
        -------
            dict: If you were successful or not.
        """
        await self.request(
            Route(method="DELETE", path=f"/players/{player_id}/relationships/flags/{flag_id}"),
        )

    async def player_coplay_info(
        self,
        player_id: int,
        *,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
        player_names: str | None = None,
        organization_names: str | None = None,
        server_names: str | None = None,
    ) -> dict[str, Any]:
        """Get the coplay data related to the targeted player.

        Parameters
        ----------
            player_id (int): The BATTLEMETRICS id of the targeted player
            time_start (str): UTC time start. Defaults to 7 days ago
            time_end (str): UTC time ends. Defaults to day.
            player_names (str, optional): Player names to target. Defaults to None.
            organization_names (str, optional): Specific Organizations. Defaults to None.
            server_names (str, optional): Specific servers. Defaults to None.

        Returns
        -------
            dict: A dictionary response of all the coplay users.
        """
        if not start_time:
            now = datetime.now(tz=UTC)
            start_time = now - timedelta(days=0)
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not end_time:
            end_time = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        data = {
            "filter[period]": f"{start_time}:{end_time}",
            "page[size]": "100",
            "fields[coplayrelation]": "name,duration",
        }
        if player_names:
            data["filter[players]"] = player_names
        if organization_names:
            data["filter[organizations]"] = organization_names
        if server_names:
            data["filter[servers]"] = server_names

        return await self.request(
            Route(method="GET", path=f"/players/{player_id}/relationships/coplay"),
            params=data,
        )

    async def add_ban(
        self,
        reason: str,
        note: str,
        org_id: str,
        banlist: str,
        server_id: str,
        battlemetrics_id: int | None = None,
        steam_id: int | None = None,
        expires: str | None = None,
        *,
        orgwide: bool = True,
    ) -> dict[str, Any]:
        """Create a ban for the targeted user.

        One of battlemetrics_id or steam_id is required to ban the user.
        By default, the ban is set to organization wide.

        Parameters
        ----------
            reason (str): Reason for the ban (This is what the user/server sees)
            note (str): Note attached to the ban (Admins/staff can see this)
            org_id (str): Organization ID the ban is associated to.
            banlist (str): Banlist the ban is associated to.
            server_id (str): Server ID the ban is associated to.
            expires (str, optional): _description_. Defaults to "permanent".
            orgwide (bool, optional): _description_. Defaults to True.
            battlemetrics_id (int, optional): Battlemetrics ID of the banned user.
            steam_id (int, optional): Steam ID of the banned user.

        Returns
        -------
            dict: The results, whether it was successful or not.
        """
        if expires:
            expires = await utils.calculate_future_date(expires)

        data: dict[str, Any] = {
            "data": {
                "type": "ban",
                "attributes": {
                    "uid": str(uuid.uuid4())[:14],
                    "reason": reason,
                    "note": note,
                    "expires": expires,
                    "identifiers": [],
                    "orgWide": orgwide,
                    "autoAddEnabled": True,
                    "nativeEnabled": None,
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{org_id}",
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
                            "id": f"{battlemetrics_id}",
                        },
                    },
                    "banList": {
                        "data": {
                            "type": "banList",
                            "id": f"{banlist}",
                        },
                    },
                },
            },
        }
        # Grab the complete profile
        if not steam_id and not battlemetrics_id:
            fmt = "Submit either a Steam ID or BattleMetrics ID."
            raise ValueError(fmt)
        if steam_id and battlemetrics_id:
            fmt = "Submit either a Steam ID or BattleMetrics ID, not both."
            raise ValueError(fmt)

        if steam_id:
            player_data = await self.match_identifiers(
                identifier=steam_id,
                identifier_type="steamID",
            )
            battlemetrics_id = player_data["data"][0]["relationships"]["player"]["data"]["id"]

        player_info = (
            await self.get_player(player_id=battlemetrics_id)
            if isinstance(battlemetrics_id, int)
            else None
        )

        # Grab the battlemetrics ID's for the users BEGUID and STEAMID
        for included in player_info.get("included"):  # type: ignore [reportOptionalIterable]
            if included["type"] == "identifier":
                if included["attributes"]["type"] == "BEGUID":
                    data["data"]["attributes"]["identifiers"].append(included["id"])
                if included["attributes"]["type"] == "steamID":
                    data["data"]["attributes"]["identifiers"].append(included["id"])

        return await self.request(Route(method="POST", path="/bans"), json=data)

    async def add_note(
        self,
        note: str,
        player_id: int,
        organization_id: int,
        *,
        shared: bool = True,
    ) -> dict[str, Any]:
        """Create a new note.

        Parameters
        ----------
            note (str): The note it
            shared (bool): Will this be shared or not? (True or False), default is True
            organization_id (int): The organization ID this note belongs to.
            player_id (int): The battlemetrics ID of the player this note is attached to.

        Returns
        -------
            dict: Response from server (was it successful?)
        """
        data = {
            "data": {
                "type": "playerNote",
                "attributes": {
                    "note": note,
                    "shared": shared,
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}",
                        },
                    },
                },
            },
        }
        return await self.request(
            Route(method="POST", path=f"/players/{player_id}/relationships/notes"),
            json=data,
        )

    async def session_info(
        self,
        *,
        filter_server: int | None = None,
        filter_game: str | None = None,
        filter_organizations: int | None = None,
        filter_player: int | None = None,
        filter_identifiers: int | None = None,
    ) -> list[Session] | Session:
        """Return the session information for the targeted server, game or organization.

        Parameters
        ----------
            server (int, optional): Targeted server. Defaults to None.
            game (str, optional): Targeted game. Defaults to None.
            organizations (int, optional): Targeted Organization. Defaults to None.
            player (int, optional): Targeted player. Defaults to None.
            identifiers (int, optional): Targeted identifiers. Defaults to None.
        """
        data = {
            "include": "identifier,server,player",
            "page[size]": "100",
        }
        if filter_server:
            data["filter[servers]"] = str(filter_server)
        if filter_game:
            data["filter[game]"] = filter_game
        if filter_organizations:
            data["filter[organizations]"] = str(filter_organizations)
        if filter_player:
            data["filter[players]"] = str(filter_player)
        if filter_identifiers:
            data["filter[identifiers]"] = str(filter_identifiers)

        r = await self.request(Route(method="GET", path="/sessions"), params=data)
        r = r.get("data")

        if len(r) == 0:
            fmt = "No servers found."
            raise ValueError(fmt)

        if len(r) > 1:
            return [
                Session(
                    data=x,
                    http=self,
                )
                for x in r
            ]

        return Session(
            data=r,
            http=self,
        )

    async def get_banlist(self, banlist_id: str) -> BanList:
        """Return the banlist information of the targeted banlist.

        Parameters
        ----------
            banlist_id (str): The ID of the banlist you want.

        Returns
        -------
            dict: The dictionary response of the targeted banlist.
        """
        data = {
            "page[size]": "100",
            "include": "organization,owner,server",
        }
        r = await self.request(
            Route(
                method="GET",
                path="/ban-lists",
            ),
            params=data,
        )
        for banlist in r.get("data"):
            if banlist.get("id") == banlist_id:
                return BanList(
                    banlist.get("data"),
                    http=self,
                )

        fmt = "Could not find that banlist."
        raise ValueError(fmt)

    async def create_banlist(
        self,
        *,
        name: str,
        organization_id: int,
        action: str,
        default_identifiers: list[IDENTIFIERS],
        default_reasons: list[str],
        autoadd: bool = False,
        native_ban: bool = False,
    ) -> BanList:
        """Create a new banlist for your targeted organization.

        Parameters
        ----------
            name (str): Name of the ban list.
            organization_id (int): The organization ID.
            action (str): "none", "log", "kick"
            default_identifiers (list): ["steamID", "ip"]
            default_reasons (list): List of default reasons for the ban.
            autoadd (bool, optional): true or false. Defaults to False.
            native_ban (bool, optional): Whether this ban should be a native ban. Defaults to False.
        """
        data: dict[str, Any] = {
            "data": {
                "type": "banList",
                "attributes": {
                    "name": f"{name}",
                    "action": f"{action}",
                    "defaultIdentifiers": default_identifiers,
                    "defaultReasons": default_reasons,
                    "defaultAutoAddEnabled": str(autoadd).lower(),
                    "defaultNativeEnabled": str(native_ban).lower(),
                    "nativeBanTTL": None,
                    "nativeBanTempMaxExpires": None,
                    "nativeBanPermMaxExpires": None,
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}",
                        },
                    },
                    "owner": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}",
                        },
                    },
                },
            },
        }
        r = await self.request(
            Route(
                method="POST",
                path="/ban-lists",
            ),
            json=data,
        )
        return BanList(
            data=r.get("data"),
            http=self,
        )

    async def rust_banlist_export(
        self,
        organization_id: int,
        server_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Export your rust banlist.

        Parameters
        ----------
            organization_id (int): Organization ID the banlist belongs to
            server_id (int): Server ID the banlist is associated with.
        """
        params = {
            "filter[organization]": organization_id,
            "format": "rust/bans.cfg",
        }
        if server_id:
            params["filter[server]"] = server_id

        return await self.request(
            Route(
                method="GET",
                path="/bans/export",
            ),
            params=params,
        )

    async def banlist_unsubscribe(self, banlist_id: str, organization_id: int) -> None:
        """Unsubscribe from a banlist.

        Parameters
        ----------
            banlist_id (str): ID of the banlist
            organization_id (str): Your organization ID
        """
        await self.request(
            Route(
                method="DELETE",
                path=f"/ban-lists/{banlist_id}/relationships/organizations/{organization_id}",
            ),
        )

    # TODO: Response unknown so I don't know what to return.
    async def banlist_subscribed_orgs(self, banlist_id: str) -> dict[str, Any]:
        """List all the organizations that are subscribed to the targeted banlist.

        You require manage perms to use this list (or be the owner).

        Parameters
        ----------
            banlist_id (str): The Banlist ID

        Returns
        -------
            dict: A dictionary response of all the organizations subbed to the targeted banlist.
        """
        data = {
            "include": "server,organization,owner",
            "page[size]": "100",
        }
        return await self.request(
            Route(
                method="GET",
                path=f"/ban-lists/{banlist_id}/relationships/organizations",
            ),
            params=data,
        )

    # TODO: Response unknown so I don't know what to return.
    async def banlist_subscribers(self, banlist_id: str, organization_id: int) -> dict[str, Any]:
        """Get the subscriber information for a specific banlist.

        Parameters
        ----------
            banlist_id (str): The ID of the targeted banlist.
            organization_id (str): The ID of the targeted organization subscribed to the banlist.
        """
        data = {
            "include": "organization,owner,server",
        }
        return await self.request(
            Route(
                method="GET",
                path=f"/ban-lists/{banlist_id}/relationships/{organization_id}",
            ),
            params=data,
        )

    async def banlist_read(self, banlist_id: str) -> str:
        """Retrieve the name of a banlist by the banlist id.

        Parameters
        ----------
            banlist_id (str): The ID of the banlist.
        """
        data = {
            "include": "owner",
        }
        r = await self.request(
            Route(
                method="GET",
                path=f"/ban-lists/{banlist_id}",
            ),
            params=data,
        )
        return r.get("data").get("attributes").get("name")

    async def banlist_update(
        self,
        banlist_id: str,
        organization_id: int,
        *,
        name: str | None = None,
        action: str | None = None,
        default_identifiers: list[IDENTIFIERS],
        default_reasons: list[str],
        autoadd: bool | None = None,
        native_ban: bool | None = None,
    ) -> BanList:
        """Update the targeted banlist with the altered information you supply.

        Parameters
        ----------
            banlist_id (str): Banlist ID.
            organization_id (int): Organization ID
            name (str, optional): Name of the banlist
            action (str, optional): "none", "log" or "kick"
            ban_identifiers (list, optional): ["steamID", "ip"]
            list_default_reasons (list, optional): [List of default reasons]
            autoadd (bool, optional): True or False
            native_ban (bool, optional): True or False
        """
        data: dict[str, Any] = {
            "data": {
                "type": "banList",
                "attributes": {
                    "name": f"{name}",
                    "action": f"{action}",
                    "defaultIdentifiers": default_identifiers,
                    "defaultReasons": default_reasons,
                    "defaultAutoAddEnabled": str(autoadd).lower(),
                    "defaultNativeEnabled": str(native_ban).lower(),
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}",
                        },
                    },
                    "owner": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}",
                        },
                    },
                },
            },
        }

        r = await self.request(
            Route(
                method="PATCH",
                path=f"/ban-lists/{banlist_id}/relationships/organizations/{organization_id}",
            ),
            json=data,
        )
        return BanList(
            r.get("data"),
            http=self,
        )

    async def banlist_list(self) -> list[BanList]:
        """List all your banlists for you.

        Returns
        -------
            dict: A dictionary response of all the banlists you have access to.
        """
        data = {
            "include": "server,organization,owner",
            "page[size]": "100",
        }
        request = await self.request(
            Route(
                method="GET",
                path="/ban-lists",
            ),
            params=data,
        )
        request = request.get("data")

        if len(request) == 0:
            fmt = "No banlists found."
            raise ValueError(fmt)

        return [
            BanList(
                data=x,
                http=self,
            )
            for x in request
        ]

    # TODO: Type for perm...
    async def create_banlist_invite(
        self,
        organization_id: int,
        banlist_id: str,
        *,
        uses: int = 1,
        limit: int = 1,
        permmanage: bool = False,
        permcreate: bool = False,
        permupdate: bool = False,
        permdelete: bool = False,
    ) -> BanListInvite | None:
        """Create an invite.

        Parameters
        ----------
            organization_id (int): The target organization to be invited.
            banlist_id (str): The ID of the banlist you want to create the invite for
            permManage (bool): Are they allowed to manage it?
            permCreate (bool): Can they create stuff related to this banlist?
            permUpdate (bool): Can they update the banlist?
            permDelete (bool): Can they delete stuff related to this banlist?
            uses (int, optional): Number of times this banlist invite has been used. Defaults to 1.
            limit (int, optional): How many times it's allowed to be used. Defaults to 1.

        Returns
        -------
            dict: Returns whether it was successful or not.
        """
        data = {
            "data": {
                "type": "banListInvite",
                "attributes": {
                    "uses": uses,
                    "limit": limit,
                    "permManage": permmanage,
                    "permCreate": permcreate,
                    "permUpdate": permupdate,
                    "permDelete": permdelete,
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}",
                        },
                    },
                },
            },
        }
        r: dict[str, Any] = await self.request(
            Route(
                method="POST",
                path=f"/ban-lists/{banlist_id}/relationships/invites",
            ),
            json=data,
        )

        relationships = utils.format_relationships(r.get("relationships"))
        return BanListInvite(
            id=int(r.get("data").get("id")),  # type: ignore [reportOptionalMemberAccess]
            type=r.get("data").get("type"),  # type: ignore [reportOptionalMemberAccess]
            banlist_id=relationships.get("banList_id"),  # type: ignore [reportArgumentType]
            organization_id=relationships.get("organization_id"),  # type: ignore [reportArgumentType]
        )

    async def read_banlist_invitation(self, invite_id: str) -> BanListInvite:
        """See the information about a specific banlist invite, such as uses.

        Paramaters
        ----------
            invite_id (str): The banlist invite id.

        Returns
        -------
            dict: The banlist invite information
        """
        data = {
            "include": "banList",
            "fields[organization]": "tz,banTemplate",
            "fields[user]": "nickname",
            "fields[banList]": "name, action",
            "fields[banListInvite]": "uses",
        }
        r = await self.request(
            Route(
                method="GET",
                path=f"/ban-list-invites/{invite_id}",
            ),
            params=data,
        )
        relationships = utils.format_relationships(r.get("relationships"))
        return BanListInvite(
            id=int(r.get("data").get("id")),
            type=r.get("data").get("type"),
            banlist_id=relationships.get("banList_id"),  # type: ignore [reportArgumentType]
            organization_id=relationships.get("organization_id"),  # type: ignore [reportArgumentType]
        )

    async def banlist_accept_invite(
        self,
        code: str,
        *,
        action: str,
        default_identifiers: list[IDENTIFIERS],
        default_reasons: list[str],
        organization_id: int,
        organization_owner_id: str,
        autoadd: bool,
        native_ban: bool,
    ) -> BanListInvite:
        """Accept an invitation to subscribe to a banlist.

        Parameters
        ----------
            code (str): Invitation code.
            action (str): "none", "log" or "kick"
            default_identifiers (list): ["steamID", "ip"]
            default_reasons (list): ["Banned for hacking"]
            organization_id (str): ID of your organization?
            organization_owner_id (str): ID of the owner of the organization
            autoadd (bool): True or False
            native_ban (bool): True or False
        """
        data = {
            "data": {
                "type": "banList",
                "attributes": {
                    "code": code,
                    "action": action,
                    "defaultIdentifiers": default_identifiers,
                    "defaultReasons": default_reasons,
                    "defaultAutoAddEnabled": str(autoadd).lower(),
                    "defaultNativeEnabled": str(native_ban).lower(),
                    "nativeBanTTL": None,
                    "nativeBanTempMaxExpires": None,
                    "nativeBanPermMaxExpires": None,
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}",
                        },
                    },
                    "owner": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_owner_id}",
                        },
                    },
                },
            },
        }
        r = await self.request(
            Route(
                method="POST",
                path="/ban-lists/accept-invite",
            ),
            json=data,
        )
        return BanListInvite(
            id=int(r.get("data").get("id")),
            banlist_id=r.get("relationships").get("banList").get("data").get("id"),
            organization_id=r.get("relationships").get("organization").get("data").get("id"),
        )

    async def banlist_invite_list(self, banlist_id: str) -> list[BanListInvite]:
        """Return all the invites for a specific banlist ID.

        Parameters
        ----------
            banlist_id (str): The ID of a banlist
        """
        data = {
            "include": "banList",
            "fields[organization]": "tz,banTemplate",
            "fields[user]": "nickname",
            "fields[banList]": "name,action",
            "fields[banListInvite]": "uses",
            "page[size]": "100",
        }
        r = await self.request(
            Route(
                method="GET",
                path=f"/ban-lists/{banlist_id}/relationships/invites",
            ),
            params=data,
        )
        return [
            BanListInvite(
                id=int(x.get("id")),
                type=x.get("type"),
                banlist_id=banlist_id,
                organization_id=x.get("relationships").get("data").get("id"),  # type: ignore [reportArgumentType]
            )
            for x in r.get("data")
        ]

    async def delete_banlist_invite(self, banlist_id: str, banlist_invite_id: str) -> None:
        """Delete an invite from a targeted banlist.

        Parameters
        ----------
            banlist_id (str): The target banlist
            banlist_invite_id (str): The target invite.
        """
        await self.request(
            Route(
                method="DELETE",
                path=f"/ban-lists/{banlist_id}/relationships/invites/{banlist_invite_id}",
            ),
        )

    async def banlist_exemption_create(
        self,
        ban_id: int,
        organization_id: int,
        reason: str | None = None,
    ) -> BanListExemption:
        """Create an exemption to the banlist.

        Parameters
        ----------
            ban_id (str): The ban id you want to create an exemption for.
            organization_id (int): The organization associated to the exemption
            reason (str, optional): Reason for the exemption. Defaults to None.
        """
        data = {
            "data": {
                "type": "banExemption",
                "attributes": {
                    "reason": reason,
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}",
                        },
                    },
                },
            },
        }
        r = await self.request(
            Route(
                method="POST",
                path=f"/bans/{ban_id}/relationships/exemptions",
            ),
            json=data,
        )
        return BanListExemption(
            id=int(r.get("data").get("id")),
            reason=r.get("data").get("attributes").get("reason"),
            ban_id=ban_id,
            organization_id=organization_id,
        )

    async def banlist_exemption_delete(self, ban_id: str) -> None:
        """Delete an exemption.

        Parameters
        ----------
            ban_id (str): The ban that has an exemption
        """
        await self.request(
            Route(method="DELETE", path=f"/bans/{ban_id}/relationships/exemptions"),
        )

    async def banlist_exemption_info(self, ban_id: int, exemption_id: str) -> BanListExemption:
        """Pull information from a ban regarding a specific exemption.

        Parameters
        ----------
            ban_id (str): Target ban
            exemption_id (str): Target exemption
        """
        r = await self.request(
            Route(method="GET", path=f"/bans/{ban_id}/relationships/exemptions/{exemption_id}"),
        )
        return BanListExemption(
            id=int(r.get("data").get("id")),
            reason=r.get("data").get("attributes").get("reason"),
            ban_id=int(ban_id),
            organization_id=r.get("relationships").get("organization").get("data").get("id"),
        )

    async def banlist_exemptions_info(self, ban_id: str) -> BanListExemption:
        """Pull all exemptions related to the targeted ban.

        Parameters
        ----------
            ban_id (str): Target ban
        """
        data = {
            "fields[banExemption]": "reason",
        }
        r = await self.request(
            Route(method="GET", path=f"/bans/{ban_id}/relationships/exemptions"),
            params=data,
        )
        return BanListExemption(
            id=int(r.get("data").get("id")),
            reason=r.get("data").get("attributes").get("reason"),
            ban_id=int(ban_id),
            organization_id=r.get("relationships").get("organization").get("data").get("id"),
        )

    async def banlist_exemption_update(
        self,
        ban_id: int,
        exemption_id: str,
        reason: str,
    ) -> BanListExemption:
        """Update a ban exemption.

        Parameters
        ----------
            ban_id (str): The target ban
            exemption_id (str): The target exemption
            reason (str): New reason
        """
        exemption = await self.banlist_exemption_info(ban_id=ban_id, exemption_id=exemption_id)

        data = {
            "data": {
                "type": "banExemption",
                "id": exemption_id,
                "attributes": {
                    "reason": reason,
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{exemption.organization_id}",
                        },
                    },
                },
            },
        }

        r = await self.request(
            Route(method="PATCH", path=f"/bans/{ban_id}/relationships/exemptions"),
            json=data,
        )
        return BanListExemption(
            id=int(r.get("data").get("id")),
            reason=reason,
            ban_id=ban_id,
            organization_id=r.get("relationships").get("organization").get("data").get("id"),
        )
