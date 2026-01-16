from typing import Literal

from pydantic import BaseModel, Field

from .base import Base, BaseRelationships, Relationship


class GameMetadata(BaseModel):
    """Metadata specific to the Game model.

    Fields may be partially present depending on the game; treat them as optional.
    """

    appid: float | None = None
    gamedir: str | None = None
    no_player_list: bool | None = Field(default=None, alias="noPlayerList")

    model_config = {
        "extra": "allow",
        "populate_by_name": True,
    }


class GameAttributes(BaseModel):
    """Attributes specific to the Game model."""

    max_players_24h: float = Field(alias="maxPlayers24H")
    max_players_30d: float = Field(alias="maxPlayers30D")
    max_players_7d: float = Field(alias="maxPlayers7D")
    min_players_24h: float = Field(alias="minPlayers24H")
    min_players_30d: float = Field(alias="minPlayers30D")
    min_players_7d: float = Field(alias="minPlayers7D")
    name: str
    players: int
    players_by_country: dict[str, int] = Field(alias="playersByCountry")
    servers: int
    servers_by_country: dict[str, int] = Field(alias="serversByCountry")
    metadata: GameMetadata | None = None

    model_config = {
        "populate_by_name": True,
    }


class Game(Base):
    """Game model representing a game in Battlemetrics."""

    type: str = "game"
    attributes: GameAttributes


class GameFeaturesAttributes(BaseModel):
    """Attributes for game features."""

    display: str
    feature_type: Literal["select", "boolean", "range", "dateRange"] = Field(
        alias="featureType",
    )
    type_options: str = Field(alias="typeOptions")

    model_config = {
        "populate_by_name": True,
    }


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
    updated_at: str = Field(alias="updatedAt")

    model_config = {
        "populate_by_name": True,
    }


class GameFeatureOptionsRelationships(BaseRelationships):
    """Relationships for game feature options."""

    game_feature: Relationship = Field(alias="gameFeature")


class GameFeatureOptions(Base):
    """Game feature options model representing options for a game feature in Battlemetrics."""

    type: str = "gameFeatureOption"
    attributes: GameFeatureOptionsAttributes
    relationships: GameFeatureOptionsRelationships
