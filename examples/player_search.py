"""Search for players and view their session history."""

import asyncio
import os

from battlemetrics import Battlemetrics


async def main() -> None:
    api_key = os.environ.get("BATTLEMETRICS_API_KEY")

    async with Battlemetrics(api_key) as client:
        players = await client.list_players(search="shroud", page_size=5)

        for player in players:
            print(f"{player.attributes.name} (ID: {player.id})")

        # Get session history for first player
        if players:
            sessions = await client.player_session_history(int(players[0].id))
            for session in sessions[:5]:
                print(f"  {session.attributes.start} - {session.attributes.stop}")


if __name__ == "__main__":
    asyncio.run(main())
