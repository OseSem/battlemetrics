# BattleMetrics API Wrapper

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![PyPI - Version](https://img.shields.io/pypi/v/battlemetrics)
![PyPI - Downloads](https://img.shields.io/pypi/dm/battlemetrics)


An async Python wrapper for the BattleMetrics API with full type safety using Pydantic models.

>[!CAUTION]
> This API Wrapper is very new and partly untested. Please report any issues instantly.

>[!NOTE]
> Since the BattleMetrics API Documentation is partly finished not every endpoint might be included. Make an Issue Report for any missing endpoints.

## Installation

To install the latest published version off of PyPI, you can run the following command:

```bash
pip install battlemetrics
```

To install the development version from GitHub (requires Git):
```bash
pip install git+https://github.com/OseSem/battlemetrics
```

## Usage

### Basic Example

```python
import asyncio
from battlemetrics import Battlemetrics

async def main():
    client = Battlemetrics("your-api-key")

    # Get server information
    server = await client.get_server(12345)
    print(f"Server: {server.attributes.name}")
    print(f"Players: {server.attributes.players}/{server.attributes.max_players}")

    await client.close()

asyncio.run(main())
```

### Using the Context Manager

```python
import asyncio
from battlemetrics import Battlemetrics

async def main():
    async with Battlemetrics("your-api-key") as client:
        # Search for players
        players = await client.list_players(search="username", game="rust")
        for player in players:
            print(f"Player: {player.attributes.name} (ID: {player.id})")

        # Get player session history
        if players:
            sessions = await client.player_session_history(players[0].id)
            for session in sessions:
                print(f"Session: {session.attributes.start} - {session.attributes.stop}")

asyncio.run(main())
```

### Searching for Servers

```python
import asyncio
from battlemetrics import Battlemetrics

async def main():
    async with Battlemetrics("your-api-key") as client:
        # Search for Rust servers in the US
        servers = await client.list_servers(
            search="vanilla",
            game="rust",
            countries=["US"],
            page_size=10
        )
        for server in servers:
            print(f"{server.attributes.name} - {server.attributes.players} players")

asyncio.run(main())
```
