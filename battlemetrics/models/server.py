from typing import Any, Literal

from pydantic import BaseModel

from .base import Base, BaseRelationships, Relationship


class ServerMetadata(BaseModel):
    """Metadata specific to the Server model."""

    betaSourceProtocol: bool | None = None
    clientPerf: bool | None = None
    connectionType: Literal["source", "ws"] | None = None
    disableLocked: bool | None = None
    disabledReason: str | None = None
    hasSourceMod: bool | None = None
    hllGetPlayerInfo: bool | None = None
    hllPlayerListInterval: int | None = None
    logSecret: str | None = None
    privatePlayerSessions: bool | None = None
    rconIP: str | None = None
    reservedSlotKickReason: str | None = None
    reservedSlots: int | None = None
    reservedSlotsKickLastToJoin: bool | None = None
    statusInterval: int | None = None
    useConnectionPool: bool | None = None
    useGetChat: bool | None = None
    username: str | None = None


class ServerAttributes(BaseModel):
    """Attributes specific to the Server model."""

    address: str | None = None
    country: str
    createdAt: str
    details: dict[str, Any] | None = None
    id: str
    ip: str
    location: list[float]
    maxPlayers: int
    metadata: ServerMetadata | None = None
    name: str
    players: int
    port: int
    portQuery: int
    private: bool
    queryStatus: str | None = None
    rank: int | None = None
    rconActive: bool | None = None
    rconDisconnected: str | None = None
    rconLastConnected: str | None = None
    rconStatus: str | None = None
    status: str
    updatedAt: str


class ServerGroupRelationship(Relationship):
    """Relationship for the ServerGroup model."""

    class ServerGroupMeta(BaseModel):
        """Metadata for the ServerGroup model."""

        leader: bool

    meta: ServerGroupMeta | None = None


class ServerRelationships(BaseModel):
    """Relationships for the Server model."""

    defaultBanList: Relationship
    game: Relationship
    organization: Relationship
    serverGroup: ServerGroupRelationship | None = None


class ServerMeta(BaseModel):
    """Metadata for the Server model."""

    action: Literal["none", "log", "kick"] | None
    defaultNativeEnabled: bool | None = None
    nativeBanPermMaxExpires: int | None = None
    nativeBanTTL: int | None = None
    nativeBanTempMaxExpires: int | None = None


class ServerData(Base):
    """Server data model representing a server in Battlemetrics."""

    type: str = "server"
    meta: ServerMeta | None = None


class Server(Base):
    """Server model representing a server in Battlemetrics."""

    type: str = "server"
    attributes: ServerAttributes
    relationships: ServerRelationships


class ReservedSlotAttributes(BaseModel):
    """Attributes for the ReservedSlot model."""

    createdAt: str
    expires: str | None = None
    identifiers: list[str]


class ReservedSlotRelationships(BaseRelationships):
    """Relationships for the ReservedSlot model."""

    organization: Relationship
    player: Relationship
    servers: Relationship
    user: Relationship | None = None


class ReservedSlot(Base):
    """ReservedSlot model representing a reserved slot in Battlemetrics."""

    type: str = "reservedSlot"
    attributes: ReservedSlotAttributes
    meta: dict[str, Any]
