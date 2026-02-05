"""Fetch and display basic server information."""

import asyncio
import os

from battlemetrics import Battlemetrics


async def main() -> None:
    api_key = os.environ.get("BATTLEMETRICS_API_KEY")

    async with Battlemetrics(api_key) as client:
        server = await client.get_server(1234567)

        print(f"Server: {server.attributes.name}")
        print(f"Players: {server.attributes.players}/{server.attributes.max_players}")
        print(f"Status: {server.attributes.status}")


if __name__ == "__main__":
    asyncio.run(main())
