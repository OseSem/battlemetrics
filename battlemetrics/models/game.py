from typing import Literal

from pydantic import BaseModel

from .base import Base, BaseRelationships, Relationship


class GameMetadata(BaseModel):
    """Metadata specific to the Game model."""

    appid: float
    gamedir: str
    noPlayerList: bool


class GameAttributes(BaseModel):
    """Attributes specific to the Game model."""

    maxPlayers24H: float
    maxPlayers30D: float
    maxPlayers7D: float
    minPlayers24H: float
    minPlayers30D: float
    minPlayers7D: float
    name: str
    players: int
    playersByCountry: dict[str, int]
    servers: int
    serversByCountry: dict[str, int]
    metadata: GameMetadata


class Game(Base):
    """Game model representing a game in Battlemetrics."""

    type: str = "game"
    attributes: GameAttributes


class GameFeaturesAttributes(BaseModel):
    """Attributes for game features."""

    display: str
    featureType: Literal["select", "boolean", "range", "dateRange"]
    typeOptions: str


class GameFeaturesRelationships(BaseRelationships):
    """Relationships for game features."""

    game: Relationship


class GameFeatures(Base):
    """Game features model representing features of a game in Battlemetrics."""

    type: str = "gameFeature"
    attributes: GameFeaturesAttributes
    relationships: GameFeaturesRelationships


class GameFeatureOptionsAttributes(BaseModel):
    """Attributes for game feature options."""

    count: int
    display: str
    players: int
    updatedAt: str


class GameFeatureOptionsRelationships(BaseRelationships):
    """Relationships for game feature options."""

    gameFeature: Relationship


class GameFeatureOptions(Base):
    """Game feature options model representing options for a game feature in Battlemetrics."""

    type: str = "gameFeatureOption"
    attributes: GameFeatureOptionsAttributes
    relationships: GameFeatureOptionsRelationships
