from __future__ import annotations

from typing import TYPE_CHECKING

from . import utils
from .types.flag import Flag as FlagPayload
from .types.flag import (
    FlagAttributes,
    FlagRelationships
)

from datetime import datetime, UTC

if TYPE_CHECKING:
    from .http import HTTPClient

__all__ = ("Flag",)

class Flag:
    """Represents a Flag"""

    def __init__(self, *, data :FlagPayload, http : HTTPClient) -> None:

        self._http = http

        self._data : FlagPayload = FlagPayload(**data)
        self._attributes : FlagAttributes = data.get("attributes")
        self._relationships : FlagRelationships = (
            utils.format_relationships(
                # type: ignore [reportAttributeAccessIssue]
                data.get("relationships")
                )
        )

    def __str__(self) -> str:
        """Return when the string method is run on this Flag"""
        return self._attributes.get("name") 

    @property
    def id(self) -> str:
        """Returns ID of the Flag"""
        return self._data.get("id")
    
        
    @property
    def name(self) -> str:
        """Returns Name of the Flag"""
        return self._attributes.get("name")
    
    @property
    def description(self) -> str | None:
        """Returns Description of the Flag"""
        return self._attributes.get("description")
    
    @property
    def color(self) -> str:
        """Returns Color of the Flag"""
        return self._attributes.get("color")
    
    @property
    def created_at(self) -> datetime:
        """Returns creation date of the Flag"""
        
        return datetime.strptime(
            self._attributes.get("createdAt"),
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ).replace(
            tzinfo=UTC,
        )
    
    @property
    def updated_at(self) -> datetime:
        """Returns updated date of the Flag"""
        return datetime.strptime(
            self._attributes.get("updatedAt"),
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ).replace(
            tzinfo=UTC,
        )



    @property
    def icon(self) -> str | None:
        """Returns Icon of the Flag"""
        return self._attributes.get("icon")
    
    
    
    @property
    def organization_id(self) -> int:
        """Returns Organization ID of the Flag"""
        return self._relationships.get("organization_id")
    
    @property
    def user_id(self) -> int:
        """Returns user ID of the Flag"""
        return self._relationships.get("user_id")
    

    # TODO : add def Player Flag Update

    # TODO : add def Player Flag Delete
    
    async def update(self):
        ...

    async def delete(self):
        ...





        
    





    