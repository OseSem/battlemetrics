from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal

from battlemetrics.http import HTTPClient, Route
from battlemetrics.types.misc import ActivityLogs, APIScopes, Metrics

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from typing import Any

    from aiohttp import BaseConnector

    from .http import IDENTIFIERS
    from .note import Note
    from .organization import Organization
    from .player import Player
    from .server import Server
    from .session import Session

__all__ = ("Battlemetrics",)


class Battlemetrics:
    """The main client to handle all the Battlemetrics requests.

    Parameters
    ----------
        api_key (str)
            Your given API token.
    """

    def __init__(
        self,
        api_key: str,
        *,
        connector: BaseConnector | None = None,
        loop: AbstractEventLoop | None = None,
    ) -> None:
        self.__api_key = api_key

        self.loop = loop

        self.http = HTTPClient(
            api_key=self.__api_key,
            connector=connector,
            loop=loop,
        )

    async def get_note(self, player_id: int, note_id: int) -> Note:
        """Return a note based on player ID and note ID.

        Parameters
        ----------
            player_id (int):
                The ID of the player.
            note_id (int):
                The ID of the note.
        """
        return await self.http.get_note(player_id, note_id)

    async def get_server(self, server_id: int) -> Server:
        """Return a note based on Server ID.

        Parameters
        ----------
            server_id (int):
                The ID of the Server.
        """
        return await self.http.get_server(server_id)

    async def get_organization(self, organization_id: int) -> Organization:
        """Return a note based on Organization ID.

        Parameters
        ----------
            organization_id (int):
                The ID of the Organization.
        """
        return await self.http.get_organization(organization_id)

    async def get_player(self, player_id: int) -> Player:
        """Return a note based on Player ID.

        Parameters
        ----------
            player_id (int):
                The ID of the Player.
        """
        return await self.http.get_player(player_id)

    async def get_session(
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
        return await self.http.session_info(
            filter_server=filter_server,
            filter_game=filter_game,
            filter_organizations=filter_organizations,
            filter_player=filter_player,
            filter_identifiers=filter_identifiers,
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
        return await self.http.search_player(
            search=search,
            filter_game=filter_game,
            filter_servers=filter_servers,
            filter_organization=filter_organization,
            filter_online=filter_online,
            filter_public=filter_public,
            flag=flag,
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
        return await self.http.search_server(
            search=search,
            countries=countries,
            game=game,
            blacklist=blacklist,
            whitelist=whitelist,
            organization=organization,
            gather_rate_min=gather_rate_min,
            gather_rate_max=gather_rate_max,
            group_size_min=group_size_min,
            group_size_max=group_size_max,
            map_size_min=map_size_min,
            map_size_max=map_size_max,
            blueprints=blueprints,
            pve=pve,
            kits=kits,
            status=status,
            page_size=page_size,
            sort_rank=sort_rank,
            rcon=rcon,
        )

    async def match_identifiers(
        self,
        identifier: Any,
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
        return await self.http.match_identifiers(identifier, identifier_type)

    async def quick_match(
        self,
        identifier: Any,
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
        return await self.http.quick_match(identifier, identifier_type)

    async def player_identifiers(self, player_id: int) -> dict[str, Any]:
        """Player Identifiers.

        Returns all the identifiers for a player.

        Parameters
        ----------
            player_id (int): The ID of the player.

        Returns
        -------
            dict: Dictionary response of any matches.
        """
        return await self.http.player_identifiers(player_id)

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

        Returns
        -------
            list[dict]: A list of dictionaries that provide the ban data.
        """
        return await self.http.rust_banlist_export(organization_id, server_id)

    async def check_api_scopes(self, token: str | None = None) -> APIScopes:
        """Retrieve the token scopes from the oauth.

        Parameters
        ----------
            token (str | None):
                Your given API token. Defaults to the one supplied to this battlemetrics class.

        Returns
        -------
            APIScopes
        """
        token = token if token else self.__api_key

        url: str = "https://www.battlemetrics.com/oauth/introspect"
        json_dict = {
            "token": token,
        }
        data: dict[str, Any] = (
            await self.http.request(
                Route(
                    method="POST",
                    url=url,
                ),
                json=json_dict,
            )
            or {}
        )

        data = data.get("data", {})

        return APIScopes(**data)

    async def metrics(
        self,
        name: str = "games.rust.players",
        start_date: str | datetime | None = None,
        end_date: str | datetime | None = None,
        resolution: str = "60",
    ) -> list[Metrics]:
        """Return metrics.

        Parameters
        ----------
            name (str, optional): "games.{game}.players" and "games.{game}.players.steam".
            start_date (str, optional) UTC time format. Defaults to Current Date.
            end_date (str, optional): UTC time format. Defaults to 1 day ago.
            resolution (str, optional): raw, 30, 60 or 1440. Defaults to "60".

        Returns
        -------
            dict: a bunch of numbers.
        """
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)

        if not start_date:
            now = datetime.now(tz=UTC)
            start_date = now - timedelta(days=1)
            start_date = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not end_date:
            end_date = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        params = {
            "metrics[0][name]": name,
            "metrics[0][range]": f"{start_date}:{end_date}",
            "metrics[0][resolution]": resolution,
            "fields[dataPoint]": "name,group,timestamp,value",
        }
        data = await self.http.request(
            Route(
                method="GET",
                path="/metrics",
            ),
            params=params,
        )

        return [Metrics(**x) for x in data["data"]]

    async def activity_logs(
        self,
        filter_bmid: int | None = None,
        filter_search: str | None = None,
        filter_servers: int | None = None,
        blacklist: str | None = None,
        whitelist: str | None = None,
    ) -> ActivityLogs:
        """Retrieve the activity logs.

        Parameters
        ----------
            filter_bmid (int, optional): A battlemetrics ID for a specific user. Defaults to None.
            filter_search (str, optional): What do you want to search?. Defaults to None.
            filter_servers (int, optional): A specific battlemetrics server ID. Defaults to None.
            blacklist (str, optional): Example: unknown, playerMessage. Defaults to None.
            whitelist (str, optional): unknown, playerMessage. Defaults to None.

        Returns
        -------
            dict: The activity logs information.
        """
        params = {
            "page[size]": "100",
            "include": "organization,server,user,player",
        }

        if blacklist:
            params["filter[types][blacklist]"] = blacklist
        if whitelist:
            params["filter[types][whitelist]"] = whitelist
        if filter_servers:
            params["filter[servers]"] = str(filter_servers)
        if filter_search:
            params["filter[search]"] = filter_search
        if filter_bmid:
            params["filter[players]"] = str(filter_bmid)

        data = await self.http.request(
            Route(
                method="GET",
                path="/activity",
            ),
            params=params,
        )
        return ActivityLogs(**data)
