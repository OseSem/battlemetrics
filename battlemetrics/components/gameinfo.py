from battlemetrics.components.helpers import Helpers


class GameInfo:
    def __init__(self, helpers: Helpers, base_url: str) -> None:
        self.helpers = helpers
        self.base_url = base_url

    async def features(self, game: str = None) -> dict:
        """Lists the game features for the specified game
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-gameFeature-/game-features
        Args:
            game (str, optional): _description_. Defaults to None.
        Returns:
            dict: Returns a dictionary of the game features.
        """

        data = {
            "page[size]": "100"
        }
        if game:
            data['filter[game]'] = game
        url = f"{self.base_url}/game-features"
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def feature_options(self, feature_id: str, sort: str = "players") -> dict:
        """Gets the game feature options.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-gameFeatureOption-/game-features/{(%23%2Fdefinitions%2FgameFeature%2Fdefinitions%2Fidentity)}/relationships/options
        Args:
            feature_id (str): The ID of the game Feature.
            sort (str, optional): Takes "count" and "players". Defaults to "players".
        Returns:
            dict: Game feature options
        """

        data = {
            "page[size]": "100",
            "sort": sort
        }
        url = f"{self.base_url}/game-features/{feature_id}/relationships/options"
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def list(self, game: str = None) -> dict:
        """Lists all the games Battlemetrics can view.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-game-/games
        Args:
            game (str, optional): Refine it to a specific game. Or leave as none.
        Returns:
            dict: Games information!
        """

        data = {
            "page[size]": "100"
        }
        if game:
            data['fields[game]'] = game
        url = f"{self.base_url}/games"
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def info(self, game_id: str, game: str = None) -> dict:
        """Gets information on a specific game.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-game-/games/{(%23%2Fdefinitions%2Fgame%2Fdefinitions%2Fidentity)}
        Args:
            game_id (str): The ID of a specific game.
            game (str, optional): Limit it to a specific game, or leave as none.
        Returns:
            dict: Game information.
        """

        data = {
            "page[size]": "100"
        }
        if game:
            data['fields[game]'] = game
        url = f"{self.base_url}/games/{game_id}"
        return await self.helpers._make_request(method="GET", url=url, params=data)
