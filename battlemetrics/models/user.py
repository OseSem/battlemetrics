"""User related models for the Battlemetrics API."""

from pydantic import BaseModel

from .base import Base, BaseRelationships, Relationship


class UserAttributes(BaseModel):
    """Attributes for the User model."""

    id: str
    nickname: str | None = None


class UserRelationships(BaseRelationships):
    """Relationships for the User model."""

    organizations: list[Relationship]


class User(Base):
    """User model representing a user in Battlemetrics."""

    type: str = "user"
    attributes: UserAttributes
    relationships: UserRelationships
