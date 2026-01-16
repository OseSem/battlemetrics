from pydantic import BaseModel, Field

from .base import Base, BaseRelationships, Relationship


class NoteAttributes(BaseModel):
    """Attributes for the Note model."""

    clearance_level: int = Field(alias="clearanceLevel")
    created_at: str = Field(alias="createdAt")
    expires_at: str | None = Field(default=None, alias="expiresAt")
    note: str
    shared: bool

    model_config = {
        "populate_by_name": True,
    }


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
