from pydantic import BaseModel, Field

from .base import Base, BaseRelationships, IdentifierTypesLiteral, Relationship
from .server import ServerData


class PlayerAttributes(BaseModel):
    """Attributes for the Player model."""

    created_at: str = Field(alias="createdAt")
    id: str
    name: str
    positive_match: bool = Field(alias="positiveMatch")
    private: bool
    updated_at: str = Field(alias="updatedAt")

    model_config = {
        "populate_by_name": True,
    }


class PlayerMeta(BaseModel):
    """Metadata for the Player model."""

    class Metadata(BaseModel):
        """Metadata for the Player model."""

        key: str
        private: bool
        value: str | None = None

    metadata: list[Metadata] | None = None


class PlayerRelationships(BaseRelationships):
    """Relationships for the Player model."""

    organizations: list[Relationship] | None = None
    server: Relationship | None = None
    servers: list[ServerData] | None = None
    user: Relationship | None = None


class Player(Base):
    """Player model representing a player in Battlemetrics."""

    type: str = "player"
    attributes: PlayerAttributes
    meta: PlayerMeta | None = None
    relationships: PlayerRelationships


class PlayerIdentifierAttributes(BaseModel):
    """Attributes for the PlayerIdentifier model."""

    identifier: str
    last_seen: str = Field(alias="lastSeen")
    metadata: object | None = None
    private: bool
    type: IdentifierTypesLiteral  # type: ignore[reportInvalidTypeForm]

    model_config = {
        "populate_by_name": True,
    }


class PlayerIdentifierRelationships(BaseRelationships):
    """Relationships for the PlayerIdentifier model."""

    organizations: Relationship
    player: Relationship


class PlayerIdentifier(Base):
    """PlayerIdentifier model representing a player's identifier."""

    type: str = "playerIdentifier"
    attributes: PlayerIdentifierAttributes
    relationships: PlayerIdentifierRelationships
    relationships: PlayerIdentifierRelationships


class PlayerCounterAttributes(BaseModel):
    """Attributes for the PlayerCounter model."""

    name: str
    value: int


class PlayerCounterRelationships(BaseRelationships):
    """Relationships for the PlayerCounter model."""

    organization: Relationship
    player: Relationship


class PlayerCounter(Base):
    """PlayerCounter model representing a player's counter."""

    type: str = "playerCounter"
    attributes: PlayerCounterAttributes
    relationships: PlayerCounterRelationships


class PlayerStatsAttributes(BaseModel):
    """Attributes for the PlayerStats model."""

    first_time_session_duration: float = Field(alias="firstTimeSessionDuration")
    max_players: float = Field(alias="maxPlayers")
    min_players: float = Field(alias="minPlayers")
    session_duration: float = Field(alias="sessionDuration")
    unique_players: float = Field(alias="uniquePlayers")
    unique_players_by_country: float = Field(alias="uniquePlayersByCountry")

    model_config = {
        "populate_by_name": True,
    }


class PlayerStatsRelationships(BaseRelationships):
    """Relationships for the PlayerStats model."""

    game: Relationship
    organization: Relationship
    server: Relationship


class PlayerStats(Base):
    """PlayerStats model representing a player's statistics."""

    type: str = "playerStats"
    attributes: PlayerStatsAttributes
    relationships: PlayerStatsRelationships


class RelatedPlayerIdentifierAttributes(BaseModel):
    """Attributes for the RelatedPlayerIdentifier model."""

    identifier: str
    last_seen: str = Field(alias="lastSeen")
    metadata: object | None = None
    private: bool
    type: IdentifierTypesLiteral  # type: ignore[reportInvalidTypeForm]

    model_config = {
        "populate_by_name": True,
    }


class RelatedPlayerIdentifierRelationships(BaseRelationships):
    """Relationships for the RelatedPlayerIdentifier model."""

    organizations: Relationship
    player: Relationship
    related_identifier: Relationship = Field(alias="relatedIdentifier")
    related_players: Relationship = Field(alias="relatedPlayers")


class RelatedPlayerIdentifierMeta(BaseModel):
    """Metadata for the RelatedPlayerIdentifier model."""

    common_identifier: bool = Field(alias="commonIdentifier")

    model_config = {
        "populate_by_name": True,
    }


class RelatedPlayerIdentifier(Base):
    """RelatedPlayerIdentifier model representing a related player's identifier."""

    type: str = "relatedPlayerIdentifier"
    attributes: RelatedPlayerIdentifierAttributes
    meta: RelatedPlayerIdentifierMeta
    relationships: RelatedPlayerIdentifierRelationships
