from pydantic import BaseModel

from .base import Base, Relationship


class SessionMetadata(BaseModel):
    """Metadata for the Session model."""

    key: str
    private: bool
    value: str | None = None


class SessionAttributes(BaseModel):
    """Attributes for the Session model."""

    firstTime: bool
    metadata: list[SessionMetadata] | None = None
    name: str
    private: bool
    start: str
    stop: str | None = None


class IdentifierRelationship(BaseModel):
    """Relationship to an identifier."""

    id: str
    type: str = "identifier"


class SessionRelationships(BaseModel):
    """Relationships for the Session model."""

    identifiers: list[IdentifierRelationship]
    organization: Relationship
    player: Relationship
    server: Relationship


class Session(Base):
    """Session model representing a game play session on a server."""

    type: str = "session"
    attributes: SessionAttributes
    relationships: SessionRelationships
