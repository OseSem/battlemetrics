from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from .types.player import Player as PlayerPayload

if TYPE_CHECKING:
    from typing import Any

    from .http import HTTPClient
    from .types.player import PlayerAttributes

__all__ = ("Player",)


class Player:
    """Represents a server."""

    def __init__(self, data: PlayerPayload, *, http: HTTPClient) -> None:
        self._http = http

        self._data: PlayerPayload = PlayerPayload(**data)
        self._attributes: PlayerAttributes = data.get("attributes")

    def __str__(self) -> str:
        """Return the name of the player when the str method is run."""
        return self.name

    @property
    def id(self) -> int:
        """Return the ID of the player."""
        return self._data.get("id")

    @property
    def name(self) -> str:
        """Return the name of the player."""
        return self._attributes.get("name")

    @property
    def created_at(self) -> datetime:
        """Return the creation date of the server."""
        return datetime.strptime(
            self._attributes.get("createdAt"),
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ).replace(
            tzinfo=UTC,
        )

    @property
    def updated_at(self) -> datetime:
        """Return the update date of the server."""
        return datetime.strptime(
            self._attributes.get("updatedAt"),
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ).replace(
            tzinfo=UTC,
        )

    @property
    def private(self) -> bool:
        """Return if the player is private."""
        return self._attributes.get("private")

    @property
    def positive_match(self) -> bool:
        """Return if the player is a positive match."""
        return self._attributes.get("positiveMatch")

    async def server_info(self, server_id: int) -> dict[str, Any]:
        """Return server specifics for the given player and server.

        Parameters
        ----------
            player_id (int): The battlemetrics player ID.
            server_id (int): The server ID
        Returns:
            dict: Response from the server showing the player server info.
        """
        return await self._http.player_server_info(self.id, server_id)

    async def session_history(
        self,
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
        return await self._http.player_session_history(
            player_id=self.id,
            filter_server=filter_server,
            filter_organization=filter_organization,
        )

    async def coplay_info(
        self,
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
        return await self._http.player_coplay_info(
            player_id=self.id,
            start_time=start_time,
            end_time=end_time,
            player_names=player_names,
            organization_names=organization_names,
            server_names=server_names,
        )

    async def ban(
        self,
        reason: str,
        note: str,
        org_id: str,
        banlist: str,
        server_id: str,
        expires: str | None = None,
        *,
        orgwide: bool = True,
    ) -> dict[str, Any]:
        """Ban the player."""
        return await self._http.add_ban(
            battlemetrics_id=self.id,
            reason=reason,
            note=note,
            org_id=org_id,
            banlist=banlist,
            server_id=server_id,
            expires=expires,
            orgwide=orgwide,
        )

    async def add_note(
        self,
        note: str,
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

        Returns
        -------
            dict: Response from server (was it successful?)
        """
        return await self._http.add_note(
            note=note,
            player_id=self.id,
            organization_id=organization_id,
            shared=shared,
        )

    async def add_flag(self, flag_id: str | None = None) -> dict[str, Any]:
        """Create or add a flag to the targeted players profile.

        Parameters
        ----------
            player_id (int): Battlemetrics ID of the player.
            flag_id (str, optional): An existing flag ID. Defaults to None.

        Returns
        -------
            dict: Player profile relating to the new flag.
        """
        return await self._http.add_flag(self.id, flag_id)

    async def remove_flag(self, flag_id: str) -> None:
        """Delete a targeted flag from a targeted player ID.

        Parameters
        ----------
            player_id (int): Battlemetrics ID of the player.
            flag_id (str): The ID of the flag to remove.

        Returns
        -------
            dict: If you were successful or not.
        """
        return await self._http.remove_flag(self.id, flag_id)

    async def fetch_flags(self) -> dict[str, Any]:
        """Return all the flags on a players profile.

        Parameters
        ----------
            player_id (int): Battlemetrics ID of the targeted player.

        Returns
        -------
            dict: The profile with all the flags.
        """
        return await self._http.player_flags(self.id)
