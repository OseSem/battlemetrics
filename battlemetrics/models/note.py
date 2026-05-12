from datetime import datetime

from pydantic import BaseModel, Field

from .base import Base, BaseRelationships, Relationship


class NoteAttributes(BaseModel):
    """Attributes for the Note model."""

    clearance_level: int | None = Field(default=None, alias="clearanceLevel")
    created_at: datetime = Field(alias="createdAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
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
