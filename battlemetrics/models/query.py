from typing import Literal

from pydantic import BaseModel, Field

from .base import Base, BaseRelationships, Relationship


class PlayerQueryConditions(BaseModel):
    """Conditions for the PlayerQuery model."""

    score: float
    score_type: Literal["score", "pow", "multiplier"] = Field(alias="scoreType")
    types: list[str | None]

    model_config = {
        "populate_by_name": True,
    }


class PlayerQueryAttributes(BaseModel):
    """Attributes for the PlayerQuery model."""

    conditions: PlayerQueryConditions
    created_at: str = Field(alias="createdAt")
    query_name: str = Field(alias="queryName")
    updated_at: str = Field(alias="updatedAt")

    model_config = {
        "populate_by_name": True,
    }


class PlayerQueryRelationships(BaseRelationships):
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
