from pydantic import BaseModel

from .base import Base, BaseRelationships, IdentifierTypesLiteral, Relationship
from .server import ServerData


class PlayerAttributes(BaseModel):
    """Attributes for the Player model."""

    createdAt: str
    id: str
    name: str
    positiveMatch: bool
    private: bool
    updatedAt: str


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

    organizations: Relationship
    server: Relationship
    servers: list[ServerData] | None = None
    user: Relationship | None = None


class Player(Base):
    """Player model representing a player in Battlemetrics."""

    type: str = "player"
    attributes: PlayerAttributes
    meta: PlayerMeta
    relationships: PlayerRelationships


class PlayerIdentifierAttributes(BaseModel):
    """Attributes for the PlayerIdentifier model."""

    identifier: str
    lastSeen: str
    metadata: object | None = None
    private: bool
    type: IdentifierTypesLiteral  # type: ignore[reportInvalidTypeForm]


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

    firstTimeSessionDuration: float
    maxPlayers: float
    minPlayers: float
    sessionDuration: float
    uniquePlayers: float
    uniquePlayersByCountry: float


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
    lastSeen: str
    metadata: object | None = None
    private: bool
    type: IdentifierTypesLiteral  # type: ignore[reportInvalidTypeForm]


class RelatedPlayerIdentifierRelationships(BaseRelationships):
    """Relationships for the RelatedPlayerIdentifier model."""

    organizations: Relationship
    player: Relationship
    relatedIdentifier: Relationship
    relatedPlayers: Relationship


class RelatedPlayerIdentifierMeta(BaseModel):
    """Metadata for the RelatedPlayerIdentifier model."""

    commonIdentifier: bool


class RelatedPlayerIdentifier(Base):
    """RelatedPlayerIdentifier model representing a related player's identifier."""

    type: str = "relatedPlayerIdentifier"
    attributes: RelatedPlayerIdentifierAttributes
    meta: RelatedPlayerIdentifierMeta
    relationships: RelatedPlayerIdentifierRelationships
