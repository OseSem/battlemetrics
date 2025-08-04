from typing import Literal

from pydantic import BaseModel

from .base import Base, BaseRelationships, Relationship
from .server import ServerData


class BanListAttributes(BaseModel):
    """Attributes for the BanList model."""

    action: Literal["none", "log", "kick"] | None
    defaultAutoAddEnabled: bool
    defaultIdentifiers: list[str] = []
    defaultNativeEnabled: bool | None = None
    defaultReasons: list[str] = []
    name: str
    nativeBanPermMaxExpires: int | None = None
    nativeBanTTL: int | None = None
    nativeBanTempMaxExpires: int | None = None
    permCreate: bool
    permDelete: bool
    permManage: bool
    permUpdate: bool


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
    banList: Relationship


class BanListExemption(Base):
    """Represents an exemption from a ban list."""

    type: str = "banExemption"
    attributes: BanListExemptionAttributes
    relationships: BanListExemptionRelationships
    relationships: BanListExemptionRelationships


class BanListInviteAttributes(BaseModel):
    """Attributes for the BanListInvite model."""

    limit: int | None
    permCreate: bool
    permDelete: bool
    permManage: bool
    permUpdate: bool
    uses: int


class BanListInviteRelationships(BaseRelationships):
    """Relationships for the BanListInvite model."""

    banList: Relationship
    organization: Relationship
    user: Relationship


class BanListInvite(Base):
    """Represents an invite to a ban list."""

    type: str = "banListInvite"
    attributes: BaseModel
    relationships: BaseRelationships
