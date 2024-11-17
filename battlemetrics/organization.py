from __future__ import annotations

from typing import TYPE_CHECKING

from . import utils
from .types.organization import Organization as OrganizationPayload
from .types.organization import (
    OrganizationAttributes,
    OrganizationPlayerStats,
    OrganizationRelationships,
)

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Any

    from .http import HTTPClient

__all__ = ("Organization",)


class Organization:
    """Represents an Organization."""

    def __init__(self, data: OrganizationPayload, *, http: HTTPClient) -> None:
        self._http = http

        self._data: OrganizationPayload = OrganizationPayload(**data)
        self._attributes: OrganizationAttributes = data.get("attributes")
        self._relationships: OrganizationRelationships = (
            utils.format_relationships(  # type: ignore [reportAttributeAccessIssue]
                data.get("relationships"),
            )
        )

    def __str__(self) -> str:
        """Return the name of the organization.

        Returns
        -------
        str
            The name of the organization.
        """
        return self.name

    @property
    def id(self) -> int:
        """Return the ID of the organization.

        Returns
        -------
        int
            The ID of the organization.
        """
        return self._data.get("id")

    @property
    def name(self) -> str:
        """Return the name of the organization.

        Returns
        -------
        str
            The name of the organization.
        """
        return self._attributes.get("name")

    @property
    def locale(self) -> str | None:
        """Return the locale of the organization.

        Returns
        -------
        str | None
            The locale of the organization, or None if not set.
        """
        return self._attributes.get("locale")

    @property
    def tz(self) -> str | None:
        """Return the timezone of the organization.

        Returns
        -------
        str | None
            The timezone of the organization, or None if not set.
        """
        return self._attributes.get("tz")

    @property
    def ban_template(self) -> str:
        """Return the ban template of the organization.

        Returns
        -------
        str
            The ban template of the organization.
        """
        return self._attributes.get("banTemplate")

    @property
    def mfa_required(self) -> bool | None:
        """Return whether MFA is required for the organization.

        Returns
        -------
        bool | None
            True if MFA is required, False otherwise, or None if not set.
        """
        return self._attributes.get("mfaRequired")

    @property
    def active(self) -> bool:
        """Return whether the organization is active.

        Returns
        -------
        bool
            True if the organization is active, False otherwise.
        """
        return self._attributes.get("active")

    @property
    def discoverable(self) -> bool:
        """Return whether the organization is discoverable.

        Returns
        -------
        bool
            True if the organization is discoverable, False otherwise.
        """
        return self._attributes.get("discoverable")

    @property
    def discoverable_rank(self) -> int | None:
        """Return the discoverable rank of the organization.

        Returns
        -------
        int | None
            The discoverable rank of the organization, or None if not set.
        """
        return self._attributes.get("discoverableRank")

    @property
    def consent_geoip_required(self) -> bool:
        """Return whether consent for GeoIP is required for the organization.

        Returns
        -------
        bool
            True if consent for GeoIP is required, False otherwise.
        """
        return self._attributes.get("consentGeoIPRequired")

    @property
    def consent_api_keys_required(self) -> bool:
        """Return whether consent for API keys is required for the organization.

        Returns
        -------
        bool
            True if consent for API keys is required, False otherwise.
        """
        return self._attributes.get("consentAPIKeysRequired")

    @property
    def consent_organizations_required(self) -> bool:
        """Return whether consent for organizations is required for the organization.

        Returns
        -------
        bool
            True if consent for organizations is required, False otherwise.
        """
        return self._attributes.get("consentOrganizationsRequired")

    @property
    def data_sharing_enabled(self) -> bool:
        """Return whether data sharing is enabled for the organization.

        Returns
        -------
        bool
            True if data sharing is enabled, False otherwise.
        """
        return self._attributes.get("dataSharingEnabled")

    @property
    def owner_id(self) -> int:
        """Return the owner ID of the organization.

        Returns
        -------
        int
            The owner ID of the organization.
        """
        return self._relationships.get("owner_id")

    @property
    def banlist_id(self) -> str:
        """Return the banlist ID of the organization.

        Returns
        -------
        str
            The banlist ID of the organization.
        """
        return self._relationships.get("defaultBanList_id")

    async def organization_player_stats(
        self,
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
        return await self._http.organization_player_stats(self.id, start_time, end_time, game)

    async def get_friends(
        self,
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
            filter_accepted (bool, optional): True or False. Have they accepted our friendship?
            filter_origin (bool, optional): True or False. Defaults to True.
            filter_name (str, optional): Name of a specific organization. Defaults to None.
            filter_reciprocated (bool, optional): True or False. Are the feelings mutual?

        Returns
        -------
            dict: Returns all the friendship information based on the paramaters set.
        """
        return await self._http.organization_friends_list(
            self.id,
            filter_name=filter_name,
            filter_accepted=filter_accepted,
            filter_origin=filter_origin,
            filter_reciprocated=filter_reciprocated,
        )
