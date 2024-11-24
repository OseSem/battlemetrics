from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from . import utils
from .types.session import Session as SessionPayload
from .types.session import SessionAttributes, SessionRelationships

if TYPE_CHECKING:

    from .http import HTTPClient

__all__ = ("Session",)


class Session:
    """Represents a server."""

    def __init__(self, data: SessionPayload, *, http: HTTPClient) -> None:
        self._http = http
        self._data: SessionPayload = SessionPayload(**data)
        self._attributes: SessionAttributes = data.get("attributes")
        self._relationships: SessionRelationships = (
            utils.format_relationships(  # type: ignore [reportAttributeAccessIssue]
                data.get("relationships"),
            )
        )

    @property
    def id(self) -> str:
        """Returns ID of the session."""
        return self._data.get("id")

    @property
    def start(self) -> datetime:
        """Returns start of the session."""
        return datetime.strptime(self._attributes.get("start"), "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=UTC,
        )

    @property
    def stop(self) -> datetime:
        """Returns stop of the session."""
        return datetime.strptime(self._attributes.get("stop"), "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=UTC,
        )

    @property
    def first_time(self) -> bool:
        """Returns first time of the session."""
        return self._attributes.get("firstTime")

    @property
    def player_name(self) -> str:
        """Returns name of the sessions player."""
        return self._attributes.get("name")

    @property
    def private(self) -> bool:
        """Returns private of the session."""
        return self._attributes.get("private")
