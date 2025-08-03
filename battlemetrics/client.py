from __future__ import annotations

import asyncio
import warnings
from typing import TYPE_CHECKING

from battlemetrics.http import HTTPClient

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

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
