from __future__ import annotations

import asyncio
import uuid
from enum import Enum
from logging import getLogger
from typing import TYPE_CHECKING, Any, ClassVar, Literal

import aiohttp
import yarl

from .errors import BMException, Forbidden, HTTPException, NotFound, Unauthorized

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from types import TracebackType

    from aiohttp import BaseConnector, ClientResponse, ClientSession
    from yarl import URL


_log = getLogger(__name__)


class IdentifierType(Enum):
    """A player identifier type."""

    BE_GUID = "BEGUID"
    BE_LEGACY_GUID = "legacyBEGUID"
    CONAN_CHAR_NAME = "conanCharName"
    EGS_ID = "egsID"
    FUNCOM_ID = "funcomID"
    IP = "ip"
    MC_UUID = "mcUUID"
    NAME = "name"
    PLAY_FAB_ID = "playFabID"
    STEAM_FAMILY_SHARE_OWNER = "steamFamilyShareOwner"
    STEAM_ID = "steamID"
    SURVIVOR_NAME = "survivorName"

    def __repr__(self) -> str:
        """Return a string representation of the identifier type."""
        return f"<{self.__class__.__name__}.{self.name}>"


async def json_or_text(
    response: ClientResponse,
) -> dict[str, Any] | list[dict[str, Any]] | str:
    """
    Process a `ClientResponse` to return either a JSON object or raw text.

    This function attempts to parse the response as JSON. If the content type of the response is not
    application/json or parsing fails, it falls back to returning the raw text of the response.

    Parameters
    ----------
    response : ClientResponse
        The response object to process.

    Returns
    -------
    dict[str, t.Any] | list[dict[str, t.Any]] | str
        The parsed JSON object as a dictionary or list of dictionaries, or the raw response text.
    """
    try:
        if "application/json" in response.headers["content-type"].lower():
            return await response.json()
    except KeyError:
        # Thanks Cloudflare
        pass

    return await response.text(encoding="utf-8")


METHODS = Literal[
    "GET",
    "HEAD",
    "OPTIONS",
    "TRACE",
    "PUT",
    "DELETE",
    "POST",
    "PATCH",
    "CONNECT",
]


class Route:
    """Represents a route for the BattleMetrics API.

    This method requires either one of path or url.

    Parameters
    ----------
    method : str
        The HTTP method for the route.
    path : str
        The path for the route.
    url : str | URL
        The URL for the route.
    parameters : int | str | bool
        Optional parameters for the route.
    """

    BASE: ClassVar[str] = "https://api.battlemetrics.com"

    def __init__(
        self,
        method: METHODS,
        path: str,
        **parameters: int | str | bool,
    ) -> None:
        self.method: str = method
        url = path if path.startswith(("http://", "https://")) else f"{self.BASE}{path}"
        self.url: URL = (
            yarl.URL(url).update_query(**parameters) if parameters else yarl.URL(url)
        )


