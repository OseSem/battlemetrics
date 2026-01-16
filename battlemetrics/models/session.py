from pydantic import BaseModel, Field

from .base import Base, BaseRelationships, Relationship


class SessionMetadata(BaseModel):
    """Metadata for the Session model."""

    key: str
    private: bool
    value: str | None = None


class SessionAttributes(BaseModel):
    """Attributes for the Session model."""

    first_time: bool = Field(alias="firstTime")
    metadata: list[SessionMetadata] | None = None
    name: str
    private: bool
    start: str
    stop: str | None = None

    model_config = {
        "populate_by_name": True,
    }


class IdentifierRelationship(BaseModel):
    """Relationship to an identifier."""

    id: str
    type: str = "identifier"


class SessionRelationships(BaseRelationships):
    """Relationships for the Session model."""

    identifiers: list[IdentifierRelationship] | None = None
    organization: Relationship | None = None
    player: Relationship | None = None
    server: Relationship | None = None


class Session(Base):
    """Session model representing a game play session on a server."""

    type: str = "session"
    attributes: SessionAttributes
    relationships: SessionRelationships
