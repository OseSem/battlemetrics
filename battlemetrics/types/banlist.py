from typing import Literal, NamedTuple, TypedDict

from battlemetrics.http import IDENTIFIERS


class BanListAttributes(TypedDict):
    """Represents a BanList Attributes."""

    name: str
    action: str
    permManage: bool
    permCreate: bool
    permUpdate: bool
    permDelete: bool
    defaultIdentifiers: list[IDENTIFIERS]
    defaultReasons: list[str]
    defaultAutoAddEnabled: bool
    defaultNativeEnabled: bool
    nativeBanTTL: bool
    nativeBanTempMaxExpires: bool
    nativeBanPermMaxExpires: bool


class BanListRelationships(TypedDict):
    """Represents a BanList Relationships."""

    organization_id: int
    owner_id: int


class BanList(TypedDict):
    """Represents a BanList."""

    id: str
    type: Literal["banList"]
    attributes: BanListAttributes
    relationships: BanListRelationships


class BanListInvite(NamedTuple):
    """Represents a BanList Invite."""

    id: int
    banlist_id: str
    organization_id: int
    type: Literal["banListInvite"] = "banListInvite"


class BanListExemption(NamedTuple):
    """Represents a BanList Exemption."""

    id: int
    reason: str | None
    ban_id: int
    organization_id: int
    type: Literal["banExemption"] = "banExemption"
