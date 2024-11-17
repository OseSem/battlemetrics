from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

__all__ = (
    "remove_html_tags",
    "format_relationships",
)


def remove_html_tags(text: str) -> str:
    """Remove HTML tags from a string."""
    return re.compile(r"<[^>]+>").sub("", text)


def format_relationships(
    data: Any,  # noqa: ANN401
) -> dict[str, int | str]:
    """Format the relationships data."""
    if not data:
        msg = "No relationships found."
        raise ValueError(msg)

    new_data: dict[str, str | int] = {}
    if data:
        for key, value in data.items():
            name = f"{key}_id"
            new_data[name] = (
                int(value.get("data").get("id"))
                if isinstance(value.get("data").get("id"), int)
                else value.get("data").get("id")
            )

    return new_data
