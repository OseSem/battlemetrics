from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

__all__ = (
    "Base",
    "Relationship",
    "BaseRelationships",
    "IDENTIFIER_TYPES",
    "IdentifierTypesLiteral",
)

IDENTIFIER_TYPES = [
    "steamID",
    "BEGUID",
    "legacyBEGUID",
    "ip",
    "name",
    "survivorName",
    "steamFamilyShareOwner",
    "conanCharName",
    "egsID",
    "eosID",
    "funcomID",
    "playFabID",
    "mcUUID",
    "7dtdEOS",
    "battlebitHWID",
    "hllWindowsID",
    "palworldUID",
    "reforgerUUID",
]
IdentifierTypesLiteral = Literal[*IDENTIFIER_TYPES]


class Base(BaseModel):
    """Base model for all Battlemetrics models.

    This model follows the Json API specification, which requires a `type` and `id` field.
    """

    type: str = Field(..., description="The type of the model.")
    id: str | int = Field(..., description="The unique identifier for the model.")


class Relationship(BaseModel):
    """Represents a relationship between two resources."""

    type: str
    id: str


class BaseRelationships(BaseModel):
    """Base model for all Battlemetrics relationships."""

    @field_validator("*", mode="before")
    @classmethod
    def flatten_data(cls, v: Any) -> Any:
        """Flatten the data field if it exists."""
        if isinstance(v, dict) and "data" in v:
            return v["data"]  # type: ignore[reportUnknownVariableType]
        return v  # type: ignore[reportUnknownVariableType]
