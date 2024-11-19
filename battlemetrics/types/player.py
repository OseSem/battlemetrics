from typing import TypedDict


class PlayerAttributes(TypedDict):
    """Attributes of a Player."""

    id: int
    name: str
    createdAt: str
    updatedAt: str
    private: bool
    positiveMatch: bool


class Player(TypedDict):
    """Represents a player."""

    type: str
    id: int
    attributes: PlayerAttributes
