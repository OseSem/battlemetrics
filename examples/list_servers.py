"""Search for game servers with filters."""

import asyncio
import os

from battlemetrics import Battlemetrics


async def main() -> None:
    api_key = os.environ.get("BATTLEMETRICS_API_KEY")

    async with Battlemetrics(api_key) as client:
        servers = await client.list_servers(
            game="rust",
            countries=["US"],
            page_size=10,
        )

        for server in servers:
            print(f"{server.attributes.name} - {server.attributes.players} players")


if __name__ == "__main__":
    asyncio.run(main())
