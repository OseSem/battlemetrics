from __future__ import annotations

import asyncio
import warnings
from typing import TYPE_CHECKING, Any

from battlemetrics.http import HTTPClient
from battlemetrics.models.ban import Ban

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from types import TracebackType

    from aiohttp import BaseConnector, BasicAuth

__all__ = ("Battlemetrics",)


class Battlemetrics:
    """The main client to handle all the Battlemetrics requests.

    Parameters
    ----------
        api_key (str)
            Your given API token.
    """

    def __init__(
        self,
        api_key: str,
        *,
        asyncio_debug: bool = False,
        connector: BaseConnector | None = None,
        loop: AbstractEventLoop | None = None,
        proxy: str | None = None,
        proxy_auth: BasicAuth | None = None,
    ) -> None:
        self.__api_key = api_key

        if loop is None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        else:
            self.loop: asyncio.AbstractEventLoop = loop

        self.loop.set_debug(asyncio_debug)

        self.http = HTTPClient(
            api_key=self.__api_key,
            connector=connector,
            loop=loop,
            proxy=proxy,
            proxy_auth=proxy_auth,
        )

    async def __aenter__(self) -> "Battlemetrics":
        """Enter the context manager and return the Battlemetrics client."""
        return self

    async def __aexit__(
        self,
        type: type[BaseException] | None,  # noqa: A002
        value: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the client when exiting the context."""
        await self.close()

    async def close(self) -> None:
        """Close the client."""
        await self.http.close()

    # Helpers / Getters

    async def create_ban(
        self,
        player_id: int,
        *,
        reason: str,
        note: str | None,
        banlist_id: str,
        organization_id: int,
        server_id: int,
        org_wide: bool = True,
        auto_add_enabled: bool = True,
        native_enabled: bool = True,
        identifiers: list[str | dict[str, Any]] | None = None,  # TODO: Add player object
        expires: str | None = None,
    ) -> Ban:
        """Create a ban with all required and optional parameters."""
        resp = await self.http.create_ban(
            player_id=player_id,
            reason=reason,
            note=note,
            banlist_id=banlist_id,
            organization_id=organization_id,
            server_id=server_id,
            org_wide=org_wide,
            auto_add_enabled=auto_add_enabled,
            native_enabled=native_enabled,
            identifiers=identifiers,
            expires=expires,
        )
        return Ban.model_validate(resp["data"])

    async def ban_info(self, ban_id: int) -> Ban:
        """Get information about a specific ban."""
        resp = await self.http.ban_info(ban_id)
        return Ban.model_validate(resp["data"])
