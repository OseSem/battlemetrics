from typing import Literal

from pydantic import BaseModel, Field

from .base import Base, BaseRelationships, Relationship
from .server import ServerData


class BanListAttributes(BaseModel):
    """Attributes for the BanList model."""

    action: Literal["none", "log", "kick"] | None
    default_auto_add_enabled: bool = Field(alias="defaultAutoAddEnabled")
    default_identifiers: list[str] = Field(
        default_factory=list,
        alias="defaultIdentifiers",
    )
    default_native_enabled: bool | None = Field(
        default=None,
        alias="defaultNativeEnabled",
    )
    default_reasons: list[str] = Field(default_factory=list, alias="defaultReasons")
    name: str
    native_ban_perm_max_expires: int | None = Field(
        default=None,
        alias="nativeBanPermMaxExpires",
    )
    native_ban_ttl: int | None = Field(default=None, alias="nativeBanTTL")
    native_ban_temp_max_expires: int | None = Field(
        default=None,
        alias="nativeBanTempMaxExpires",
    )
    perm_create: bool = Field(alias="permCreate")
    perm_delete: bool = Field(alias="permDelete")
    perm_manage: bool = Field(alias="permManage")
    perm_update: bool = Field(alias="permUpdate")

    model_config = {
        "populate_by_name": True,
    }


class BanListRelationships(BaseRelationships):
    """Relationships for the BanList model."""

    organization: Relationship
    owner: Relationship
    servers: list[ServerData] | None = None


class BanList(Base):
    """Represents a ban list in Battlemetrics."""

    type: str = "banList"
    attributes: BanListAttributes
    relationships: BanListRelationships


class BanListExemptionAttributes(BaseModel):
    """Attributes for the BanListExemption model."""

    reason: str


class BanListExemptionRelationships(BaseRelationships):
    """Relationships for the BanListExemption model."""

    ban: Relationship
    ban_list: Relationship = Field(alias="banList")


class BanListExemption(Base):
    """Represents an exemption from a ban list."""

    type: str = "banExemption"
    attributes: BanListExemptionAttributes
    relationships: BanListExemptionRelationships


class BanListInviteAttributes(BaseModel):
    """Attributes for the BanListInvite model."""

    limit: int | None
    perm_create: bool = Field(alias="permCreate")
    perm_delete: bool = Field(alias="permDelete")
    perm_manage: bool = Field(alias="permManage")
    perm_update: bool = Field(alias="permUpdate")
    uses: int

    model_config = {
        "populate_by_name": True,
    }


class BanListInviteRelationships(BaseRelationships):
    """Relationships for the BanListInvite model."""

    ban_list: Relationship = Field(alias="banList")
    organization: Relationship
    user: Relationship


class BanListInvite(Base):
    """Represents an invite to a ban list."""

    type: str = "banListInvite"
    attributes: BaseModel
    relationships: BaseRelationships
