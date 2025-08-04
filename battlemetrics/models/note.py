from pydantic import BaseModel

from .base import Base, BaseRelationships, Relationship


class NoteAttributes(BaseModel):
    """Attributes for the Note model."""

    clearanceLevel: int
    createdAt: str
    expiresAt: str | None = None
    note: str
    shared: bool


class NoteRelationships(BaseRelationships):
    """Relationships for the Note model."""

    organization: Relationship
    player: Relationship
    user: Relationship


class Note(Base):
    """Note model representing a note in Battlemetrics."""

    type: str = "playerNote"
    attributes: NoteAttributes
    relationships: NoteRelationships
