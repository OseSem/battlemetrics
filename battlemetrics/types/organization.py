from typing import NamedTuple, TypedDict


class OrganizationAttributes(TypedDict):
    """Attributes of an organization."""

    name: str
    locale: str | None
    tz: str | None
    banTemplate: str
    mfaRequired: bool | None
    active: bool
    discoverable: bool
    discoverableRank: int | None
    consentGeoIPRequired: bool
    consentAPIKeysRequired: bool
    consentOrganizationsRequired: bool
    dataSharingEnabled: bool


class OrganizationRelationships(TypedDict):
    """Relationships of an organization."""

    owner_id: int
    defaultBanList_id: str


class Organization(TypedDict):
    """Represents Organization data."""

    type: str
    id: int
    attributes: OrganizationAttributes
    relationships: OrganizationRelationships


class OrganizationPlayerStats(NamedTuple):
    """Represents Organization Player Stats data."""

    minPlayers: int
    maxPlayers: int
    uniquePlayers: int
    uniquePlayersByCountry: dict[str, int]
    sessionDuration: int
    firstTimeSessionDuration: int
