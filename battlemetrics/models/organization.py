from pydantic import BaseModel

from .base import Base, BaseRelationships, Relationship


class OrganizationAttributes(BaseModel):
    """Attributes specific to the Organization model."""

    active: bool
    banTemplate: str
    consentAPIKeysRequired: bool
    consentGeoIPRequired: bool
    consentOrganizationsRequired: bool
    dataSharingEnabled: bool
    discoverable: bool
    discoverableRank: int | None = None
    locale: str | None = None
    mfaRequired: bool
    name: str
    plan: str | None = None
    tz: str | None = None


class OrganizationRelationships(BaseRelationships):
    """Relationships for the Organization model."""

    banLists: Relationship
    defaultBanList: Relationship | None = None
    games: Relationship
    owner: Relationship
    servers: Relationship


class Organization(Base):
    """Organization model representing an organization in Battlemetrics."""

    type: str = "organization"
    attributes: OrganizationAttributes
    relationships: OrganizationRelationships


class OrganizationFriendAttributes(BaseModel):
    """Attributes for the OrganizationFriend model."""

    accepted: bool
    identifiers = list[str] | None
    notes: bool
    reciprocated: bool


class OrganizationFriendRelationships(BaseRelationships):
    """Relationships for the OrganizationFriend model."""

    flagsShared: Relationship
    flagsUsed: Relationship
    friend: Relationship
    organization: Relationship


class OrganizationFriend(Base):
    """Represents a friendship between two organizations."""

    type: str = "organizationFriend"
    attributes: OrganizationFriendAttributes
    relationships: OrganizationFriendRelationships


class OrganizationStatsAttributes(BaseModel):
    """Attributes for the Organization Stats model."""

    gameRanks: dict[str, int]
    identifiers: float
    uniquePlayers: float


class OrganizationStatsRelationships(BaseRelationships):
    """Relationships for the Organization Stats model."""

    organization: Relationship


class OrganizationStats(Base):
    """Represents the stats of an organization."""

    type: str = "organizationStats"
    attributes: OrganizationStatsAttributes
    relationships: OrganizationStatsRelationships
