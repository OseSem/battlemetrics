from typing import Any, Literal

from pydantic import BaseModel, Field

from .base import Base, BaseRelationships, Relationship


class ServerMetadata(BaseModel):
    """Metadata specific to the Server model."""

    beta_source_protocol: bool | None = Field(default=None, alias="betaSourceProtocol")
    client_perf: bool | None = Field(default=None, alias="clientPerf")
    connection_type: Literal["source", "ws"] | None = Field(
        default=None,
        alias="connectionType",
    )
    disable_locked: bool | None = Field(default=None, alias="disableLocked")
    disabled_reason: str | None = Field(default=None, alias="disabledReason")
    has_source_mod: bool | None = Field(default=None, alias="hasSourceMod")
    hll_get_player_info: bool | None = Field(default=None, alias="hllGetPlayerInfo")
    hll_player_list_interval: int | None = Field(
        default=None,
        alias="hllPlayerListInterval",
    )
    log_secret: str | None = Field(default=None, alias="logSecret")
    private_player_sessions: bool | None = Field(
        default=None,
        alias="privatePlayerSessions",
    )
    rcon_ip: str | None = Field(default=None, alias="rconIP")
    reserved_slot_kick_reason: str | None = Field(
        default=None,
        alias="reservedSlotKickReason",
    )
    reserved_slots: int | None = Field(default=None, alias="reservedSlots")
    reserved_slots_kick_last_to_join: bool | None = Field(
        default=None,
        alias="reservedSlotsKickLastToJoin",
    )
    status_interval: int | None = Field(default=None, alias="statusInterval")
    use_connection_pool: bool | None = Field(default=None, alias="useConnectionPool")
    use_get_chat: bool | None = Field(default=None, alias="useGetChat")
    username: str | None = None

    model_config = {
        "populate_by_name": True,
    }


class ServerAttributes(BaseModel):
    """Attributes specific to the Server model."""

    address: str | None = None
    country: str
    created_at: str = Field(alias="createdAt")
    details: dict[str, Any] | None = None
    id: str
    ip: str
    location: list[float]
    max_players: int = Field(alias="maxPlayers")
    metadata: ServerMetadata | None = None
    name: str
    players: int
    port: int
    port_query: int = Field(alias="portQuery")
    private: bool
    query_status: str | None = Field(default=None, alias="queryStatus")
    rank: int | None = None
    rcon_active: bool | None = Field(default=None, alias="rconActive")
    rcon_disconnected: str | None = Field(default=None, alias="rconDisconnected")
    rcon_last_connected: str | None = Field(default=None, alias="rconLastConnected")
    rcon_status: str | None = Field(default=None, alias="rconStatus")
    status: str
    updated_at: str = Field(alias="updatedAt")

    model_config = {
        "populate_by_name": True,
    }


class ServerGroupRelationship(Relationship):
    """Relationship for the ServerGroup model."""

    class ServerGroupMeta(BaseModel):
        """Metadata for the ServerGroup model."""

        leader: bool

    meta: ServerGroupMeta | None = None


class ServerRelationships(BaseRelationships):
    """Relationships for the Server model."""

    default_ban_list: Relationship | None = Field(default=None, alias="defaultBanList")
    game: Relationship | None = None
    organization: Relationship | None = None
    server_group: ServerGroupRelationship | None = Field(
        default=None,
        alias="serverGroup",
    )


class ServerMeta(BaseModel):
    """Metadata for the Server model."""

    action: Literal["none", "log", "kick"] | None
    default_native_enabled: bool | None = Field(
        default=None,
        alias="defaultNativeEnabled",
    )
    native_ban_perm_max_expires: int | None = Field(
        default=None,
        alias="nativeBanPermMaxExpires",
    )
    native_ban_ttl: int | None = Field(default=None, alias="nativeBanTTL")
    native_ban_temp_max_expires: int | None = Field(
        default=None,
        alias="nativeBanTempMaxExpires",
    )

    model_config = {
        "populate_by_name": True,
    }


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

    created_at: str = Field(alias="createdAt")
    expires: str | None = None
    identifiers: list[str]

    model_config = {
        "populate_by_name": True,
    }


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
