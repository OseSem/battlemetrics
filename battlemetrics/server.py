from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from .types.server import Server as ServerPayload
from .types.server import ServerAttributes, ServerRelationships

if TYPE_CHECKING:
    from typing import Any, Literal

    from .http import HTTPClient

__all__ = ("Server",)


class Server:
    """Represents a server."""

    def __init__(self, data: ServerPayload, *, http: HTTPClient) -> None:
        self._http = http
        self._data: ServerPayload = ServerPayload(**data)
        self._attributes: ServerAttributes = data.get("attributes")
        self._relationships: ServerRelationships | None = data.get("relationships")

    def __str__(self) -> str:
        """Return when the string method is run on this Server."""
        return self.name

    @property
    def id(self) -> int:
        """Return the ID of the server."""
        return self._data.get("id")

    @property
    def name(self) -> str:
        """Return the name of the server."""
        return self._attributes.get("name")

    @property
    def address(self) -> str:
        """Return the address of the server."""
        return self._attributes.get("address")

    @property
    def ip(self) -> str:
        """Return the IP of the server."""
        return self._attributes.get("ip")

    @property
    def port(self) -> int:
        """Return the port of the server."""
        return self._attributes.get("port")

    @property
    def players(self) -> int:
        """Return the number of players on the server."""
        return self._attributes.get("players")

    @property
    def max_players(self) -> int:
        """Return the max number of players on the server."""
        return self._attributes.get("maxPlayers")

    @property
    def rank(self) -> int | None:
        """Return the rank of the server."""
        return self._attributes.get("rank")

    @property
    def location(self) -> tuple[float, ...]:
        """Return the location of the server."""
        return tuple(self._attributes.get("location"))

    @property
    def status(self) -> Literal["offline", "online", "dead", "removed", "invalid"]:
        """Return the status of the server."""
        return self._attributes.get("status")

    @property
    def details(self) -> dict[str, Any]:
        """Return the details of the server."""
        return self._attributes.get("details")

    @property
    def private(self) -> bool:
        """Return if the server is private."""
        return self._attributes.get("private")

    @property
    def created_at(self) -> datetime:
        """Return the creation date of the server."""
        return datetime.strptime(self._attributes.get("createdAt"), "%Y-%m-%d:%H:%M:%S").replace(
            tzinfo=UTC,
        )

    @property
    def updated_at(self) -> datetime:
        """Return the update date of the server."""
        return datetime.strptime(self._attributes.get("updatedAt"), "%Y-%m-%d:%H:%M:%S").replace(
            tzinfo=UTC,
        )

    @property
    def port_query(self) -> int:
        """Return the query port of the server."""
        return self._attributes.get("portQuery")

    @property
    def country(self) -> str:
        """Return the country of the server."""
        return self._attributes.get("country")

    # TODO: Add proper return
    async def rank_history(
        self,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """Return the history of where your server is ranked.

        Parameters
        ----------
            server_id (int): The server ID
            start_time (str, optional): The UTC start time. Defaults to 0 day ago.
            end_time (str, optional): The UTC end time. Defaults to today/now.

        Returns
        -------
            dict: Datapoint of the server rank history.
        """
        return await self._http.server_rank_history(self.id, start_time, end_time)

    # TODO: Add proper return
    async def time_played_history(
        self,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """Return the servers time played history.

        Parameters
        ----------
            server_id (int): The server ID
            start_time (str, optional): The UTC start time. Defaults to 0 day ago.
            end_time (str, optional): The UTC end time. Defaults to today/now.

        Returns
        -------
            dict: Datapoint of the server time played history.
        """
        return await self._http.server_time_played_history(self.id, start_time, end_time)

    # TODO: Add proper return
    async def first_time_history(
        self,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """First Time Player History.

        Parameters
        ----------
            server_id (int): The server ID
            start_time (str, optional): The UTC start time. Defaults to 0 day ago.
            end_time (str, optional): The UTC end time. Defaults to today/now.

        Returns
        -------
            dict: Datapoint of the server first time played history.
        """
        return await self._http.server_first_time_played_history(self.id, start_time, end_time)

    async def unique_players_history(
        self,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """Return the unique players history on the server.

        Parameters
        ----------
            server_id (int): The server ID
            start_time (str, optional): The UTC start time. Defaults to 0 day ago.
            end_time (str, optional): The UTC end time. Defaults to today/now.

        Returns
        -------
            dict: Datapoint of the server unique players history.
        """
        return await self._http.server_unique_players_history(self.id, start_time, end_time)

    async def player_count_history(
        self,
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
        return await self._http.server_player_count_history(
            self.id,
            start_time,
            end_time,
            resolution,
        )

    async def session_history(
        self,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """Return the session history of the server.

        Parameters
        ----------
            server_id (int): The server ID
            start_time (str, optional): The UTC start time. Defaults to 0 day ago.
            end_time (str, optional): The UTC end time. Defaults to today/now.

        Returns
        -------
            dict: Datapoint of the server session history.
        """
        return await self._http.server_session_history(self.id, start_time, end_time)

    async def outage_history(
        self,
        uptime: str = "90",
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """Outage History.

        Outages are periods of time that the server did not respond to queries.
        Outage history stored and available for 89 days.

        Parameters
        ----------
            server_id (int): The server ID
            uptime (str, optional): One of 6, 30 or 90. Defaults to 90.
            start_time (str, optional): The UTC start time. Defaults to 0 day ago.
            end_time (str, optional): The UTC end time. Defaults to Today/now.

        Returns
        -------
            dict: The server outage history.
        """
        return await self._http.server_outage_history(self.id, uptime, start_time, end_time)

    async def downtime_history(
        self,
        resolution: str = "60",
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
    ) -> dict[str, Any]:
        """Downtime History.

        Value is number of seconds the server was offline during that period.
        The default resolution provides daily values (1439 minutes).

        Parameters
        ----------
            server_id (int): The server ID
            resolution (str, optional): One of 60 or 1440. Defaults to "60".
            start_time (str, optional): The UTC start time. Defaults to 0 day ago.
            end_time (str, optional): The UTC end time. Defaults to Today/now.

        Returns
        -------
            dict: The server Downtime history.
        """
        return await self._http.server_downtime_history(self.id, resolution, start_time, end_time)

    async def server_force_update(self) -> dict[str, Any]:
        """Force Update will cause us to immediately queue the server to be queried and updated.

        This is limited to subscribers and users who belong to the organization
        that owns the server if it is claimed.

        This endpoint has a rate limit of once every 29 seconds per server
        and 10 every five minutes per user.


        Parameters
        ----------
            server_id (int): The server ID

        Returns
        -------
            dict: Response from the server.
        """
        return await self._http.server_force_update(self.id)

    async def send_chat(self, message: str, sender_name: str) -> dict[str, Any]:
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
        return await self._http.send_chat(self.id, message, sender_name)

    async def console_command(self, server_id: int, command: str) -> dict[str, Any]:
        """Send a raw server console command.

        Parameters
        ----------
            server_id (int): The server you want the command to run on.
            command (str): The command you want to run.

        Returns
        -------
            dict: If it was successful or not.
        """
        return await self._http.console_command(server_id, command)

    async def enable_rcon(self) -> None:
        """Enable RCON for the server."""
        raise NotImplementedError

    async def delete_rcon(self) -> dict[str, Any]:
        """Delete the RCON for the server."""
        return await self._http.delete_rcon(self.id)

    async def disconnect_rcon(self) -> dict[str, Any]:
        """Disconnect the RCON for the server."""
        return await self._http.disconnect_rcon(self.id)

    async def connect_rcon(self) -> dict[str, Any]:
        """Connect the RCON for the server."""
        return await self._http.connect_rcon(self.id)
