from typing import Literal, TypedDict


class SessionAttributes(TypedDict):
    """Represents a Session Attributes."""

    start: str
    stop: str
    firstTime: bool
    name: str
    private: bool


class SessionRelationships(TypedDict):
    """Represents a Session Relationships."""

    server_id: int
    player_id: int
    identifier_id: int


class Session(TypedDict):
    """Represents a Session."""

    type: Literal["session"]
    id: str
    attributes: SessionAttributes
    relationships: SessionRelationships
