from typing import Any, NamedTuple

__all__ = (
    "APIScopes",
    "Metrics",
    "ActivityLogs",
)

# TODO: Add attrubites in docstrings for all these classes.


class APIScopes(NamedTuple):
    """All types for the function check_api_scopes."""

    active: bool
    scopes: list[str]
    client_id: str
    token_type: str | None


# TODO: Add better type for timestamp.
class Metrics(NamedTuple):
    """All types for the function metrics."""

    type: str
    timestamp: str
    value: int


# TODO: Better types.
class ActivityLogs(NamedTuple):
    """All types for the function activity_logs."""

    data: list[Any]
    included: list[Any]
    links: dict[str, Any]
