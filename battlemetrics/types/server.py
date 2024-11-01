from typing import Literal, TypedDict
from uuid import UUID


class ServerMetadata(TypedDict):
    """Represent the metadata of a server."""

    betaSourceProtocol: bool
    clientPerf: bool
    connectionType: Literal["source", "ws"]
    disableLocked: bool | None
    disabledReason: str | None
    hasSourceMod: bool | None
    hllGetPlayerInfo: bool
    hllPlayerListInterval: int
    logSecret: str | None
    privatePlayerSessions: bool
    rconIP: str
    reservedSlotKickReason: str
    reservedSlots: int
    reservedSlotsKickLastToJoin: bool
    statusInterval: int
    useConnectionPool: bool
    useGetChat: bool
    username: str


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
    metadata: ServerMetadata
    relationships: ServerRelationships
