from typing import Literal

from pydantic import BaseModel

from .base import Base, BaseRelationships, Relationship


class PlayerQueryConditions(BaseModel):
    """Conditions for the PlayerQuery model."""

    score: float
    scoreType: Literal["score", "pow", "multiplier"]
    types: list[str | None]


class PlayerQueryAttributes(BaseModel):
    """Attributes for the PlayerQuery model."""

    conditions: PlayerQueryConditions
    createdAt: str
    queryName: str
    updatedAt: str


class PlayerQueryRelationships(BaseModel):
    """Relationships for the PlayerQuery model."""

    organization: Relationship
    user: Relationship


class PlayerQuery(Base):
    """PlayerQuery model representing a query for players in Battlemetrics."""

    type: str = "playerQuery"
    attributes: PlayerQueryAttributes
    relationships: PlayerQueryRelationships


class PlayerQueryResultAttributes(BaseModel):
    """Attributes for the PlayerQueryResult model."""

    score: int


class PlayerQueryResultRelationships(BaseRelationships):
    """Relationships for the PlayerQueryResult model."""

    player: Relationship


class PlayerQueryResult(Base):
    """PlayerQueryResult model representing a result from a player query."""

    type: str = "playerQueryResult"
    attributes: PlayerQueryResultAttributes
    relationships: PlayerQueryResultRelationships
    relationships: PlayerQueryResultRelationships
