from pydantic import BaseModel, Field

from .base import Base, BaseRelationships, Relationship


class OrganizationAttributes(BaseModel):
    """Attributes specific to the Organization model."""

    active: bool
    ban_template: str = Field(alias="banTemplate")
    consent_api_keys_required: bool = Field(alias="consentAPIKeysRequired")
    consent_geo_ip_required: bool = Field(alias="consentGeoIPRequired")
    consent_organizations_required: bool = Field(alias="consentOrganizationsRequired")
    data_sharing_enabled: bool = Field(alias="dataSharingEnabled")
    discoverable: bool
    discoverable_rank: int | None = Field(default=None, alias="discoverableRank")
    locale: str | None = None
    mfa_required: bool = Field(alias="mfaRequired")
    name: str
    plan: str | None = None
    tz: str | None = None

    model_config = {
        "populate_by_name": True,
    }


class OrganizationRelationships(BaseRelationships):
    """Relationships for the Organization model."""

    ban_lists: Relationship = Field(alias="banLists")
    default_ban_list: Relationship | None = Field(default=None, alias="defaultBanList")
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
    identifiers: list[str] | None
    notes: bool
    reciprocated: bool


class OrganizationFriendRelationships(BaseRelationships):
    """Relationships for the OrganizationFriend model."""

    flags_shared: Relationship = Field(alias="flagsShared")
    flags_used: Relationship = Field(alias="flagsUsed")
    friend: Relationship
    organization: Relationship


class OrganizationFriend(Base):
    """Represents a friendship between two organizations."""

    type: str = "organizationFriend"
    attributes: OrganizationFriendAttributes
    relationships: OrganizationFriendRelationships


class OrganizationStatsAttributes(BaseModel):
    """Attributes for the Organization Stats model."""

    game_ranks: dict[str, int] = Field(alias="gameRanks")
    identifiers: float
    unique_players: float = Field(alias="uniquePlayers")

    model_config = {
        "populate_by_name": True,
    }


class OrganizationStatsRelationships(BaseRelationships):
    """Relationships for the Organization Stats model."""

    organization: Relationship


class OrganizationStats(Base):
    """Represents the stats of an organization."""

    type: str = "organizationStats"
    attributes: OrganizationStatsAttributes
    relationships: OrganizationStatsRelationships
