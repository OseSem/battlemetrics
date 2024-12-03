from __future__ import annotations

from typing import TYPE_CHECKING

from . import utils
from .types.banlist import BanList as BanListPayload
from .types.banlist import BanListAttributes, BanListRelationships

if TYPE_CHECKING:
    from typing import Any, Self

    from .http import IDENTIFIERS, HTTPClient
    from .types.banlist import BanListInvite


__all__ = ("BanList",)


class BanList:
    """Represents a banlist."""

    def __init__(self, data: BanListPayload, *, http: HTTPClient) -> None:
        self._http = http
        self._data: BanListPayload = BanListPayload(**data)
        self._attributes: BanListAttributes = data.get("attributes")
        self._relationships: BanListRelationships = (
            utils.format_relationships(  # type: ignore [reportAttributeAccessIssue]
                data.get("relationships"),
            )
        )

    def __repr__(self) -> str:
        """Return the representation of the banlist."""
        return f"<BanList id={self.id!r}>"

    @property
    def id(self) -> str:
        """The ID of the banlist."""
        return self._data.get("id")

    @property
    def name(self) -> str:
        """The name of the banlist."""
        return self._attributes.get("name")

    @property
    def action(self) -> str:
        """The action of the banlist."""
        return self._attributes.get("action")

    @property
    def perm_manage(self) -> bool:
        """Whether the banlist has permission to manage."""
        return self._attributes.get("permManage")

    @property
    def perm_create(self) -> bool:
        """Whether the banlist has permission to create."""
        return self._attributes.get("permCreate")

    @property
    def perm_update(self) -> bool:
        """Whether the banlist has permission to update."""
        return self._attributes.get("permUpdate")

    @property
    def perm_delete(self) -> bool:
        """Whether the banlist has permission to delete."""
        return self._attributes.get("permDelete")

    @property
    def default_identifiers(self) -> list[str]:
        """The default identifiers of the banlist."""
        return self._attributes.get("defaultIdentifiers")

    @property
    def default_reasons(self) -> list[str]:
        """The default reasons of the banlist."""
        return self._attributes.get("defaultReasons")

    @property
    def default_auto_add_enabled(self) -> bool:
        """Whether the default auto add is enabled."""
        return self._attributes.get("defaultAutoAddEnabled")

    @property
    def default_native_enabled(self) -> bool:
        """Whether the default native is enabled."""
        return self._attributes.get("defaultNativeEnabled")

    @property
    def native_ban_ttl(self) -> bool:
        """The native ban TTL of the banlist."""
        return self._attributes.get("nativeBanTTL")

    @property
    def native_ban_temp_max_expires(self) -> bool:
        """The native ban temp max expires of the banlist."""
        return self._attributes.get("nativeBanTempMaxExpires")

    @property
    def native_ban_perm_max_expires(self) -> bool:
        """The native ban perm max expires of the banlist."""
        return self._attributes.get("nativeBanPermMaxExpires")

    @property
    def organization_id(self) -> int:
        """The organization ID of the banlist."""
        return self._relationships.get("organization_id")

    @property
    def owner_id(self) -> int:
        """The owner ID of the banlist."""
        return self._relationships.get("owner_id")

    async def update(
        self,
        *,
        name: str | None = None,
        action: str | None = None,
        default_identifiers: list[IDENTIFIERS],
        default_reasons: list[str],
        autoadd: bool | None = None,
        native_ban: bool | None = None,
    ) -> Self:
        """Update this banlist with the altered information you supply.

        Parameters
        ----------
            banlist_id (str): Banlist ID.
            organization_id (str): Organization ID
            name (str, optional): Name of the banlist
            action (str, optional): "none", "log" or "kick"
            ban_identifiers (list, optional): ["steamID", "ip"]
            list_default_reasons (list, optional): [List of default reasons]
            autoadd (bool, optional): True or False
            native_ban (bool, optional): True or False
        """
        return await self._http.banlist_update(
            banlist_id=self.id,
            organization_id=self.organization_id,
            name=name,
            action=action,
            default_identifiers=default_identifiers,
            default_reasons=default_reasons,
            autoadd=autoadd,
            native_ban=native_ban,
        )

    async def get_subscribers(self) -> dict[str, Any]:
        """Get the subscriber information for a specific banlist.

        Parameters
        ----------
            banlist_id (str): The ID of the targeted banlist.
            organization_id (str): The ID of the targeted organization subscribed to the banlist.
        """
        return await self._http.banlist_subscribers(
            self.id,
            self.organization_id,
        )

    async def unsubscribe(self) -> None:
        """Unsubscribe from the banlist."""
        await self._http.banlist_unsubscribe(self.id, self.organization_id)

    async def invite(
        self,
        *,
        uses: int = 1,
        limit: int = 1,
        permmanage: bool = False,
        permcreate: bool = False,
        permupdate: bool = False,
        permdelete: bool = False,
    ) -> BanListInvite | None:
        """Create an invite to this banlist.

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
        return await self._http.create_banlist_invite(
            banlist_id=self.id,
            organization_id=self.organization_id,
            uses=uses,
            limit=limit,
            permmanage=permmanage,
            permcreate=permcreate,
            permupdate=permupdate,
            permdelete=permdelete,
        )

    async def get_invites(self) -> list[BanListInvite]:
        """Return all the invites for this banlist.

        Parameters
        ----------
            banlist_id (str): The ID of a banlist
        """
        return await self._http.banlist_invite_list(self.id)

    async def delete_invite(self, banlist_invite_id: str) -> None:
        """Delete an invite from this banlist.

        Parameters
        ----------
            banlist_id (str): The target banlist
            banlist_invite_id (str): The target invite.
        """
        await self._http.delete_banlist_invite(self.id, banlist_invite_id)
