from pydantic import BaseModel

from .base import Base, BaseRelationships, Relationship


class CommandsActivityRelationships(BaseRelationships):
    """Relationships for the CommandsActivity model."""

    games: Relationship
    organization: Relationship | None = None
    user: Relationship | None = None


class CommandsActivity(Base):
    """Represents the CommandsActivity model."""

    type: str = "commandStats"
    relationships: CommandsActivityRelationships


class CoplayAttributes(BaseModel):
    """Attributes for the Coplay model."""

    duration: int
    name: str


class Coplay(Base):
    """Represents the time two players have spent together."""

    type: str = "coplay"
    attributes: CoplayAttributes


class LeaderboardAttributes(BaseModel):
    """Attributes for the Leaderboard model."""

    name: str
    rank: int
    value: int


class Leaderboard(Base):
    """Represents a leaderboard entry."""

    type: str = "leaderboardPlayer"
    attributes: LeaderboardAttributes
