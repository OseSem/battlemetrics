from __future__ import annotations

import asyncio
import logging
import warnings
from typing import TYPE_CHECKING, Any, Literal, Self

from battlemetrics.http import HTTPClient
from battlemetrics.models.ban import Ban, NativeBan
from battlemetrics.models.banlist import BanList, BanListExemption, BanListInvite
from battlemetrics.models.flag import FlagPlayer, PlayerFlag
from battlemetrics.models.game import Game, GameFeatureOptions, GameFeatures
from battlemetrics.models.misc import CommandsActivity, Coplay, Leaderboard
from battlemetrics.models.note import Note
from battlemetrics.models.organization import (
    Organization,
    OrganizationFriend,
    OrganizationStats,
)
from battlemetrics.models.player import (
    Player,
    QuickMatchIdentifier,
    RelatedPlayerIdentifier,
)
from battlemetrics.models.query import PlayerQuery, PlayerQueryResult
from battlemetrics.models.server import ReservedSlot, Server
from battlemetrics.models.session import Session
from battlemetrics.models.user import User

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from types import TracebackType

    from aiohttp import BaseConnector, BasicAuth

__all__ = ("Battlemetrics",)

_log = logging.getLogger(__name__)


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
        asyncio_debug: bool = False,
        connector: BaseConnector | None = None,
        loop: AbstractEventLoop | None = None,
        proxy: str | None = None,
        proxy_auth: BasicAuth | None = None,
    ) -> None:
        self.__api_key = api_key

        if loop is None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        else:
            self.loop: asyncio.AbstractEventLoop = loop

        self.loop.set_debug(asyncio_debug)

        self.http = HTTPClient(
            api_key=self.__api_key,
            connector=connector,
            loop=loop,
            proxy=proxy,
            proxy_auth=proxy_auth,
        )

    async def __aenter__(self) -> Self:
        """Enter the context manager and return the Battlemetrics client."""
        return self

    async def __aexit__(
        self,
        type: type[BaseException] | None,  # noqa: A002
        value: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the client when exiting the context."""
        await self.close()

    async def close(self) -> None:
        """Close the client."""
        await self.http.close()

    # Helpers / Getters

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
        identifiers: list[str | dict[str, Any]] | None = None,  # TODO: Add player object
        expires: str | None = None,
    ) -> Ban:
        """Create a ban with all required and optional parameters."""
        resp = await self.http.create_ban(
            player_id=player_id,
            reason=reason,
            note=note,
            banlist_id=banlist_id,
            organization_id=organization_id,
            server_id=server_id,
            org_wide=org_wide,
            auto_add_enabled=auto_add_enabled,
            native_enabled=native_enabled,
            identifiers=identifiers,
            expires=expires,
        )
        return Ban.model_validate(resp["data"])

    async def import_bans(self, bans: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Import multiple bans at once.

        This method allows adding multiple bans at once with certain limitations.

        Parameters
        ----------
        bans : list[dict[str, Any]]
            A list of ban data dictionaries, each containing attributes and relationships.

        Returns
        -------
        Any
            The response from the API.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        return await self.http.import_bans(bans)

    async def export_bans(
        self,
        file_format: Literal[
            "arma2/bans.txt",
            "arma3/bans.txt",
            "squad/Bans.cfg",
            "ark/banlist.txt",
            "rust/bans.cfg",
            "rust/bansip_SERVER.ini",
        ],
        *,
        organization_id: int | None = None,
        server_id: int | None = None,
    ) -> Any:
        """Export bans in a specific format.

        Parameters
        ----------
        file_format : str
            The format to export the bans in.

        Returns
        -------
        Any
            The response from the API containing the exported bans.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        return await self.http.export_bans(
            file_format=file_format,
            organization_id=organization_id,
            server_id=server_id,
        )

    async def delete_ban(self, ban_id: int) -> None:
        """Delete a specific ban by its ID.

        Parameters
        ----------
        ban_id : int
            The ID of the ban to delete.


        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        await self.http.delete_ban(ban_id)

    async def list_bans(
        self,
        *,
        banlist_id: str | None = None,
        exempt: bool | None = None,
        expired: bool | None = None,
        organization_id: int | None = None,
        player_id: int | None = None,
        search: str | None = None,
        server_id: int | None = None,
        user_ids: list[int] | None = None,
        page_size: int | None = None,
    ) -> list[Ban]:
        """List bans with optional filters for organization and server.

        Parameters
        ----------
        organization_id : int | None
            The ID of the organization to filter by.
        server_id : int | None
            The ID of the server to filter by.

        Returns
        -------
        Any
            The response from the API containing the list of bans.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        resp = await self.http.list_bans(
            banlist_id=banlist_id,
            exempt=exempt,
            expired=expired,
            organization_id=organization_id,
            player_id=player_id,
            search=search,
            server_id=server_id,
            user_ids=user_ids,
            page_size=page_size,
        )
        return [Ban.model_validate(ban) for ban in resp["data"]]

    async def update_ban(
        self,
        ban_id: int | None = None,
        *,
        reason: str | None = None,
        note: str | None = None,
        identifiers: list[str | dict[str, Any]] | None = None,
        expires: str | None = None,
        org_wide: bool = True,
        auto_add_enabled: bool = True,
        native_enabled: bool = True,
    ) -> Ban:
        """Update a specific ban by its ID.

        Parameters
        ----------
        ban_id : int
            The ID of the ban to update.
        **kwargs : Any
            The fields to update.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        resp = await self.http.update_ban(
            ban_id=ban_id,
            reason=reason,
            note=note,
            identifiers=identifiers,
            expires=expires,
            org_wide=org_wide,
            auto_add_enabled=auto_add_enabled,
            native_enabled=native_enabled,
        )
        return Ban.model_validate(resp["data"])

    async def ban_info(self, ban_id: int) -> Ban:
        """Get information about a specific ban."""
        resp = await self.http.ban_info(ban_id)
        return Ban.model_validate(resp["data"])

    async def create_banlist_exemption(
        self,
        ban_id: int,
        organization_id: int,
        *,
        reason: str | None = None,
    ) -> BanListExemption:
        """Create a banlist Exemption."""
        resp = await self.http.create_banlist_exemption(
            ban_id=ban_id,
            organization_id=organization_id,
            reason=reason,
        )
        return BanListExemption.model_validate(resp["data"])

    async def read_banlist_exemption(
        self,
        ban_id: int,
        ban_exemption_id: int,
    ) -> dict[str, Any]:
        """Read a specific banlist exemption by its ID.

        Parameters
        ----------
        ban_id : int
            The ID of the ban to read.
        ban_exemption_id : int
            The ID of the ban exemption to read.

        Returns
        -------
        dict[str, Any]
            The response from the API containing the banlist exemption.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        resp = await self.http.read_banlist_exemption(
            ban_id=ban_id,
            ban_exemption_id=ban_exemption_id,
        )
        return BanListExemption.model_validate(resp["data"])

    async def list_banlist_exemptions(self, ban_id: int) -> dict[str, Any]:
        """List all banlist exemptions for a specific ban.

        Parameters
        ----------
        ban_id : int
            The ID of the ban to list exemptions for.

        Returns
        -------
        dict[str, Any]
            The response from the API containing the list of banlist exemptions.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        resp = await self.http.list_banlist_exemptions(ban_id=ban_id)
        return [BanListExemption.model_validate(exemption) for exemption in resp["data"]]

    async def update_banlist_exemption(
        self,
        ban_id: int,
        *,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Update a specific banlist exemption by its ID.

        Parameters
        ----------
        ban_id : int
            The ID of the ban to update.
        ban_exemption_id : int
            The ID of the ban exemption to update.
        reason : str | None
            The new reason for the ban exemption.

        Returns
        -------
        dict[str, Any]
            The response from the API containing the updated banlist exemption.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        resp = await self.http.update_banlist_exemption(
            ban_id=ban_id,
            reason=reason,
        )
        return BanListExemption.model_validate(resp["data"])

    async def delete_banlist_exemption(
        self,
        ban_id: int,
    ) -> None:
        """Delete a specific banlist exemption by its ID.

        Parameters
        ----------
        ban_id : int
            The ID of the ban to delete the exemption from.
        ban_exemption_id : int
            The ID of the ban exemption to delete.

        Returns
        -------
        dict[str, Any]
            The response from the API confirming the deletion.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        await self.http.delete_banlist_exemption(
            ban_id=ban_id,
        )

    # ----------------------------- Ban Lists ----------------------------- #

    async def create_banlist(
        self,
        *,
        name: str,
        action: Literal["none", "log", "kick"],
        organization_id: int,
        owner_id: int,
        default_identifiers: list[str] | None = None,
        default_reasons: list[str] | None = None,
        default_auto_add_enabled: bool = True,
        default_native_enabled: bool | None = None,
        native_ban_ttl: int | None = None,
        native_ban_temp_max_expires: int | None = None,
        native_ban_perm_max_expires: int | None = None,
    ) -> BanList:
        """Create a ban list."""
        resp = await self.http.create_banlist(
            name=name,
            action=action,
            organization_id=organization_id,
            owner_id=owner_id,
            default_identifiers=default_identifiers,
            default_reasons=default_reasons,
            default_auto_add_enabled=default_auto_add_enabled,
            default_native_enabled=default_native_enabled,
            native_ban_ttl=native_ban_ttl,
            native_ban_temp_max_expires=native_ban_temp_max_expires,
            native_ban_perm_max_expires=native_ban_perm_max_expires,
        )
        return BanList.model_validate(resp["data"])

    async def create_banlist_from_invite(
        self,
        *,
        code: str,
        action: Literal["none", "log", "kick"],
        organization_id: int,
        owner_id: int,
        default_identifiers: list[str] | None = None,
        default_reasons: list[str] | None = None,
        default_auto_add_enabled: bool = True,
        default_native_enabled: bool | None = None,
        native_ban_ttl: int | None = None,
        native_ban_temp_max_expires: int | None = None,
        native_ban_perm_max_expires: int | None = None,
    ) -> BanList:
        """Accept a ban list invite and subscribe."""
        resp = await self.http.create_banlist_from_invite(
            code=code,
            action=action,
            organization_id=organization_id,
            owner_id=owner_id,
            default_identifiers=default_identifiers,
            default_reasons=default_reasons,
            default_auto_add_enabled=default_auto_add_enabled,
            default_native_enabled=default_native_enabled,
            native_ban_ttl=native_ban_ttl,
            native_ban_temp_max_expires=native_ban_temp_max_expires,
            native_ban_perm_max_expires=native_ban_perm_max_expires,
        )
        return BanList.model_validate(resp["data"])

    async def list_banlists(
        self,
        *,
        include: str | None = None,
        page_size: int | None = None,
    ) -> list[BanList]:
        """List ban lists owned or subscribed to."""
        resp = await self.http.list_banlists(include=include, page_size=page_size)
        return [BanList.model_validate(b) for b in resp["data"]]

    async def get_banlist(
        self,
        banlist_id: str,
        *,
        include: str | None = None,
    ) -> BanList:
        """Get a ban list."""
        resp = await self.http.get_banlist(banlist_id, include=include)
        return BanList.model_validate(resp["data"])

    async def update_banlist(
        self,
        banlist_id: str,
        *,
        name: str | None = None,
        action: Literal["none", "log", "kick"] | None = None,
        default_identifiers: list[str] | None = None,
        default_reasons: list[str] | None = None,
        default_auto_add_enabled: bool | None = None,
        default_native_enabled: bool | None = None,
        native_ban_ttl: int | None = None,
        native_ban_temp_max_expires: int | None = None,
        native_ban_perm_max_expires: int | None = None,
    ) -> BanList:
        """Update a ban list."""
        resp = await self.http.update_banlist(
            banlist_id=banlist_id,
            name=name,
            action=action,
            default_identifiers=default_identifiers,
            default_reasons=default_reasons,
            default_auto_add_enabled=default_auto_add_enabled,
            default_native_enabled=default_native_enabled,
            native_ban_ttl=native_ban_ttl,
            native_ban_temp_max_expires=native_ban_temp_max_expires,
            native_ban_perm_max_expires=native_ban_perm_max_expires,
        )
        return BanList.model_validate(resp["data"])

    async def list_banlist_organizations(
        self,
        banlist_id: str,
        *,
        include: str | None = None,
        page_size: int | None = None,
    ) -> list[Organization]:
        """List organizations subscribed to a ban list."""
        resp = await self.http.list_banlist_organizations(
            banlist_id=banlist_id,
            include=include,
            page_size=page_size,
        )
        return [Organization.model_validate(o) for o in resp["data"]]

    async def get_banlist_subscription(
        self,
        banlist_id: str,
        organization_id: int,
        *,
        include: str | None = None,
    ) -> BanList:
        """Get an organization's ban list subscription."""
        resp = await self.http.get_banlist_subscription(
            banlist_id=banlist_id,
            organization_id=organization_id,
            include=include,
        )
        return BanList.model_validate(resp["data"])

    async def update_banlist_subscription(
        self,
        banlist_id: str,
        organization_id: int,
        *,
        perm_manage: bool | None = None,
        perm_create: bool | None = None,
        perm_update: bool | None = None,
        perm_delete: bool | None = None,
    ) -> BanList:
        """Update an organization's ban list subscription permissions."""
        resp = await self.http.update_banlist_subscription(
            banlist_id=banlist_id,
            organization_id=organization_id,
            perm_manage=perm_manage,
            perm_create=perm_create,
            perm_update=perm_update,
            perm_delete=perm_delete,
        )
        return BanList.model_validate(resp["data"])

    async def unsubscribe_banlist(self, banlist_id: str, organization_id: int) -> None:
        """Unsubscribe an organization from a ban list."""
        await self.http.unsubscribe_banlist(banlist_id, organization_id)

    # -------------------------- Ban List Invites ------------------------- #

    async def create_banlist_invite(
        self,
        banlist_id: str,
        *,
        limit: int | None = None,
        perm_manage: bool | None = None,
        perm_create: bool | None = None,
        perm_update: bool | None = None,
        perm_delete: bool | None = None,
        uses: int | None = None,
        organization_id: int | None = None,
    ) -> BanListInvite:
        """Create a ban list invite."""
        resp = await self.http.create_banlist_invite(
            banlist_id=banlist_id,
            limit=limit,
            perm_manage=perm_manage,
            perm_create=perm_create,
            perm_update=perm_update,
            perm_delete=perm_delete,
            uses=uses,
            organization_id=organization_id,
        )
        return BanListInvite.model_validate(resp["data"])

    async def list_banlist_invites(
        self,
        banlist_id: str,
        *,
        include: str | None = None,
    ) -> list[BanListInvite]:
        """List invites for a ban list."""
        resp = await self.http.list_banlist_invites(
            banlist_id=banlist_id,
            include=include,
        )
        return [BanListInvite.model_validate(i) for i in resp["data"]]

    async def get_banlist_invite(
        self,
        invite_id: str,
        *,
        include: str | None = None,
    ) -> BanListInvite:
        """Get a ban list invite."""
        resp = await self.http.get_banlist_invite(invite_id=invite_id, include=include)
        return BanListInvite.model_validate(resp["data"])

    async def delete_banlist_invite(self, invite_id: str) -> None:
        """Delete a ban list invite."""
        await self.http.delete_banlist_invite(invite_id)

    # ----------------------------- Native Bans ---------------------------- #

    async def list_native_bans(
        self,
        *,
        ban_id: int | None = None,
        server_id: int | None = None,
        include: str | None = None,
        page_size: int | None = None,
        sort: str | None = None,
    ) -> list[NativeBan]:
        """List native (game) bans."""
        resp = await self.http.list_native_bans(
            ban_id=ban_id,
            server_id=server_id,
            include=include,
            page_size=page_size,
            sort=sort,
        )
        return [NativeBan.model_validate(nb) for nb in resp["data"]]

    # --------------------------- Commands Activity ------------------------ #

    async def list_command_stats(
        self,
        organization_id: int,
        *,
        commands: list[str] | None = None,
        servers: list[int] | None = None,
        users: list[int] | None = None,
        timestamp_range: str | None = None,
        summary: bool | None = None,
    ) -> list[CommandsActivity]:
        """List command activity statistics."""
        resp = await self.http.list_command_stats(
            organization_id=organization_id,
            commands=commands,
            servers=servers,
            users=users,
            timestamp_range=timestamp_range,
            summary=summary,
        )
        return [CommandsActivity.model_validate(c) for c in resp["data"]]

    # -------------------------------- Coplay ------------------------------ #

    async def list_coplay(
        self,
        player_id: int,
        *,
        period: str,
        players: list[int] | None = None,
        servers: list[int] | None = None,
        organizations: list[int] | None = None,
        page_size: int | None = None,
    ) -> list[Coplay]:
        """List coplay entries for a player."""
        resp = await self.http.list_coplay(
            player_id=player_id,
            period=period,
            players=players,
            servers=servers,
            organizations=organizations,
            page_size=page_size,
        )
        return [Coplay.model_validate(cp) for cp in resp["data"]]

    # ------------------------------ Player Flags -------------------------- #

    async def create_player_flag(
        self,
        *,
        organization_id: int,
        name: str,
        color: str | None = None,
        icon: str | None = None,
        description: str | None = None,
    ) -> PlayerFlag:
        """Create a player flag."""
        resp = await self.http.create_player_flag(
            organization_id=organization_id,
            name=name,
            color=color,
            icon=icon,
            description=description,
        )
        return PlayerFlag.model_validate(resp["data"])

    async def list_player_flags(
        self,
        *,
        personal: bool | None = None,
        include: str | None = None,
        page_size: int | None = None,
    ) -> list[PlayerFlag]:
        """List player flags."""
        resp = await self.http.list_player_flags(
            personal=personal,
            include=include,
            page_size=page_size,
        )
        return [PlayerFlag.model_validate(f) for f in resp["data"]]

    async def update_player_flag(
        self,
        flag_id: str,
        *,
        name: str | None = None,
        color: str | None = None,
        icon: str | None = None,
        description: str | None = None,
    ) -> PlayerFlag:
        """Update a player flag."""
        resp = await self.http.update_player_flag(
            flag_id=flag_id,
            name=name,
            color=color,
            icon=icon,
            description=description,
        )
        return PlayerFlag.model_validate(resp["data"])

    async def delete_player_flag(self, flag_id: str) -> None:
        """Delete a player flag."""
        await self.http.delete_player_flag(flag_id)

    async def list_player_flag_assignments(
        self,
        player_id: int,
        *,
        include: str | None = None,
        page_size: int | None = None,
    ) -> list[FlagPlayer]:
        """List player flag assignments for a player."""
        resp = await self.http.list_player_flag_assignments(
            player_id=player_id,
            include=include,
            page_size=page_size,
        )
        return [FlagPlayer.model_validate(a) for a in resp["data"]]

    async def remove_player_flag_assignment(
        self,
        player_id: int,
        player_flag_id: str,
    ) -> None:
        """Remove a player flag assignment."""
        await self.http.remove_player_flag_assignment(player_id, player_flag_id)

    # --------------------------------- Games ------------------------------ #

    async def list_games(self, *, page_size: int | None = None) -> list[Game]:
        """List games."""
        resp = await self.http.list_games(page_size=page_size)
        return [Game.model_validate(g) for g in resp["data"]]

    async def get_game(self, game_id: str) -> Game:
        """Get a game."""
        resp = await self.http.get_game(game_id)
        return Game.model_validate(resp["data"])

    # ---------------------------- Game Features --------------------------- #

    async def list_game_features(
        self,
        *,
        game: str | None = None,
        page_size: int | None = None,
    ) -> list[GameFeatures]:
        """List game features."""
        resp = await self.http.list_game_features(game=game, page_size=page_size)
        return [GameFeatures.model_validate(f) for f in resp["data"]]

    async def list_game_feature_options(
        self,
        feature_id: str,
        *,
        page_size: int | None = None,
        sort: str | None = None,
    ) -> list[GameFeatureOptions]:
        """List game feature options."""
        resp = await self.http.list_game_feature_options(
            feature_id=feature_id,
            page_size=page_size,
            sort=sort,
        )
        return [GameFeatureOptions.model_validate(o) for o in resp["data"]]

    # ------------------------------ Leaderboards ------------------------- #

    async def get_leaderboard(
        self,
        server_id: int,
        *,
        period: str,
        player_id: int | None = None,
        leaderboard: str = "time",
        page_size: int | None = None,
        offset: int | None = None,
    ) -> list[Leaderboard]:
        """Get a server leaderboard."""
        resp = await self.http.get_leaderboard(
            server_id=server_id,
            period=period,
            player_id=player_id,
            leaderboard=leaderboard,
            page_size=page_size,
            offset=offset,
        )
        return [Leaderboard.model_validate(lb) for lb in resp["data"]]

    # ---------------------------- Organization Stats --------------------- #

    async def get_organization_player_stats(
        self,
        organization_id: int,
        *,
        range_: str,
        game: str | None = None,
        group: str | None = None,
    ) -> OrganizationStats:
        """Get organization player stats."""
        resp = await self.http.get_organization_player_stats(
            organization_id=organization_id,
            range_=range_,
            game=game,
            group=group,
        )
        return OrganizationStats.model_validate(resp["data"])

    # -------------------------------- Players ----------------------------- #

    async def list_players(
        self,
        *,
        search: str | None = None,
        servers: list[int] | None = None,
        organizations: list[int] | None = None,
        game: str | None = None,
        page_size: int | None = None,
        sort: str | None = None,
        online: bool | None = None,
    ) -> list[Player]:
        """List players."""
        resp = await self.http.list_players(
            search=search,
            servers=servers,
            organizations=organizations,
            game=game,
            page_size=page_size,
            sort=sort,
            online=online,
        )
        return [Player.model_validate(p) for p in resp["data"]]

    async def get_player(self, player_id: int, *, include: str | None = None) -> Player:
        """Get a player."""
        resp = await self.http.get_player(player_id, include=include)
        included = resp.get("included")
        return Player.model_validate({**resp["data"], "included": included})

    async def match_players(self, identifiers: list[dict[str, str]]) -> list[Player]:
        """Match players (slow)."""
        resp = await self.http.match_players(identifiers)
        return [Player.model_validate(p) for p in resp["data"]]

    async def quick_match_players(
        self,
        identifiers: list[dict[str, str]],
    ) -> list[QuickMatchIdentifier]:
        """Quick match players by identifiers.

        This API method is rate limited to 10 requests per second.
        Enterprise users have a higher rate limit of 30 requests per second.

        Parameters
        ----------
        identifiers : list[dict[str, str]]
            A list of identifier dicts with 'type' and 'identifier' keys.
            Example: [{"type": "steamID", "identifier": "76561197960265720"}]

        Returns
        -------
        list[QuickMatchIdentifier]
            A list of matched identifiers with player relationships.
        """
        resp = await self.http.quick_match_players(identifiers)
        return [QuickMatchIdentifier.model_validate(p) for p in resp["data"]]

    async def player_session_history(
        self,
        player_id: int,
        *,
        servers: list[int] | None = None,
        organizations: list[int] | None = None,
        page_size: int | None = None,
        include: str | None = None,
    ) -> list[Session]:
        """Get a player's session history."""
        resp = await self.http.player_session_history(
            player_id=player_id,
            servers=servers,
            organizations=organizations,
            page_size=page_size,
            include=include,
        )
        return [Session.model_validate(s) for s in resp["data"]]

    async def related_identifiers(
        self,
        player_id: int,
        *,
        match_identifiers: list[str] | None = None,
        identifiers: list[str] | None = None,
        page_size: int | None = None,
        include: str | None = None,
    ) -> list[RelatedPlayerIdentifier]:
        """Get related identifiers."""
        resp = await self.http.related_identifiers(
            player_id=player_id,
            match_identifiers=match_identifiers,
            identifiers=identifiers,
            page_size=page_size,
            include=include,
        )
        return [RelatedPlayerIdentifier.model_validate(r) for r in resp["data"]]

    # ----------------------------- Player Queries ------------------------- #

    async def list_player_queries(
        self,
        *,
        organizations: list[int] | None = None,
        ids: list[str] | None = None,
        sort: str | None = None,
        page_size: int | None = None,
    ) -> list[PlayerQuery]:
        """List player queries."""
        resp = await self.http.list_player_queries(
            organizations=organizations,
            ids=ids,
            sort=sort,
            page_size=page_size,
        )
        return [PlayerQuery.model_validate(q) for q in resp["data"]]

    async def get_player_query(self, query_id: str) -> PlayerQuery:
        """Get a player query."""
        resp = await self.http.get_player_query(query_id)
        return PlayerQuery.model_validate(resp["data"])

    async def create_player_query(
        self,
        organization_id: int,
        *,
        query_name: str,
        conditions: list[dict[str, Any]],
    ) -> PlayerQuery:
        """Create a player query."""
        resp = await self.http.create_player_query(
            organization_id=organization_id,
            query_name=query_name,
            conditions=conditions,
        )
        return PlayerQuery.model_validate(resp["data"])

    async def update_player_query(
        self,
        query_id: str,
        *,
        query_name: str | None = None,
        conditions: list[dict[str, Any]] | None = None,
    ) -> PlayerQuery:
        """Update a player query."""
        resp = await self.http.update_player_query(
            query_id=query_id,
            query_name=query_name,
            conditions=conditions,
        )
        return PlayerQuery.model_validate(resp["data"])

    async def delete_player_query(self, query_id: str) -> None:
        """Delete a player query."""
        await self.http.delete_player_query(query_id)

    async def run_player_query(
        self,
        player_id: int,
        query_id: str,
        *,
        identifiers: list[str] | None = None,
        include: str | None = None,
        page_size: int | None = None,
        offset: int | None = None,
    ) -> list[PlayerQueryResult]:
        """Run a saved player query for a player."""
        resp = await self.http.run_player_query(
            player_id=player_id,
            query_id=query_id,
            identifiers=identifiers,
            include=include,
            page_size=page_size,
            offset=offset,
        )
        return [PlayerQueryResult.model_validate(r) for r in resp["data"]]

    # ----------------------------- Reserved Slots ------------------------- #

    async def create_reserved_slot(
        self,
        *,
        player_id: int,
        organization_id: int,
        server_ids: list[int],
        identifiers: list[str | dict[str, Any]] | None = None,
        expires: str | None = None,
    ) -> ReservedSlot:
        """Create a reserved slot."""
        resp = await self.http.create_reserved_slot(
            player_id=player_id,
            organization_id=organization_id,
            server_ids=server_ids,
            identifiers=identifiers,
            expires=expires,
        )
        return ReservedSlot.model_validate(resp["data"])

    async def get_reserved_slot(
        self,
        slot_id: str,
        *,
        include: str | None = None,
    ) -> ReservedSlot:
        """Get a reserved slot."""
        resp = await self.http.get_reserved_slot(slot_id, include=include)
        return ReservedSlot.model_validate(resp["data"])

    async def list_reserved_slots(
        self,
        *,
        organization_id: int | None = None,
        player_id: int | None = None,
        server_id: int | None = None,
        search: str | None = None,
        expired: bool | None = None,
        include: str | None = None,
        page_size: int | None = None,
    ) -> list[ReservedSlot]:
        """List reserved slots."""
        resp = await self.http.list_reserved_slots(
            organization_id=organization_id,
            player_id=player_id,
            server_id=server_id,
            search=search,
            expired=expired,
            include=include,
            page_size=page_size,
        )
        return [ReservedSlot.model_validate(rs) for rs in resp["data"]]

    async def update_reserved_slot(
        self,
        slot_id: str,
        *,
        identifiers: list[str | dict[str, Any]] | None = None,
        expires: str | None = None,
        server_ids: list[int] | None = None,
    ) -> ReservedSlot:
        """Update a reserved slot."""
        resp = await self.http.update_reserved_slot(
            slot_id=slot_id,
            identifiers=identifiers,
            expires=expires,
            server_ids=server_ids,
        )
        return ReservedSlot.model_validate(resp["data"])

    async def delete_reserved_slot(self, slot_id: str) -> None:
        """Delete a reserved slot."""
        await self.http.delete_reserved_slot(slot_id)

    # -------------------------------- Servers ----------------------------- #

    async def list_servers(
        self,
        *,
        search: str | None = None,
        game: str | None = None,
        status: str | None = None,
        countries: list[str] | None = None,
        page_size: int | None = None,
        sort: str | None = None,
    ) -> list[Server]:
        """List servers."""
        resp = await self.http.list_servers(
            search=search,
            game=game,
            status=status,
            countries=countries,
            page_size=page_size,
            sort=sort,
        )
        return [Server.model_validate(s) for s in resp["data"]]

    async def get_server(self, server_id: int, *, include: str | None = None) -> Server:
        """Get a server."""
        resp = await self.http.get_server(server_id, include=include)
        return Server.model_validate(resp["data"])

    async def server_sessions(
        self,
        server_id: int,
        *,
        start: str | None = None,
        stop: str | None = None,
        at: str | None = None,
        include: str | None = None,
    ) -> list[Session]:
        """List sessions for a server."""
        resp = await self.http.server_sessions(
            server_id=server_id,
            start=start,
            stop=stop,
            at=at,
            include=include,
        )
        return [Session.model_validate(s) for s in resp["data"]]

    async def server_outages(
        self,
        server_id: int,
        *,
        range_: str | None = None,
        include: str | None = None,
        page_size: int | None = None,
    ) -> Any:
        """Return raw outage data (no model)."""
        return await self.http.server_outages(
            server_id=server_id,
            range_=range_,
            include=include,
            page_size=page_size,
        )

    # -------------------------------- Sessions ---------------------------- #

    async def list_sessions(
        self,
        *,
        servers: list[int] | None = None,
        games: list[str] | None = None,
        organizations: list[int] | None = None,
        players: list[int] | None = None,
        identifiers: list[str] | None = None,
        range_: str | None = None,
        at: str | None = None,
        include: str | None = None,
        page_size: int | None = None,
    ) -> list[Session]:
        """List sessions."""
        resp = await self.http.list_sessions(
            servers=servers,
            games=games,
            organizations=organizations,
            players=players,
            identifiers=identifiers,
            range_=range_,
            at=at,
            include=include,
            page_size=page_size,
        )
        return [Session.model_validate(s) for s in resp["data"]]

    async def session_coplay(
        self,
        session_id: str,
        *,
        page_size: int | None = None,
        include: str | None = None,
    ) -> list[Coplay]:
        """Get coplay data for a session."""
        resp = await self.http.session_coplay(
            session_id=session_id,
            page_size=page_size,
            include=include,
        )
        return [Coplay.model_validate(c) for c in resp["data"]]

    # --------------------------------- Users ------------------------------ #

    async def get_user(self, user_id: int) -> User:
        """Get a user."""
        resp = await self.http.get_user(user_id)
        return User.model_validate(resp["data"])

    # -------------------------------- Player Notes ----------------------- #

    async def list_player_notes(
        self,
        player_id: int,
        *,
        expired: bool | None = None,
        organizations: list[int] | None = None,
        personal: bool | None = None,
        search: str | None = None,
        users: list[int] | None = None,
        include: str | None = None,
        page_size: int | None = None,
        page_key: str | None = None,
        page_rel: Literal["next", "prev"] | None = None,
    ) -> list[Note]:
        """List player notes."""
        resp = await self.http.list_player_notes(
            player_id=player_id,
            expired=expired,
            organizations=organizations,
            personal=personal,
            search=search,
            users=users,
            include=include,
            page_size=page_size,
            page_key=page_key,
            page_rel=page_rel,
        )
        return [Note.model_validate(n) for n in resp["data"]]

    async def get_player_note(self, player_id: int, note_id: str) -> Note:
        """Get a player note."""
        resp = await self.http.get_player_note(player_id, note_id)
        return Note.model_validate(resp["data"])

    async def create_player_note(
        self,
        player_id: int,
        *,
        note: str,
        shared: bool,
        expires_at: str | None = None,
        clearance_level: int | None = None,
        organization_id: int | None = None,
        trigger_id: str | None = None,
    ) -> Note:
        """Create a player note."""
        resp = await self.http.create_player_note(
            player_id=player_id,
            note=note,
            shared=shared,
            expires_at=expires_at,
            clearance_level=clearance_level,
            organization_id=organization_id,
            trigger_id=trigger_id,
        )
        return Note.model_validate(resp["data"])

    async def update_player_note(
        self,
        player_id: int,
        note_id: str,
        *,
        note: str | None = None,
        shared: bool | None = None,
        expires_at: str | None = None,
        clearance_level: int | None = None,
    ) -> Note:
        """Update a player note."""
        resp = await self.http.update_player_note(
            player_id=player_id,
            note_id=note_id,
            note=note,
            shared=shared,
            expires_at=expires_at,
            clearance_level=clearance_level,
        )
        return Note.model_validate(resp["data"])

    async def delete_player_note(self, player_id: int, note_id: str) -> None:
        """Delete a player note."""
        await self.http.delete_player_note(player_id, note_id)

    # -------------------------- Organization Friends ----------------------- #

    async def list_organization_friends(
        self,
        organization_id: int,
        *,
        include: str | None = None,
        page_size: int | None = None,
    ) -> list[OrganizationFriend]:
        """List organization friends."""
        resp = await self.http.list_organization_friends(
            organization_id=organization_id,
            include=include,
            page_size=page_size,
        )
        return [OrganizationFriend.model_validate(f) for f in resp["data"]]

    async def get_organization_friend(
        self,
        organization_id: int,
        friend_id: int,
        *,
        include: str | None = None,
    ) -> OrganizationFriend:
        """Get a specific organization friend."""
        resp = await self.http.get_organization_friend(
            organization_id=organization_id,
            friend_id=friend_id,
            include=include,
        )
        return OrganizationFriend.model_validate(resp["data"])

    async def create_organization_friend(
        self,
        organization_id: int,
        friend_id: int,
        *,
        identifiers: list[str] | None = None,
        notes: bool = False,
        player_flags: list[str] | None = None,
    ) -> OrganizationFriend:
        """Create an organization friend request."""
        resp = await self.http.create_organization_friend(
            organization_id=organization_id,
            friend_id=friend_id,
            identifiers=identifiers,
            notes=notes,
            player_flags=player_flags,
        )
        return OrganizationFriend.model_validate(resp["data"])

    async def update_organization_friend(
        self,
        organization_id: int,
        friend_id: int,
        *,
        identifiers: list[str] | None = None,
        notes: bool | None = None,
        player_flags: list[str] | None = None,
    ) -> OrganizationFriend:
        """Update an organization friend."""
        resp = await self.http.update_organization_friend(
            organization_id=organization_id,
            friend_id=friend_id,
            identifiers=identifiers,
            notes=notes,
            player_flags=player_flags,
        )
        return OrganizationFriend.model_validate(resp["data"])

    async def delete_organization_friend(
        self,
        organization_id: int,
        friend_id: int,
    ) -> None:
        """Delete an organization friend."""
        await self.http.delete_organization_friend(organization_id, friend_id)

    async def bulk_delete_organization_friends(
        self,
        organization_id: int,
        friend_ids: list[int],
    ) -> None:
        """Bulk delete organization friends."""
        await self.http.bulk_delete_organization_friends(organization_id, friend_ids)

    # ------------------------ Additional Server Methods --------------------- #

    async def server_downtime(
        self,
        server_id: int,
        *,
        start: str,
        stop: str,
        include: str | None = None,
        page_size: int | None = None,
    ) -> Any:
        """Get server downtime history."""
        return await self.http.server_downtime(
            server_id=server_id,
            start=start,
            stop=stop,
            include=include,
            page_size=page_size,
        )

    async def server_first_time_history(
        self,
        server_id: int,
        *,
        start: str,
        stop: str,
    ) -> Any:
        """Get server first-time player history."""
        return await self.http.server_first_time_history(
            server_id=server_id,
            start=start,
            stop=stop,
        )

    async def server_player_count_history(
        self,
        server_id: int,
        *,
        start: str,
        stop: str,
        resolution: Literal["raw", "30", "60", "1440"] | None = None,
    ) -> Any:
        """Get server player count history."""
        return await self.http.server_player_count_history(
            server_id=server_id,
            start=start,
            stop=stop,
            resolution=resolution,
        )

    async def server_rank_history(
        self,
        server_id: int,
        *,
        start: str,
        stop: str,
    ) -> Any:
        """Get server rank history."""
        return await self.http.server_rank_history(
            server_id=server_id,
            start=start,
            stop=stop,
        )

    async def server_group_rank_history(
        self,
        server_id: int,
        *,
        start: str,
        stop: str,
    ) -> Any:
        """Get server group rank history."""
        return await self.http.server_group_rank_history(
            server_id=server_id,
            start=start,
            stop=stop,
        )

    async def server_time_played_history(
        self,
        server_id: int,
        *,
        start: str,
        stop: str,
    ) -> Any:
        """Get server time played history."""
        return await self.http.server_time_played_history(
            server_id=server_id,
            start=start,
            stop=stop,
        )

    async def server_unique_player_history(
        self,
        server_id: int,
        *,
        start: str,
        stop: str,
    ) -> Any:
        """Get server unique player history."""
        return await self.http.server_unique_player_history(
            server_id=server_id,
            start=start,
            stop=stop,
        )

    async def create_server(
        self,
        *,
        game: str,
        ip: str,
        port: int,
        port_query: int,
        organization_id: int,
    ) -> Server:
        """Create a server."""
        resp = await self.http.create_server(
            game=game,
            ip=ip,
            port=port,
            port_query=port_query,
            organization_id=organization_id,
        )
        return Server.model_validate(resp["data"])

    async def update_server(
        self,
        server_id: int,
        *,
        metadata: dict[str, Any] | None = None,
        port_query: int | None = None,
        default_ban_list_id: str | None = None,
        server_group_id: str | None = None,
    ) -> Server:
        """Update a server."""
        resp = await self.http.update_server(
            server_id=server_id,
            metadata=metadata,
            port_query=port_query,
            default_ban_list_id=default_ban_list_id,
            server_group_id=server_group_id,
        )
        return Server.model_validate(resp["data"])

    async def enable_server_rcon(
        self,
        server_id: int,
        *,
        password: str,
        port: int | None = None,
        ip: str | None = None,
    ) -> Server:
        """Enable RCON for a server."""
        resp = await self.http.enable_server_rcon(
            server_id=server_id,
            password=password,
            port=port,
            ip=ip,
        )
        return Server.model_validate(resp["data"])

    async def delete_server_rcon(self, server_id: int) -> None:
        """Delete RCON configuration for a server."""
        await self.http.delete_server_rcon(server_id)

    async def disconnect_server_rcon(self, server_id: int) -> None:
        """Disconnect RCON for a server."""
        await self.http.disconnect_server_rcon(server_id)

    async def connect_server_rcon(self, server_id: int) -> None:
        """Connect RCON for a server."""
        await self.http.connect_server_rcon(server_id)

    async def force_update_server(self, server_id: int) -> Server:
        """Force update a server."""
        resp = await self.http.force_update_server(server_id)
        return Server.model_validate(resp["data"])

    # ------------------------- Additional Player Methods -------------------- #

    async def player_time_played_history(
        self,
        player_id: int,
        server_id: int,
        *,
        start: str,
        stop: str,
    ) -> Any:
        """Get a player's time played history for a server."""
        return await self.http.player_time_played_history(
            player_id=player_id,
            server_id=server_id,
            start=start,
            stop=stop,
        )

    async def get_player_server_info(
        self,
        player_id: int,
        server_id: int,
    ) -> Player:
        """Get player information for a specific server."""
        resp = await self.http.get_player_server_info(
            player_id=player_id,
            server_id=server_id,
        )
        return Player.model_validate(resp["data"])

    # ------------------------- Additional Flag Methods ---------------------- #

    async def get_player_flag(
        self,
        flag_id: str,
        *,
        include: str | None = None,
    ) -> PlayerFlag:
        """Get a specific player flag."""
        resp = await self.http.get_player_flag(flag_id, include=include)
        return PlayerFlag.model_validate(resp["data"])

    async def add_player_flag_assignment(
        self,
        player_id: int,
        player_flag_id: str,
    ) -> FlagPlayer:
        """Add a flag to a player."""
        resp = await self.http.add_player_flag_assignment(player_id, player_flag_id)
        return FlagPlayer.model_validate(resp["data"])

    # ----------------------- Additional Native Ban Methods ------------------ #

    async def force_update_native_ban(self, native_ban_id: str) -> NativeBan:
        """Force update a native ban."""
        resp = await self.http.force_update_native_ban(native_ban_id)
        return NativeBan.model_validate(resp["data"])

    # ------------------------ Additional Session Methods -------------------- #

    async def get_session(
        self,
        session_id: str,
        *,
        include: str | None = None,
    ) -> Session:
        """Get a specific session."""
        resp = await self.http.get_session(session_id, include=include)
        return Session.model_validate(resp["data"])

    # --------------------- Additional Player Query Methods ------------------ #

    async def run_custom_player_query(
        self,
        player_id: int,
        *,
        conditions: list[dict[str, Any]],
        identifiers: list[str] | None = None,
        include: str | None = None,
        page_size: int | None = None,
        offset: int | None = None,
    ) -> list[PlayerQueryResult]:
        """Run a custom related player query (not saved) for a player."""
        resp = await self.http.run_custom_player_query(
            player_id=player_id,
            conditions=conditions,
            identifiers=identifiers,
            include=include,
            page_size=page_size,
            offset=offset,
        )
        return [PlayerQueryResult.model_validate(r) for r in resp["data"]]