class HTTPClient:
    """Represent an HTTP Client used for making requests to APIs."""

    def __init__(
        self,
        api_key: str,
        *,
        connector: BaseConnector | None = None,
        loop: AbstractEventLoop | None = None,
        proxy: str | None = None,
        proxy_auth: aiohttp.BasicAuth | None = None,
    ) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.connector = connector
        self.proxy = proxy
        self.proxy_auth = proxy_auth

        self.__session: ClientSession = None  # type: ignore[reportAttributeAccessIssue]

        self.api_key: str = api_key

        self.ensure_session()

    def __aexit__(
        self,
        exc_type: BaseException | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the HTTP client when exiting."""
        return self.close()

    def ensure_session(self) -> None:
        """
        Ensure that an :class:`ClientSession` is created and open.

        If a session does not exist, this method creates a new :class:`ClientSession`
        using the provided connector and loop.
        """
        if not self.__session or self.__session.closed:
            self.__session = aiohttp.ClientSession(
                connector=self.connector,
                loop=self.loop,
            )

    async def close(self) -> None:
        """Close the :class:`ClientSession` if it exists and is open."""
        if self.__session:
            await self.__session.close()

    async def request(
        self,
        route: Route,
        **kwargs: Any,
    ) -> Any:
        """
        Send a request to the specified route and returns the response.

        This method constructs and sends an HTTP request based on the specified route and headers.
        It processes the response to return JSON data or raw text, handling errors as needed.

        Parameters
        ----------
        route : Route
            The route object containing the method and URL for the request.

        Returns
        -------
        dict[str, t.Any] | list[dict[str, t.Any]] | str
            The response data as a parsed JSON object or list, or raw text if JSON parsing is
            not applicable.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
            Might raise a more specific exception if the response status code is known.
        """
        self.ensure_session()

        method = route.method
        url = route.url
        path = route.url.path

        headers: dict[str, Any] = {
            "Accept": "application/json",
            **(kwargs.get("headers") or {}),
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if "json" in kwargs:
            headers["Content-Type"] = "application/json"

        kwargs["headers"] = headers

        if self.proxy:
            kwargs["proxy"] = self.proxy
        if self.proxy_auth:
            kwargs["proxy_auth"] = self.proxy_auth

        async with self.__session.request(method, url, **kwargs) as response:
            _log.debug("%s %s returned %s", method, path, response.status)

            # errors typically have text involved, so this should be safe 99.5% of the time.
            data = await json_or_text(response)

            if 200 <= response.status < 300:
                return data

            if isinstance(data, dict):
                if response.status == 401:
                    _log.warning(
                        "Path %s returned 401, your API key may be invalid.",
                        path,
                    )
                    raise Unauthorized(response, data)
                if response.status == 403:
                    _log.warning(
                        "Path %s returned 403, check whether you have valid permissions.",
                        path,
                    )
                    raise Forbidden(response, data)
                if response.status == 404:
                    _log.warning(
                        "Path %s returned 404, check whether the path is correct.",
                        path,
                    )
                    raise NotFound(response, data)
                if response.status == 429:
                    _log.warning(
                        "We're being rate limited. You are limited to %s requests per minute.",
                        response.headers.get("X-Rate-Limit-Limit"),
                    )

                raise HTTPException(response, data)

            raise BMException

    # HTTP Requests

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
        identifiers: list[str | dict[str, Any]] | None = None,
        expires: str | None = None,
    ) -> dict[str, Any]:
        """Create a ban with all required and optional parameters."""
        data: dict[str, Any] = {
            "data": {
                "type": "ban",
                "attributes": {
                    "uid": str(uuid.uuid4())[:14],
                    "reason": reason,
                    "note": note,
                    "expires": expires,
                    "identifiers": identifiers or [],  # TODO: Add identifier handling
                    "orgWide": org_wide,
                    "autoAddEnabled": auto_add_enabled,
                    "nativeEnabled": native_enabled,
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}",
                        },
                    },
                    "server": {
                        "data": {
                            "type": "server",
                            "id": f"{server_id}",
                        },
                    },
                    "player": {
                        "data": {
                            "type": "player",
                            "id": f"{player_id}",
                        },
                    },
                    "banList": {
                        "data": {
                            "type": "banList",
                            "id": f"{banlist_id}",
                        },
                    },
                },
            },
        }

        return await self.request(Route(method="POST", path="/bans"), json=data)

    async def import_bans(self, bans: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Import multiple bans at once.

        This method allows adding multiple bans at once with certain limitations.

        Parameters
        ----------
        bans : list[dict[str, Any]]
            A list of ban data dictionaries, each containing attributes and relationships.

        Returns
        -------
        Any
            The response from the API.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        data = {"data": bans}

        return await self.request(Route(method="POST", path="/bans/import"), json=data)

    async def export_bans(
        self,
        file_format: Literal[
            "arma2/bans.txt",
            "arma3/bans.txt",
            "squad/Bans.cfg",
            "ark/banlist.txt",
            "rust/bans.cfg",
            "rust/bansip_SERVER.ini",
        ],
        *,
        organization_id: int | None = None,
        server_id: int | None = None,
    ) -> Any:
        """Export bans in a specific format.

        Parameters
        ----------
        file_format : str
            The format to export the bans in.

        Returns
        -------
        Any
            The response from the API containing the exported bans.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        params = {"format": file_format}
        if organization_id:
            params["filter[organization]"] = str(organization_id)
        if server_id:
            params["filter[server]"] = str(server_id)

        return await self.request(
            Route(method="GET", path="/bans/export"),
            params=params,
        )

    async def delete_ban(self, ban_id: int) -> None:
        """Delete a specific ban by its ID.

        Parameters
        ----------
        ban_id : int
            The ID of the ban to delete.


        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        return await self.request(Route(method="DELETE", path=f"/bans/{ban_id}"))

    async def ban_info(self, ban_id: int) -> dict[str, Any]:
        """Get information about a specific ban."""
        return await self.request(
            Route(
                method="GET",
                path=f"/bans/{ban_id}",
                include="organization,player,server,user",
            ),
        )

    async def list_bans(
        self,
        *,
        banlist_id: str | None = None,
        exempt: bool | None = None,
        expired: bool | None = None,
        organization_id: int | None = None,
        player_id: int | None = None,
        search: str | None = None,
        server_id: int | None = None,
        user_ids: list[int] | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """List bans with optional filters for organization and server.

        Parameters
        ----------
        organization_id : str | None
            The ID of the organization to filter by.
        server_id : str | None
            The ID of the server to filter by.
        page : int
            The page number for pagination.
        per_page : int
            The number of results per page.

        Returns
        -------
        Any
            The response from the API containing the list of bans.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        params: dict[str, Any] = {
            "include": "organization,player,server,user",
        }

        if banlist_id:
            params["filter[banList]"] = banlist_id
        if exempt is not None:
            params["filter[exempt]"] = str(exempt).lower()
        if expired is not None:
            params["filter[expired]"] = str(expired).lower()
        if player_id:
            params["filter[player]"] = player_id
        if search:
            params["filter[search]"] = search
        if user_ids:
            params["filter[users]"] = ",".join(map(str, user_ids))
        if organization_id:
            params["filter[organization]"] = organization_id
        if server_id:
            params["filter[server]"] = server_id
        if page_size:
            params["page[size]"] = page_size

        return await self.request(Route(method="GET", path="/bans"), params=params)

    async def update_ban(
        self,
        ban_id: int | None = None,
        *,
        reason: str | None = None,
        note: str | None = None,
        identifiers: list[str | dict[str, Any]] | None = None,
        expires: str | None = None,
        org_wide: bool = True,
        auto_add_enabled: bool = True,
        native_enabled: bool = True,
    ) -> dict[str, Any]:
        """Update a specific ban by its ID.

        Parameters
        ----------
        ban_id : int
            The ID of the ban to update.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        data: dict[str, Any] = {
            "data": {
                "type": "ban",
                "attributes": {
                    "reason": reason,
                    "note": note,
                    "expires": expires,
                    "identifiers": identifiers or [],  # TODO: Add identifier handling
                    "orgWide": org_wide,
                    "autoAddEnabled": auto_add_enabled,
                    "nativeEnabled": native_enabled,
                },
            },
        }
        return await self.request(
            Route(method="PATCH", path=f"/bans/{ban_id}"),
            json=data,
        )

    async def create_banlist_exemption(
        self,
        ban_id: int,
        organization_id: int,
        *,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Create a banlist Exemption."""
        data = {
            "data": {
                "type": "banExemption",
                "attributes": {"reason": reason},
                "relationships": {
                    "organization": {
                        "data": {"type": "organization", "id": str(organization_id)},
                    },
                },
            },
        }
        return await self.request(
            Route(method="POST", path=f"/bans/{ban_id}/relationships/exemptions"),
            json=data,
        )

    async def read_banlist_exemption(
        self,
        ban_id: int,
        ban_exemption_id: int,
    ) -> dict[str, Any]:
        """Read a specific banlist exemption by its ID.

        Parameters
        ----------
        ban_id : int
            The ID of the ban to read.
        ban_exemption_id : int
            The ID of the ban exemption to read.

        Returns
        -------
        dict[str, Any]
            The response from the API containing the banlist exemption.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        return await self.request(
            Route(
                method="GET",
                path=f"/bans/{ban_id}/relationships/exemptions/{ban_exemption_id}",
            ),
        )

    async def list_banlist_exemptions(self, ban_id: int) -> dict[str, Any]:
        """List all banlist exemptions for a specific ban.

        Parameters
        ----------
        ban_id : int
            The ID of the ban to list exemptions for.

        Returns
        -------
        dict[str, Any]
            The response from the API containing the list of banlist exemptions.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        return await self.request(
            Route(method="GET", path=f"/bans/{ban_id}/relationships/exemptions"),
        )

    async def update_banlist_exemption(
        self,
        ban_id: int,
        *,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Update a specific banlist exemption by its ID.

        Parameters
        ----------
        ban_id : int
            The ID of the ban to update.
        ban_exemption_id : int
            The ID of the ban exemption to update.
        reason : str | None
            The new reason for the ban exemption.

        Returns
        -------
        dict[str, Any]
            The response from the API containing the updated banlist exemption.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        data = {
            "data": {
                "type": "banExemption",
                "attributes": {"reason": reason},
            },
        }
        return await self.request(
            Route(method="PATCH", path=f"/bans/{ban_id}/relationships/exemptions"),
            json=data,
        )

    async def delete_banlist_exemption(
        self,
        ban_id: int,
    ) -> None:
        """Delete a specific banlist exemption by its ID.

        Parameters
        ----------
        ban_id : int
            The ID of the ban to delete the exemption from.
        ban_exemption_id : int
            The ID of the ban exemption to delete.

        Returns
        -------
        dict[str, Any]
            The response from the API confirming the deletion.

        Raises
        ------
        BMException
            Will raise if the request fails or the response indicates an error.
        """
        await self.request(
            Route(method="DELETE", path=f"/bans/{ban_id}/relationships/exemptions"),
        )

    # ----------------------------- Ban Lists ----------------------------- #

    async def create_banlist(
        self,
        *,
        name: str,
        action: Literal["none", "log", "kick"],
        organization_id: int,
        owner_id: int,
        default_identifiers: list[str] | None = None,
        default_reasons: list[str] | None = None,
        default_auto_add_enabled: bool = True,
        default_native_enabled: bool | None = None,
        native_ban_ttl: int | None = None,
        native_ban_temp_max_expires: int | None = None,
        native_ban_perm_max_expires: int | None = None,
    ) -> dict[str, Any]:
        """Create a ban list."""
        data = {
            "data": {
                "type": "banList",
                "attributes": {
                    "name": name,
                    "action": action,
                    "defaultIdentifiers": default_identifiers or [],
                    "defaultReasons": default_reasons or [],
                    "defaultAutoAddEnabled": default_auto_add_enabled,
                    "defaultNativeEnabled": default_native_enabled,
                    "nativeBanTTL": native_ban_ttl,
                    "nativeBanTempMaxExpires": native_ban_temp_max_expires,
                    "nativeBanPermMaxExpires": native_ban_perm_max_expires,
                },
                "relationships": {
                    "organization": {
                        "data": {"type": "organization", "id": str(organization_id)},
                    },
                    "owner": {"data": {"type": "organization", "id": str(owner_id)}},
                },
            },
        }
        return await self.request(Route(method="POST", path="/ban-lists"), json=data)

    async def create_banlist_from_invite(
        self,
        *,
        code: str,
        action: Literal["none", "log", "kick"],
        organization_id: int,
        owner_id: int,
        default_identifiers: list[str] | None = None,
        default_reasons: list[str] | None = None,
        default_auto_add_enabled: bool = True,
        default_native_enabled: bool | None = None,
        native_ban_ttl: int | None = None,
        native_ban_temp_max_expires: int | None = None,
        native_ban_perm_max_expires: int | None = None,
    ) -> dict[str, Any]:
        """Accept a ban list invite and create a subscription."""
        data = {
            "data": {
                "type": "banList",
                "attributes": {
                    "code": code,
                    "action": action,
                    "defaultIdentifiers": default_identifiers or [],
                    "defaultReasons": default_reasons or [],
                    "defaultAutoAddEnabled": default_auto_add_enabled,
                    "defaultNativeEnabled": default_native_enabled,
                    "nativeBanTTL": native_ban_ttl,
                    "nativeBanTempMaxExpires": native_ban_temp_max_expires,
                    "nativeBanPermMaxExpires": native_ban_perm_max_expires,
                },
                "relationships": {
                    "organization": {
                        "data": {"type": "organization", "id": str(organization_id)},
                    },
                    "owner": {"data": {"type": "organization", "id": str(owner_id)}},
                },
            },
        }
        return await self.request(
            Route(method="POST", path="/ban-lists/accept-invite"),
            json=data,
        )

    async def list_banlists(
        self,
        *,
        include: str | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """List ban lists you own or are subscribed to."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        if page_size:
            params["page[size]"] = page_size
        return await self.request(Route(method="GET", path="/ban-lists"), params=params)

    async def get_banlist(
        self,
        banlist_id: str,
        *,
        include: str | None = None,
    ) -> dict[str, Any]:
        """Get a specific ban list."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        return await self.request(
            Route(method="GET", path=f"/ban-lists/{banlist_id}"),
            params=params,
        )

    async def update_banlist(
        self,
        banlist_id: str,
        *,
        name: str | None = None,
        action: Literal["none", "log", "kick"] | None = None,
        default_identifiers: list[str] | None = None,
        default_reasons: list[str] | None = None,
        default_auto_add_enabled: bool | None = None,
        default_native_enabled: bool | None = None,
        native_ban_ttl: int | None = None,
        native_ban_temp_max_expires: int | None = None,
        native_ban_perm_max_expires: int | None = None,
    ) -> dict[str, Any]:
        """Update a ban list."""
        attributes = {
            "name": name,
            "action": action,
            "defaultIdentifiers": default_identifiers,
            "defaultReasons": default_reasons,
            "defaultAutoAddEnabled": default_auto_add_enabled,
            "defaultNativeEnabled": default_native_enabled,
            "nativeBanTTL": native_ban_ttl,
            "nativeBanTempMaxExpires": native_ban_temp_max_expires,
            "nativeBanPermMaxExpires": native_ban_perm_max_expires,
        }
        # remove None values
        attributes = {k: v for k, v in attributes.items() if v is not None}
        data = {"data": {"type": "banList", "id": banlist_id, "attributes": attributes}}
        return await self.request(
            Route(method="PATCH", path=f"/ban-lists/{banlist_id}"),
            json=data,
        )

    async def list_banlist_organizations(
        self,
        banlist_id: str,
        *,
        include: str | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """List organizations subscribed to a ban list."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        if page_size:
            params["page[size]"] = page_size
        return await self.request(
            Route(
                method="GET",
                path=f"/ban-lists/{banlist_id}/relationships/organizations",
            ),
            params=params,
        )

    async def get_banlist_subscription(
        self,
        banlist_id: str,
        organization_id: int,
        *,
        include: str | None = None,
    ) -> dict[str, Any]:
        """Read an organization's subscription to a ban list."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        return await self.request(
            Route(
                method="GET",
                path=f"/ban-lists/{banlist_id}/relationships/organizations/{organization_id}",
            ),
            params=params,
        )

    async def update_banlist_subscription(
        self,
        banlist_id: str,
        organization_id: int,
        *,
        perm_manage: bool | None = None,
        perm_create: bool | None = None,
        perm_update: bool | None = None,
        perm_delete: bool | None = None,
    ) -> dict[str, Any]:
        """Update an organization's subscription permissions for a ban list."""
        attributes = {
            "permManage": perm_manage,
            "permCreate": perm_create,
            "permUpdate": perm_update,
            "permDelete": perm_delete,
        }
        attributes = {k: v for k, v in attributes.items() if v is not None}
        data = {"data": {"type": "banList", "id": banlist_id, "attributes": attributes}}
        return await self.request(
            Route(
                method="PATCH",
                path=f"/ban-lists/{banlist_id}/relationships/organizations/{organization_id}",
            ),
            json=data,
        )

    async def unsubscribe_banlist(self, banlist_id: str, organization_id: int) -> None:
        """Unsubscribe an organization from a ban list."""
        await self.request(
            Route(
                method="DELETE",
                path=f"/ban-lists/{banlist_id}/relationships/organizations/{organization_id}",
            ),
        )

    # -------------------------- Ban List Invites ------------------------- #

    async def create_banlist_invite(
        self,
        banlist_id: str,
        *,
        limit: int | None = None,
        perm_manage: bool | None = None,
        perm_create: bool | None = None,
        perm_update: bool | None = None,
        perm_delete: bool | None = None,
        uses: int | None = None,
        organization_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a ban list invite."""
        attributes = {
            "limit": limit,
            "permManage": perm_manage,
            "permCreate": perm_create,
            "permUpdate": perm_update,
            "permDelete": perm_delete,
            "uses": uses,
        }
        attributes = {k: v for k, v in attributes.items() if v is not None}
        relationships: dict[str, Any] = {}
        if organization_id is not None:
            relationships["organization"] = {
                "data": {"type": "organization", "id": str(organization_id)},
            }
        data = {
            "data": {
                "type": "banListInvite",
                "attributes": attributes,
                "relationships": relationships,
            },
        }
        return await self.request(
            Route(method="POST", path=f"/ban-lists/{banlist_id}/relationships/invites"),
            json=data,
        )

    async def list_banlist_invites(
        self,
        banlist_id: str,
        *,
        include: str | None = None,
    ) -> dict[str, Any]:
        """List invites for a ban list."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        return await self.request(
            Route(method="GET", path=f"/ban-lists/{banlist_id}/relationships/invites"),
            params=params,
        )

    async def get_banlist_invite(
        self,
        invite_id: str,
        *,
        include: str | None = None,
    ) -> dict[str, Any]:
        """Get a specific ban list invite."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        return await self.request(
            Route(method="GET", path=f"/ban-list-invites/{invite_id}"),
            params=params,
        )

    async def delete_banlist_invite(self, invite_id: str) -> None:
        """Delete a ban list invite."""
        await self.request(
            Route(method="DELETE", path=f"/ban-list-invites/{invite_id}"),
        )

    # ----------------------------- Native Bans ---------------------------- #

    async def list_native_bans(
        self,
        *,
        ban_id: int | None = None,
        server_id: int | None = None,
        include: str | None = None,
        page_size: int | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List native bans (game specific)."""
        params: dict[str, Any] = {}
        if ban_id:
            params["filter[ban]"] = ban_id
        if server_id:
            params["filter[server]"] = server_id
        if include:
            params["include"] = include
        if page_size:
            params["page[size]"] = page_size
        if sort:
            params["sort"] = sort
        return await self.request(
            Route(method="GET", path="/bans-native"),
            params=params,
        )

    async def force_update_native_ban(self, native_ban_id: str) -> dict[str, Any]:
        """Force update a native ban."""
        return await self.request(
            Route(method="POST", path=f"/bans-native/{native_ban_id}/force-update"),
        )

    # --------------------------- Commands Activity ------------------------ #

    async def list_command_stats(
        self,
        organization_id: int,
        *,
        commands: list[str] | None = None,
        servers: list[int] | None = None,
        users: list[int] | None = None,
        timestamp_range: str | None = None,
        summary: bool | None = None,
    ) -> dict[str, Any]:
        """List command activity statistics for an organization."""
        params: dict[str, Any] = {}
        if commands:
            params["filter[commands]"] = ",".join(commands)
        if servers:
            params["filter[servers]"] = ",".join(map(str, servers))
        if users:
            params["filter[users]"] = ",".join(map(str, users))
        if timestamp_range:
            params["filter[timestamp]"] = timestamp_range
        if summary is not None:
            params["filter[summary]"] = str(summary).lower()
        return await self.request(
            Route(
                method="GET",
                path=f"/organizations/{organization_id}/relationships/command-stats",
            ),
            params=params,
        )

    # -------------------------------- Coplay ------------------------------ #

    async def list_coplay(
        self,
        player_id: int,
        *,
        period: str,
        players: list[int] | None = None,
        servers: list[int] | None = None,
        organizations: list[int] | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """List coplay data for a player."""
        params: dict[str, Any] = {"filter[period]": period}
        if players:
            params["filter[players]"] = ",".join(map(str, players))
        if servers:
            params["filter[servers]"] = ",".join(map(str, servers))
        if organizations:
            params["filter[organizations]"] = ",".join(map(str, organizations))
        if page_size:
            params["page[size]"] = page_size
        return await self.request(
            Route(method="GET", path=f"/players/{player_id}/relationships/coplay"),
            params=params,
        )

    # ------------------------------ Data Points --------------------------- #

    async def get_metrics(
        self,
        metrics: list[dict[str, Any]],
        *,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get data points for metrics. Each metric dict should include name, range, resolution."""
        params: dict[str, Any] = {}
        if fields:
            params["fields[dataPoint]"] = ",".join(fields)
        # Only first metric supported in this convenience wrapper; call multiple times for more.
        for metric in metrics:
            for key, value in metric.items():
                params[f"metrics[{key}]"] = value
            break  # only first metric for now (API supports multiple via different encoding)
        return await self.request(Route(method="GET", path="/metrics"), params=params)

    # ------------------------------ Player Flags -------------------------- #

    async def create_player_flag(
        self,
        *,
        organization_id: int,
        name: str,
        color: str | None = None,
        icon: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a player flag."""
        data = {
            "data": {
                "type": "playerFlag",
                "attributes": {
                    "name": name,
                    "color": color,
                    "icon": icon,
                    "description": description,
                },
                "relationships": {
                    "organization": {
                        "data": {"type": "organization", "id": str(organization_id)},
                    },
                },
            },
        }
        return await self.request(Route(method="POST", path="/player-flags"), json=data)

    async def get_player_flag(
        self,
        flag_id: str,
        *,
        include: str | None = None,
    ) -> dict[str, Any]:
        """Get a specific player flag."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        return await self.request(
            Route(method="GET", path=f"/player-flags/{flag_id}"),
            params=params,
        )

    async def list_player_flags(
        self,
        *,
        personal: bool | None = None,
        include: str | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """List player flags."""
        params: dict[str, Any] = {}
        if personal is not None:
            params["filter[personal]"] = str(personal).lower()
        if include:
            params["include"] = include
        if page_size:
            params["page[size]"] = page_size
        return await self.request(
            Route(method="GET", path="/player-flags"),
            params=params,
        )

    async def update_player_flag(
        self,
        flag_id: str,
        *,
        name: str | None = None,
        color: str | None = None,
        icon: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Update a player flag."""
        attributes = {
            "name": name,
            "color": color,
            "icon": icon,
            "description": description,
        }
        attributes = {k: v for k, v in attributes.items() if v is not None}
        data = {"data": {"type": "playerFlag", "id": flag_id, "attributes": attributes}}
        return await self.request(
            Route(method="PATCH", path=f"/player-flags/{flag_id}"),
            json=data,
        )

    async def delete_player_flag(self, flag_id: str) -> None:
        """Delete a player flag."""
        await self.request(Route(method="DELETE", path=f"/player-flags/{flag_id}"))

    async def list_player_flag_assignments(
        self,
        player_id: int,
        *,
        include: str | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """List flags applied to a player."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        if page_size:
            params["page[size]"] = page_size
        return await self.request(
            Route(method="GET", path=f"/players/{player_id}/relationships/flags"),
            params=params,
        )

    async def add_player_flag_assignment(
        self,
        player_id: int,
        player_flag_id: str,
    ) -> dict[str, Any]:
        """Add a flag to a player."""
        data = {
            "data": {
                "type": "flagPlayer",
                "relationships": {
                    "playerFlag": {
                        "data": {"type": "playerFlag", "id": player_flag_id},
                    },
                },
            },
        }
        return await self.request(
            Route(method="POST", path=f"/players/{player_id}/relationships/flags"),
            json=data,
        )

    async def remove_player_flag_assignment(
        self,
        player_id: int,
        player_flag_id: str,
    ) -> None:
        """Remove a flag from a player."""
        await self.request(
            Route(
                method="DELETE",
                path=f"/players/{player_id}/relationships/flags/{player_flag_id}",
            ),
        )

    # --------------------------------- Games ------------------------------ #

    async def list_games(self, *, page_size: int | None = None) -> dict[str, Any]:
        """List supported games."""
        params: dict[str, Any] = {}
        if page_size:
            params["page[size]"] = page_size
        return await self.request(Route(method="GET", path="/games"), params=params)

    async def get_game(self, game_id: str) -> dict[str, Any]:
        """Get information about a game."""
        return await self.request(Route(method="GET", path=f"/games/{game_id}"))

    # ---------------------------- Game Features --------------------------- #

    async def list_game_features(
        self,
        *,
        game: str | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """List game features (filter by game optionally)."""
        params: dict[str, Any] = {}
        if game:
            params["filter[game]"] = game
        if page_size:
            params["page[size]"] = page_size
        return await self.request(
            Route(method="GET", path="/game-features"),
            params=params,
        )

    async def list_game_feature_options(
        self,
        feature_id: str,
        *,
        page_size: int | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List options for a given game feature."""
        params: dict[str, Any] = {}
        if page_size:
            params["page[size]"] = page_size
        if sort:
            params["sort"] = sort
        return await self.request(
            Route(
                method="GET",
                path=f"/game-features/{feature_id}/relationships/options",
            ),
            params=params,
        )

    # ------------------------------ Leaderboards ------------------------- #

    async def get_leaderboard(
        self,
        server_id: int,
        *,
        period: str,
        player_id: int | None = None,
        leaderboard: str = "time",
        page_size: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Get leaderboard data for a server (e.g. time)."""
        params: dict[str, Any] = {"filter[period]": period}
        if player_id is not None:
            params["filter[player]"] = player_id
        if page_size:
            params["page[size]"] = page_size
        if offset is not None:
            params["page[offset]"] = offset
        return await self.request(
            Route(
                method="GET",
                path=f"/servers/{server_id}/relationships/leaderboards/{leaderboard}",
            ),
            params=params,
        )

    # ---------------------------- Organization Stats --------------------- #

    async def get_organization_player_stats(
        self,
        organization_id: int,
        *,
        range_: str,
        game: str | None = None,
        group: str | None = None,
    ) -> dict[str, Any]:
        """Get organization player stats."""
        params: dict[str, Any] = {"filter[range]": range_}
        if game:
            params["filter[game]"] = game
        if group:
            params["filter[group]"] = group
        return await self.request(
            Route(method="GET", path=f"/organizations/{organization_id}/stats/players"),
            params=params,
        )

    # -------------------------------- Players ----------------------------- #

    async def list_players(
        self,
        *,
        search: str | None = None,
        servers: list[int] | None = None,
        organizations: list[int] | None = None,
        game: str | None = None,
        page_size: int | None = None,
        sort: str | None = None,
        online: bool | None = None,
    ) -> dict[str, Any]:
        """List/search players."""
        params: dict[str, Any] = {}
        if search:
            params["filter[search]"] = search
        if servers:
            params["filter[servers]"] = ",".join(map(str, servers))
        if organizations:
            params["filter[organizations]"] = ",".join(map(str, organizations))
        if game:
            params["filter[server][game]"] = game
        if page_size:
            params["page[size]"] = page_size
        if sort:
            params["sort"] = sort
        if online is not None:
            params["filter[online]"] = str(online).lower()
        return await self.request(Route(method="GET", path="/players"), params=params)

    async def get_player(
        self,
        player_id: int,
        *,
        include: str | None = None,
    ) -> dict[str, Any]:
        """Get player information."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        return await self.request(
            Route(method="GET", path=f"/players/{player_id}"),
            params=params,
        )

    async def match_players(self, identifiers: list[dict[str, str]]) -> dict[str, Any]:
        """Match players by identifiers (slow full match)."""
        data = {
            "data": [
                {"type": "identifier", "attributes": ident} for ident in identifiers
            ],
        }
        return await self.request(
            Route(method="POST", path="/players/match"),
            json=data,
        )

    async def quick_match_players(
        self,
        identifiers: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Quick match players by identifiers."""
        data = {
            "data": [
                {"type": "identifier", "attributes": ident} for ident in identifiers
            ],
        }
        return await self.request(
            Route(method="POST", path="/players/quick-match"),
            json=data,
        )

    async def player_time_played_history(
        self,
        player_id: int,
        server_id: int,
        *,
        start: str,
        stop: str,
    ) -> dict[str, Any]:
        """Get a player's time played history for a server."""
        params = {"start": start, "stop": stop}
        return await self.request(
            Route(
                method="GET",
                path=f"/players/{player_id}/time-played-history/{server_id}",
            ),
            params=params,
        )

    async def get_player_server_info(
        self,
        player_id: int,
        server_id: int,
    ) -> dict[str, Any]:
        """Get player information for a specific server."""
        return await self.request(
            Route(method="GET", path=f"/players/{player_id}/servers/{server_id}"),
        )

    async def player_session_history(
        self,
        player_id: int,
        *,
        servers: list[int] | None = None,
        organizations: list[int] | None = None,
        page_size: int | None = None,
        include: str | None = None,
    ) -> dict[str, Any]:
        """Get a player's session history."""
        params: dict[str, Any] = {}
        if servers:
            params["filter[servers]"] = ",".join(map(str, servers))
        if organizations:
            params["filter[organizations]"] = ",".join(map(str, organizations))
        if page_size:
            params["page[size]"] = page_size
        if include:
            params["include"] = include
        return await self.request(
            Route(method="GET", path=f"/players/{player_id}/relationships/sessions"),
            params=params,
        )

    async def related_identifiers(
        self,
        player_id: int,
        *,
        match_identifiers: list[str] | None = None,
        identifiers: list[str] | None = None,
        page_size: int | None = None,
        include: str | None = None,
    ) -> dict[str, Any]:
        """Get related identifiers for a player."""
        params: dict[str, Any] = {}
        if match_identifiers:
            params["filter[matchIdentifiers]"] = ",".join(match_identifiers)
        if identifiers:
            params["filter[identifiers]"] = ",".join(identifiers)
        if page_size:
            params["page[size]"] = page_size
        if include:
            params["include"] = include
        return await self.request(
            Route(
                method="GET",
                path=f"/players/{player_id}/relationships/related-identifiers",
            ),
            params=params,
        )

    # ----------------------------- Player Queries ------------------------- #

    async def list_player_queries(
        self,
        *,
        organizations: list[int] | None = None,
        ids: list[str] | None = None,
        sort: str | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """List related player queries."""
        params: dict[str, Any] = {}
        if organizations:
            params["filter[organizations]"] = ",".join(map(str, organizations))
        if ids:
            params["filter[ids]"] = ",".join(ids)
        if sort:
            params["sort"] = sort
        if page_size:
            params["page[size]"] = page_size
        return await self.request(
            Route(method="GET", path="/player-queries"),
            params=params,
        )

    async def get_player_query(self, query_id: str) -> dict[str, Any]:
        """Get a related player query."""
        return await self.request(
            Route(method="GET", path=f"/player-queries/{query_id}"),
        )

    async def create_player_query(
        self,
        organization_id: int,
        *,
        query_name: str,
        conditions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create a related player query."""
        data = {
            "data": {
                "type": "playerQuery",
                "attributes": {"queryName": query_name, "conditions": conditions},
                "relationships": {
                    "organization": {
                        "data": {"type": "organization", "id": str(organization_id)},
                    },
                },
            },
        }
        return await self.request(
            Route(method="POST", path="/player-queries"),
            json=data,
        )

    async def update_player_query(
        self,
        query_id: str,
        *,
        query_name: str | None = None,
        conditions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Update a related player query."""
        attributes = {"queryName": query_name, "conditions": conditions}
        attributes = {k: v for k, v in attributes.items() if v is not None}
        data = {
            "data": {"type": "playerQuery", "id": query_id, "attributes": attributes},
        }
        return await self.request(
            Route(method="PATCH", path=f"/player-queries/{query_id}"),
            json=data,
        )

    async def delete_player_query(self, query_id: str) -> None:
        """Delete a saved related player query."""
        await self.request(Route(method="DELETE", path=f"/player-queries/{query_id}"))

    async def run_player_query(
        self,
        player_id: int,
        query_id: str,
        *,
        identifiers: list[str] | None = None,
        include: str | None = None,
        page_size: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Run a saved related player query for a player."""
        params: dict[str, Any] = {}
        if identifiers:
            params["filter[identifiers]"] = ",".join(identifiers)
        if include:
            params["include"] = include
        if page_size:
            params["page[size]"] = page_size
        if offset is not None:
            params["page[offset]"] = offset
        return await self.request(
            Route(
                method="GET",
                path=f"/players/{player_id}/relationships/player-query/{query_id}",
            ),
            params=params,
        )

    async def run_custom_player_query(
        self,
        player_id: int,
        *,
        conditions: list[dict[str, Any]],
        identifiers: list[str] | None = None,
        include: str | None = None,
        page_size: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Run a custom related player query (not saved) for a player."""
        params: dict[str, Any] = {}
        if identifiers:
            params["filter[identifiers]"] = ",".join(identifiers)
        if include:
            params["include"] = include
        if page_size:
            params["page[size]"] = page_size
        if offset is not None:
            params["page[offset]"] = offset
        data = {
            "data": {
                "type": "playerQuery",
                "attributes": {"conditions": conditions},
            },
        }
        return await self.request(
            Route(
                method="POST",
                path=f"/players/{player_id}/relationships/player-query",
            ),
            params=params,
            json=data,
        )

    # ----------------------------- Reserved Slots ------------------------- #

    async def create_reserved_slot(
        self,
        *,
        player_id: int,
        organization_id: int,
        server_ids: list[int],
        identifiers: list[str | dict[str, Any]] | None = None,
        expires: str | None = None,
    ) -> dict[str, Any]:
        """Create a reserved slot."""
        data = {
            "data": {
                "type": "reservedSlot",
                "attributes": {"expires": expires, "identifiers": identifiers or []},
                "relationships": {
                    "player": {"data": {"type": "player", "id": str(player_id)}},
                    "servers": {
                        "data": [
                            {"type": "server", "id": str(sid)} for sid in server_ids
                        ],
                    },
                    "organization": {
                        "data": {"type": "organization", "id": str(organization_id)},
                    },
                },
            },
        }
        return await self.request(
            Route(method="POST", path="/reserved-slots"),
            json=data,
        )

    async def get_reserved_slot(
        self,
        slot_id: str,
        *,
        include: str | None = None,
    ) -> dict[str, Any]:
        """Get a reserved slot."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        return await self.request(
            Route(method="GET", path=f"/reserved-slots/{slot_id}"),
            params=params,
        )

    async def list_reserved_slots(
        self,
        *,
        organization_id: int | None = None,
        player_id: int | None = None,
        server_id: int | None = None,
        search: str | None = None,
        expired: bool | None = None,
        include: str | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """List reserved slots."""
        params: dict[str, Any] = {}
        if organization_id:
            params["filter[organization]"] = organization_id
        if player_id:
            params["filter[player]"] = player_id
        if server_id:
            params["filter[server]"] = server_id
        if search:
            params["filter[search]"] = search
        if expired is not None:
            params["filter[expired]"] = str(expired).lower()
        if include:
            params["include"] = include
        if page_size:
            params["page[size]"] = page_size
        return await self.request(
            Route(method="GET", path="/reserved-slots"),
            params=params,
        )

    async def update_reserved_slot(
        self,
        slot_id: str,
        *,
        identifiers: list[str | dict[str, Any]] | None = None,
        expires: str | None = None,
        server_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Update a reserved slot."""
        attributes = {"identifiers": identifiers or [], "expires": expires}
        relationships: dict[str, Any] = {}
        if server_ids is not None:
            relationships["servers"] = {
                "data": [{"type": "server", "id": str(sid)} for sid in server_ids],
            }
        data = {
            "data": {
                "type": "reservedSlot",
                "id": slot_id,
                "attributes": attributes,
                "relationships": relationships,
            },
        }
        return await self.request(
            Route(method="PATCH", path=f"/reserved-slots/{slot_id}"),
            json=data,
        )

    async def delete_reserved_slot(self, slot_id: str) -> None:
        """Delete a reserved slot."""
        await self.request(Route(method="DELETE", path=f"/reserved-slots/{slot_id}"))

    # -------------------------------- Servers ----------------------------- #

    async def list_servers(
        self,
        *,
        search: str | None = None,
        game: str | None = None,
        status: str | None = None,
        countries: list[str] | None = None,
        page_size: int | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List/search servers."""
        params: dict[str, Any] = {}
        if search:
            params["filter[search]"] = search
        if game:
            params["filter[game]"] = game
        if status:
            params["filter[status]"] = status
        if countries:
            # API accepts repeated countries or comma-separated; we use comma-separated list
            params["filter[countries]"] = ",".join(countries)
        if page_size:
            params["page[size]"] = page_size
        if sort:
            params["sort"] = sort
        return await self.request(Route(method="GET", path="/servers"), params=params)

    async def get_server(
        self,
        server_id: int,
        *,
        include: str | None = None,
    ) -> dict[str, Any]:
        """Get server information."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        return await self.request(
            Route(method="GET", path=f"/servers/{server_id}"),
            params=params,
        )

    async def server_player_count_history(
        self,
        server_id: int,
        *,
        start: str,
        stop: str,
        resolution: Literal["raw", "30", "60", "1440"] | None = None,
    ) -> dict[str, Any]:
        """Get server player count history."""
        params: dict[str, Any] = {"start": start, "stop": stop}
        if resolution:
            params["resolution"] = resolution
        return await self.request(
            Route(method="GET", path=f"/servers/{server_id}/player-count-history"),
            params=params,
        )

    async def server_rank_history(
        self,
        server_id: int,
        *,
        start: str,
        stop: str,
    ) -> dict[str, Any]:
        """Get server rank history."""
        params = {"start": start, "stop": stop}
        return await self.request(
            Route(method="GET", path=f"/servers/{server_id}/rank-history"),
            params=params,
        )

    async def server_group_rank_history(
        self,
        server_id: int,
        *,
        start: str,
        stop: str,
    ) -> dict[str, Any]:
        """Get server group rank history."""
        params = {"start": start, "stop": stop}
        return await self.request(
            Route(method="GET", path=f"/servers/{server_id}/group-rank-history"),
            params=params,
        )

    async def server_time_played_history(
        self,
        server_id: int,
        *,
        start: str,
        stop: str,
    ) -> dict[str, Any]:
        """Get server time played history."""
        params = {"start": start, "stop": stop}
        return await self.request(
            Route(method="GET", path=f"/servers/{server_id}/time-played-history"),
            params=params,
        )

    async def server_unique_player_history(
        self,
        server_id: int,
        *,
        start: str,
        stop: str,
    ) -> dict[str, Any]:
        """Get server unique player history."""
        params = {"start": start, "stop": stop}
        return await self.request(
            Route(method="GET", path=f"/servers/{server_id}/unique-player-history"),
            params=params,
        )

    async def server_sessions(
        self,
        server_id: int,
        *,
        start: str | None = None,
        stop: str | None = None,
        at: str | None = None,
        include: str | None = None,
    ) -> dict[str, Any]:
        """List sessions for a server (relationships endpoint)."""
        params: dict[str, Any] = {}
        if start:
            params["start"] = start
        if stop:
            params["stop"] = stop
        if at:
            params["at"] = at
        if include:
            params["include"] = include
        return await self.request(
            Route(method="GET", path=f"/servers/{server_id}/relationships/sessions"),
            params=params,
        )

    async def server_outages(
        self,
        server_id: int,
        *,
        range_: str | None = None,
        include: str | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """Get server outage history."""
        params: dict[str, Any] = {}
        if range_:
            params["filter[range]"] = range_
        if include:
            params["include"] = include
        if page_size:
            params["page[size]"] = page_size
        return await self.request(
            Route(method="GET", path=f"/servers/{server_id}/relationships/outages"),
            params=params,
        )

    async def server_downtime(
        self,
        server_id: int,
        *,
        start: str,
        stop: str,
        include: str | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """Get server downtime history."""
        params: dict[str, Any] = {"start": start, "stop": stop}
        if include:
            params["include"] = include
        if page_size:
            params["page[size]"] = page_size
        return await self.request(
            Route(method="GET", path=f"/servers/{server_id}/relationships/downtime"),
            params=params,
        )

    async def server_first_time_history(
        self,
        server_id: int,
        *,
        start: str,
        stop: str,
    ) -> dict[str, Any]:
        """Get server first-time player history."""
        params = {"start": start, "stop": stop}
        return await self.request(
            Route(method="GET", path=f"/servers/{server_id}/first-time-history"),
            params=params,
        )

    async def create_server(
        self,
        *,
        game: str,
        ip: str,
        port: int,
        port_query: int,
        organization_id: int,
    ) -> dict[str, Any]:
        """Create a server."""
        data = {
            "data": {
                "type": "server",
                "attributes": {
                    "ip": ip,
                    "port": port,
                    "portQuery": port_query,
                },
                "relationships": {
                    "game": {"data": {"type": "game", "id": game}},
                    "organization": {
                        "data": {"type": "organization", "id": str(organization_id)},
                    },
                },
            },
        }
        return await self.request(Route(method="POST", path="/servers"), json=data)

    async def update_server(
        self,
        server_id: int,
        *,
        metadata: dict[str, Any] | None = None,
        port_query: int | None = None,
        default_ban_list_id: str | None = None,
        server_group_id: str | None = None,
    ) -> dict[str, Any]:
        """Update a server."""
        attributes: dict[str, Any] = {}
        if metadata is not None:
            attributes["metadata"] = metadata
        if port_query is not None:
            attributes["portQuery"] = port_query
        relationships: dict[str, Any] = {}
        if default_ban_list_id is not None:
            relationships["defaultBanList"] = {
                "data": {"type": "banList", "id": default_ban_list_id},
            }
        if server_group_id is not None:
            relationships["serverGroup"] = {
                "data": {"type": "serverGroup", "id": server_group_id},
            }
        data: dict[str, Any] = {
            "data": {
                "type": "server",
                "id": str(server_id),
                "attributes": attributes,
            },
        }
        if relationships:
            data["data"]["relationships"] = relationships
        return await self.request(
            Route(method="PATCH", path=f"/servers/{server_id}"),
            json=data,
        )

    async def enable_server_rcon(
        self,
        server_id: int,
        *,
        password: str,
        port: int | None = None,
        ip: str | None = None,
    ) -> dict[str, Any]:
        """Enable RCON for a server."""
        attributes: dict[str, Any] = {"password": password}
        if port is not None:
            attributes["port"] = port
        if ip is not None:
            attributes["ip"] = ip
        data = {
            "data": {
                "type": "server",
                "attributes": {"rcon": attributes},
            },
        }
        return await self.request(
            Route(method="POST", path=f"/servers/{server_id}/rcon"),
            json=data,
        )

    async def delete_server_rcon(self, server_id: int) -> None:
        """Delete RCON configuration for a server."""
        await self.request(Route(method="DELETE", path=f"/servers/{server_id}/rcon"))

    async def disconnect_server_rcon(self, server_id: int) -> None:
        """Disconnect RCON for a server."""
        await self.request(
            Route(method="DELETE", path=f"/servers/{server_id}/rcon/disconnect"),
        )

    async def connect_server_rcon(self, server_id: int) -> None:
        """Connect RCON for a server."""
        await self.request(
            Route(method="DELETE", path=f"/servers/{server_id}/rcon/connect"),
        )

    async def force_update_server(self, server_id: int) -> dict[str, Any]:
        """Force update a server."""
        return await self.request(
            Route(method="POST", path=f"/servers/{server_id}/force-update"),
        )

    # -------------------------------- Sessions ---------------------------- #

    async def list_sessions(
        self,
        *,
        servers: list[int] | None = None,
        games: list[str] | None = None,
        organizations: list[int] | None = None,
        players: list[int] | None = None,
        identifiers: list[str] | None = None,
        range_: str | None = None,
        at: str | None = None,
        include: str | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """List sessions."""
        params: dict[str, Any] = {}
        if servers:
            params["filter[servers]"] = ",".join(map(str, servers))
        if games:
            params["filter[games]"] = ",".join(games)
        if organizations:
            params["filter[organizations]"] = ",".join(map(str, organizations))
        if players:
            params["filter[players]"] = ",".join(map(str, players))
        if identifiers:
            params["filter[identifiers]"] = ",".join(identifiers)
        if range_:
            params["filter[range]"] = range_
        if at:
            params["filter[at]"] = at
        if include:
            params["include"] = include
        if page_size:
            params["page[size]"] = page_size
        return await self.request(Route(method="GET", path="/sessions"), params=params)

    async def get_session(
        self,
        session_id: str,
        *,
        include: str | None = None,
    ) -> dict[str, Any]:
        """Get a specific session."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        return await self.request(
            Route(method="GET", path=f"/sessions/{session_id}"),
            params=params,
        )

    async def session_coplay(
        self,
        session_id: str,
        *,
        page_size: int | None = None,
        include: str | None = None,
    ) -> dict[str, Any]:
        """Get coplay data for a session."""
        params: dict[str, Any] = {}
        if page_size:
            params["page[size]"] = page_size
        if include:
            params["include"] = include
        return await self.request(
            Route(method="GET", path=f"/sessions/{session_id}/relationships/coplay"),
            params=params,
        )

    # --------------------------------- Users ------------------------------ #

    async def get_user(self, user_id: int) -> dict[str, Any]:
        """Get user information."""
        return await self.request(Route(method="GET", path=f"/users/{user_id}"))

    # -------------------------------- Player Notes ----------------------- #

    async def list_player_notes(
        self,
        player_id: int,
        *,
        expired: bool | None = None,
        organizations: list[int] | None = None,
        personal: bool | None = None,
        search: str | None = None,
        users: list[int] | None = None,
        include: str | None = None,
        page_size: int | None = None,
        page_key: str | None = None,
        page_rel: Literal["next", "prev"] | None = None,
    ) -> dict[str, Any]:
        """List player notes for a player."""
        params: dict[str, Any] = {}
        if expired is not None:
            params["filter[expired]"] = str(expired).lower()
        if organizations:
            params["filter[organizations]"] = ",".join(map(str, organizations))
        if personal is not None:
            params["filter[personal]"] = str(personal).lower()
        if search:
            params["filter[search]"] = search
        if users:
            params["filter[users]"] = ",".join(map(str, users))
        if include:
            params["include"] = include
        if page_size:
            params["page[size]"] = page_size
        if page_key:
            params["page[key]"] = page_key
        if page_rel:
            params["page[rel]"] = page_rel
        return await self.request(
            Route(method="GET", path=f"/players/{player_id}/relationships/notes"),
            params=params,
        )

    async def get_player_note(self, player_id: int, note_id: str) -> dict[str, Any]:
        """Get a specific player note."""
        return await self.request(
            Route(
                method="GET",
                path=f"/players/{player_id}/relationships/notes/{note_id}",
            ),
        )

    async def create_player_note(
        self,
        player_id: int,
        *,
        note: str,
        shared: bool,
        expires_at: str | None = None,
        clearance_level: int | None = None,
        organization_id: int | None = None,
        trigger_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a player note."""
        relationships: dict[str, Any] = {
            "player": {"data": {"type": "player", "id": str(player_id)}},
        }
        if organization_id is not None:
            relationships["organization"] = {
                "data": {"type": "organization", "id": str(organization_id)},
            }
        if trigger_id is not None:
            relationships["trigger"] = {
                "data": {"type": "trigger", "id": trigger_id},
            }
        data = {
            "data": {
                "type": "playerNote",
                "attributes": {
                    "note": note,
                    "shared": shared,
                    "expiresAt": expires_at,
                    "clearanceLevel": clearance_level,
                },
                "relationships": relationships,
            },
        }
        return await self.request(
            Route(method="POST", path=f"/players/{player_id}/relationships/notes"),
            json=data,
        )

    async def update_player_note(
        self,
        player_id: int,
        note_id: str,
        *,
        note: str | None = None,
        shared: bool | None = None,
        expires_at: str | None = None,
        clearance_level: int | None = None,
    ) -> dict[str, Any]:
        """Update a player note."""
        attributes = {
            "note": note,
            "shared": shared,
            "expiresAt": expires_at,
            "clearanceLevel": clearance_level,
        }
        attributes = {k: v for k, v in attributes.items() if v is not None}
        data = {
            "data": {
                "type": "playerNote",
                "id": note_id,
                "attributes": attributes,
            },
        }
        return await self.request(
            Route(
                method="PATCH",
                path=f"/players/{player_id}/relationships/notes/{note_id}",
            ),
            json=data,
        )

    async def delete_player_note(self, player_id: int, note_id: str) -> None:
        """Delete a player note."""
        await self.request(
            Route(
                method="DELETE",
                path=f"/players/{player_id}/relationships/notes/{note_id}",
            ),
        )

    # -------------------------- Organization Friends ----------------------- #

    async def list_organization_friends(
        self,
        organization_id: int,
        *,
        include: str | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """List organization friends."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        if page_size:
            params["page[size]"] = page_size
        return await self.request(
            Route(
                method="GET",
                path=f"/organizations/{organization_id}/relationships/friends",
            ),
            params=params,
        )

    async def get_organization_friend(
        self,
        organization_id: int,
        friend_id: int,
        *,
        include: str | None = None,
    ) -> dict[str, Any]:
        """Get a specific organization friend."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        return await self.request(
            Route(
                method="GET",
                path=f"/organizations/{organization_id}/relationships/friends/{friend_id}",
            ),
            params=params,
        )

    async def create_organization_friend(
        self,
        organization_id: int,
        friend_id: int,
        *,
        identifiers: list[str] | None = None,
        notes: bool = False,
        player_flags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create an organization friend request."""
        relationships: dict[str, Any] = {
            "friend": {"data": {"type": "organization", "id": str(friend_id)}},
        }
        if player_flags:
            relationships["playerFlags"] = {
                "data": [
                    {"type": "playerFlag", "id": flag_id} for flag_id in player_flags
                ],
            }
        data = {
            "data": {
                "type": "organizationFriend",
                "attributes": {
                    "identifiers": identifiers or [],
                    "notes": notes,
                },
                "relationships": relationships,
            },
        }
        return await self.request(
            Route(
                method="POST",
                path=f"/organizations/{organization_id}/relationships/friends",
            ),
            json=data,
        )

    async def update_organization_friend(
        self,
        organization_id: int,
        friend_id: int,
        *,
        identifiers: list[str] | None = None,
        notes: bool | None = None,
        player_flags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update an organization friend."""
        attributes: dict[str, Any] = {}
        if identifiers is not None:
            attributes["identifiers"] = identifiers
        if notes is not None:
            attributes["notes"] = notes
        relationships: dict[str, Any] = {}
        if player_flags is not None:
            relationships["playerFlags"] = {
                "data": [
                    {"type": "playerFlag", "id": flag_id} for flag_id in player_flags
                ],
            }
        data: dict[str, Any] = {
            "data": {
                "type": "organizationFriend",
                "attributes": attributes,
            },
        }
        if relationships:
            data["data"]["relationships"] = relationships
        return await self.request(
            Route(
                method="PATCH",
                path=f"/organizations/{organization_id}/relationships/friends/{friend_id}",
            ),
            json=data,
        )

    async def delete_organization_friend(
        self,
        organization_id: int,
        friend_id: int,
    ) -> None:
        """Delete an organization friend."""
        await self.request(
            Route(
                method="DELETE",
                path=f"/organizations/{organization_id}/relationships/friends/{friend_id}",
            ),
        )

    async def bulk_delete_organization_friends(
        self,
        organization_id: int,
        friend_ids: list[int],
    ) -> None:
        """Bulk delete organization friends."""
        data = {
            "data": [{"type": "organization", "id": str(fid)} for fid in friend_ids],
        }
        await self.request(
            Route(
                method="DELETE",
                path=f"/organizations/{organization_id}/relationships/friends",
            ),
            json=data,
        )
