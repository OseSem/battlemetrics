from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
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
    data: Any,
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


async def calculate_future_date(input_string: str) -> str | None:
    # Extract the numeric part and unit from the input string
    number = int(input_string[:-1])
    unit = input_string[-1]

    # Define a dictionary to map units to timedelta objects
    unit_to_timedelta = {
        "d": timedelta(days=number),
        "w": timedelta(weeks=number),
        "m": timedelta(minutes=number),  # Approximate for months
        "h": timedelta(hours=number),
        "s": timedelta(seconds=number),  # Hours
    }

    # Get the timedelta object based on the unit
    delta: timedelta = unit_to_timedelta.get(unit, timedelta())

    if delta:
        # Calculate the future date by adding the timedelta to the current date
        future_date = str(datetime.now(tz=UTC) + delta)
        future_date = future_date.replace(" ", "T")
        future_date += "Z"
        return future_date

    return None
