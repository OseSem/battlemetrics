from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from . import utils
from .types.note import Note as NotePayload
from .types.note import NoteAttributes, NoteRelationships

if TYPE_CHECKING:
    from .http import HTTPClient

__all__ = ("Note",)


class Note:
    """Represents a note on a player."""

    def __init__(self, *, data: NotePayload, http: HTTPClient) -> None:
        self._http = http

        self._data: NotePayload = NotePayload(**data)
        self._attributes: NoteAttributes = data.get("attributes")
        self._relationships: NoteRelationships = (
            utils.format_relationships(  # type: ignore [reportAttributeAccessIssue]
                data.get("relationships"),
            )
        )

    def __str__(self) -> str:
        """Return when the string method is run on this Note."""
        return self.content

    def __repr__(self) -> str:
        """Return a string representation of the Note object."""
        return f"<Note id={self.id} content={self.content[:25]!r}>"

    @property
    def id(self) -> int:
        """Return the ID of the note."""
        return self._data.get("id")

    @property
    def clearancelevel(self) -> int:
        """Return the clearance level of the note."""
        return self._attributes.get("clearanceLevel")

    @property
    def created_at(self) -> datetime:
        """Return the date the note was created.

        Returns
        -------
        datetime:
            The date the note was created in the UTC timezone.
        """
        created = self._attributes.get("createdAt", "")
        return datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)

    @property
    def expires_at(self) -> datetime | None:
        """Return the date the note expires.

        Returns
        -------
        datetime | None:
            The date the note expires in the UTC timezone. Could not be specified.
        """
        expires = self._attributes.get("expiresAt")
        return (
            datetime.strptime(expires, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
            if expires
            else None
        )

    @property
    def content(self) -> str:
        """Return the note in plain text.

        Returns
        -------
        str:
            The note.
        """
        return utils.remove_html_tags(self._attributes.get("note"))

    @property
    def content_html(self) -> str:
        """Return the note in it's original HTML format.

        Returns
        -------
        str:
            The note.
        """
        return self._attributes.get("note")

    @property
    def shared(self) -> bool:
        """Return whether the note is shared.

        Returns
        -------
        bool:
            Whether the note is shared.
        """
        return self._attributes.get("shared")

    # TODO: Add organization property.
    @property
    def organization(self) -> int | None:
        """Return the organization that created the note.

        Returns
        -------
        int:
            The organizations ID the note is on.
        """
        return self._relationships.get("organization_id") if self._relationships else None

    # TODO: Add player property
    @property
    def player(self) -> int | None:
        """Return the player that the note is about.

        Returns
        -------
        int:
            The players ID that the note is about.
        """
        return self._relationships.get("player_id") if self._relationships else None

    # TODO: Add user property
    @property
    def user(self) -> int | None:
        """Return the user that created the note.

        Returns
        -------
        int:
            The users ID that created the note.
        """
        return self._relationships.get("user_id") if self._relationships else None

    async def delete(self) -> None:
        """Delete the note."""
        await self._http.delete_note(player_id=self.player if self.player else 0, note_id=self.id)

    async def update(
        self,
        attributes: NoteAttributes,
        *,
        append: bool,
    ) -> Note:
        """Update the note.

        Parameters
        ----------
        content : str
            The new content of the note.
        clearancelevel : int
            The new clearance level of the note.
        shared : bool
            Whether the note should be shared.
        append : bool
            Whether to append the new content to the existing content of the note.

        Returns
        -------
        Note:
            The updated note.
        """
        return await self._http.update_note(
            player_id=self.player if self.player else 0,
            note_id=self.id,
            attributes=attributes,
            append=append,
        )
