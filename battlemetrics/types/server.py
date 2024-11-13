from typing import Literal, NamedTuple, TypedDict
from uuid import UUID


class ServerAttributes(TypedDict):
    """Represent the attributes of a server."""

    address: str
    country: str  # TODO: Add country enum
    createdAt: str
    details: str
    id: int
    ip: str
    location: tuple[float, float]
    maxPlayers: int
    name: str
    players: int
    port: int
    portQuery: int
    private: bool
    queryStatus: Literal["valid", "invalid", "timeout"] | None
    rank: int | None
    rconActive: bool | None
    rconDisconnected: str | None  # TODO: Add datetime
    rconLastConnected: str | None  # TODO: Add datetime
    rconStatus: (
        Literal["connected", "disconnected", "password-rejected", "timeout", "refused", "unknown"]
        | None
    )
    status: Literal["offline", "online", "dead", "removed", "invalid"]
    updatedAt: str  # TODO: Add datetime


class ServerRelationships(TypedDict):
    """Represent the relationships of a server."""

    defaultBanListID: UUID
    gameID: str
    organizationID: int
    serverGroupID: int


class Server(TypedDict):
    """Represent a server."""

    id: int
    type: str
    attributes: ServerAttributes
    relationships: ServerRelationships


class ServerSearch(NamedTuple):
    """Represent a search for a server."""

    search: str | None = None
    countries: list[str] | None = None  # TODO: Add countries type
    game: str | None = None
    blacklist: list[str] | None = None
    whitelist: list[str] | None = None
    organization: str | None = None
    gather_rate_min: int = 1
    gather_rate_max: int = 20
    group_size_min: int | None = 1
    group_size_max: int | None = 16
    map_size_min: int | None = 1
    map_size_max: int | None = 6000
    blueprints: bool | Literal["both"] = "both"
    pve: bool | Literal["both"] = "both"
    kits: bool | Literal["both"] = "both"
    status: Literal["offline", "online", "dead", "invalid", "unknown"] = "online"
    sort_rank: bool = True
    page_size: int = 100
    rcon: bool = True
