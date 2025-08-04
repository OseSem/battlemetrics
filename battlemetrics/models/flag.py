from typing import Literal

from pydantic import BaseModel

from .base import Base, BaseRelationships, Relationship

PlayerFlagIcon = Literal[
    None,
    "flag",
    "alarm",
    "attach_money",
    "block",
    "bookmark",
    "check_circle_outline",
    "emoji_objects",
    "enhanced_encryption",
    "error_outline",
    "highlight_off",
    "info",
    "label",
    "loyalty",
    "monetization_on",
    "note_add",
    "notifications",
    "notification_important",
    "policy",
    "verified_user",
    "priority_high",
    "remove_circle",
    "report",
    "star",
    "thumb_down",
    "thumb_up",
    "visibility",
    "warning",
    "whatshot",
]


class FlagPlayerAttributes(BaseModel):
    """Attributes for the FlagPlayer model."""

    addedAt: str
    removedAt: str | None = None


class FlagPlayerRelationships(BaseRelationships):
    """Relationships for the FlagPlayer model."""

    organization: Relationship
    player: Relationship
    playerFlag: Relationship
    user: Relationship


class FlagPlayer(Base):
    """Represents the relationship between a player flag and a player."""

    type: str = "flagPlayer"
    attributes: FlagPlayerAttributes
    relationships: FlagPlayerRelationships


class PlayerFlagAttributes(BaseModel):
    """Attributes for the PlayerFlag model."""

    color: str
    createdAt: str
    description: str | None = None
    icon: PlayerFlagIcon = None
    name: str
    updatedAt: str


class PlayerFlagMeta(BaseModel):
    """Metadata for the PlayerFlag model."""

    shared: bool


class PlayerFlagRelationships(BaseRelationships):
    """Relationships for the PlayerFlag model."""

    organization: Relationship
    user: Relationship


class PlayerFlag(Base):
    """Player flag model representing a flag that can be assigned to players."""

    type: str = "playerFlag"
    attributes: PlayerFlagAttributes
    meta: PlayerFlagMeta
    relationships: PlayerFlagRelationships
