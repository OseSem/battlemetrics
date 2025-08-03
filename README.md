# BattleMetrics API Wrapper

An async Python wrapper for the BattleMetrics API with full type safety using Pydantic models.

## Features

- 🚀 **Async/await support** - Built with aiohttp for efficient async operations
- 🔒 **Type safety** - Full type hints and Pydantic models for all API responses  
- ⚡ **Rate limiting** - Built-in rate limiting with exponential backoff
- 🛡️ **Error handling** - Comprehensive error handling with custom exceptions
- 🎮 **Complete coverage** - Support for all major BattleMetrics endpoints

## Installation

```bash
poetry install
```

## Quick Start

```python
import asyncio
from battlemetrics import BattleMetricsClient

async def main():
    async with BattleMetricsClient(api_token="your_api_token") as client:
        # Get games
        games = await client.get_games()
        print(f"Found {len(games.data)} games")
        
        # Get servers for a specific game
        servers = await client.get_servers(game="rust", page_size=10)
        for server in servers.data:
            if server.attributes:
                print(f"Server: {server.attributes.name}")

asyncio.run(main())
```

## Authentication

To use authenticated endpoints, you need a BattleMetrics API token:

1. Go to [BattleMetrics Developer Portal](https://www.battlemetrics.com/developers)
2. Create an application and get your API token
3. Set it as an environment variable:

```python
import os
client = BattleMetricsClient(api_token=os.getenv("BATTLEMETRICS_API_TOKEN"))
```

## API Coverage

### Servers
```python
# List servers
servers = await client.get_servers(game="rust", country="US")

# Get specific server  
server = await client.get_server("server_id")

# Search servers
servers = await client.get_servers(search="Official", game="ark")
```

### Players
```python
# List players (requires authentication)
players = await client.get_players(page_size=20)

# Get specific player
player = await client.get_player("player_id")
```

### Bans
```python
# List bans (requires authentication)
bans = await client.get_bans(expired=False)

# Get specific ban
ban = await client.get_ban("ban_id")
```

### Organizations
```python
# List organizations (requires authentication)
orgs = await client.get_organizations()

# Get specific organization
org = await client.get_organization("org_id")
```

### Games
```python
# List all games
games = await client.get_games()

# Get specific game
game = await client.get_game("rust")
```

## Error Handling

```python
from battlemetrics.exceptions import BattleMetricsAPIError, BattleMetricsRateLimitError

try:
    servers = await client.get_servers(game="rust")
except BattleMetricsRateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after} seconds")
except BattleMetricsAPIError as e:
    print(f"API Error: {e.message} (Status: {e.status_code})")
```

## Development

```bash
# Install dependencies
poetry install

# Run linting
poetry run ruff check
poetry run black --check .

# Type checking  
poetry run pyright
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- [BattleMetrics API Documentation](https://www.battlemetrics.com/developers/documentation)
- [BattleMetrics Developer Portal](https://www.battlemetrics.com/developers)
- [JSON:API Specification](https://jsonapi.org/)
