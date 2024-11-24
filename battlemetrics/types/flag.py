from typing import TypedDict


class FlagAttributes(TypedDict):
    """Represents the attributes of a Flag."""

    name: str
    description: str | None
    color: str
    icon: str | None
    createdAt: str
    updatedAt: str


class FlagRelationships(TypedDict):
    """Represents the relationships of a Flag."""

    user_id: int
    organization_id: int


class Flag(TypedDict):
    """Represents a Flag."""

    id: str
    type: str
    attributes: FlagAttributes
    relationships: FlagRelationships
