from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .base import Base, BaseRelationships, IdentifierTypesLiteral, Relationship


class BanAttributes(BaseModel):
    """Attributes for the Ban model."""

    reason: str
    note: str | None = None
    expires: datetime | None = None
    identifiers: list[str | dict[str, Any]]
    org_wide: bool = Field(alias="orgWide")
    auto_add_enabled: bool = Field(alias="autoAddEnabled")
    native_enabled: bool | None = Field(default=None, alias="nativeEnabled")
    timestamp: datetime
    uid: str
    id: int


class BanRelationships(BaseRelationships):
    """Relationships for the Ban model."""

    organization: Relationship
    server: Relationship
    player: Relationship
    ban_list: Relationship = Field(alias="banList")
    user: Relationship | None = None


class Ban(Base):
    """The Ban model representing a ban in Battlemetrics."""

    type: str = "ban"
    attributes: BanAttributes
    relationships: BanRelationships


class NativeBanAttributes(BaseModel):
    """Attributes for the NativeBan model."""

    created_at: datetime = Field(alias="createdAt")
    expires: datetime | None = None
    identifier: str
    reason: str | None = None
    state: Literal["added", "removed"]
    type: IdentifierTypesLiteral  # type: ignore[reportInvalidTypeForm]
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {
        "populate_by_name": True,
    }


class NativeBanRelationships(BaseRelationships):
    """Relationships for the NativeBan model."""

    ban: Relationship
    organization: Relationship
    server: Relationship


class NativeBan(Base):
    """Represents a native ban in Battlemetrics."""

    type: str = "banNative"
    attributes: NativeBanAttributes
    relationships: NativeBanRelationships
