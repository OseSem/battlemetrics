from typing import Literal

from pydantic import BaseModel, Field

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

    added_at: str = Field(alias="addedAt")
    removed_at: str | None = Field(default=None, alias="removedAt")

    model_config = {
        "populate_by_name": True,
    }


class FlagPlayerRelationships(BaseRelationships):
    """Relationships for the FlagPlayer model."""

    organization: Relationship | None = None
    player: Relationship | None = None
    player_flag: Relationship | None = Field(default=None, alias="playerFlag")
    user: Relationship | None = None


class FlagPlayer(Base):
    """Represents the relationship between a player flag and a player."""

    type: str = "flagPlayer"
    attributes: FlagPlayerAttributes
    relationships: FlagPlayerRelationships


class PlayerFlagAttributes(BaseModel):
    """Attributes for the PlayerFlag model."""

    color: str
    created_at: str = Field(alias="createdAt")
    description: str | None = None
    icon: PlayerFlagIcon = None
    name: str
    updated_at: str = Field(alias="updatedAt")

    model_config = {
        "populate_by_name": True,
    }


class PlayerFlagMeta(BaseModel):
    """Metadata for the PlayerFlag model."""

    shared: bool


class PlayerFlagRelationships(BaseRelationships):
    """Relationships for the PlayerFlag model."""

    organization: Relationship | None = None
    user: Relationship | None = None


class PlayerFlag(Base):
    """Player flag model representing a flag that can be assigned to players."""

    type: str = "playerFlag"
    attributes: PlayerFlagAttributes
    meta: PlayerFlagMeta | None = None
    relationships: PlayerFlagRelationships
