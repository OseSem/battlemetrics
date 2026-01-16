from battlemetrics.components.helpers import Helpers

class Flags:
    def __init__(self, helpers: Helpers, base_url: str) -> None:
        self.base_url = base_url
        self.helpers = helpers

    async def create(self, color: str, description: str, icon_name: str, flag_name: str, organization_id: int, user_id: int) -> dict:
        """Create a new flag
        Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-playerFlag-/player-flags
        Args:
            color (str): The color of the flag. pattern: ^#[0-9a-fA-F]{6}$
            description (str): Flag Description
            icon_name (str): Icon name. Refer to documentation
            flag_name (str): Name of flag
            organization_id (int): The organization ID the flag belongs to
            user_id (int): The User ID the flag is created by.
        Returns:
            dict: Response from server.
        """

        url = f"{self.base_url}/player-flags"
        data = {
            "data": {
                "type": "playerFlag",
                "attributes": {
                    "icon": f"{icon_name}",
                    "name": f"{flag_name}",
                    "color": f"{color}",
                    "description": f"{description}"
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}"
                        }
                    },
                    "user": {
                        "data": {
                            "type": "user",
                            "id": f"{user_id}"
                        }
                    }
                }
            }
        }
        
        return await self.helpers._make_request(method="POST", url=url, json_dict=data)

    async def delete(self, flag_id: str) -> dict:
        """Delete an existing flag.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-playerFlag-/player-flags/{(%23%2Fdefinitions%2FplayerFlag%2Fdefinitions%2Fidentity)}
        Args:
            flag_id (str): The ID of the flag
        Returns:
            dict: Response from the server.
        """

        url = f"{self.base_url}/player-flags/{flag_id}"
        return await self.helpers._make_request(method="DELETE", url=url)

    async def info(self, flag_id: str) -> dict:
        """Info for existing flag.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-playerFlag-/player-flags/{(%23%2Fdefinitions%2FplayerFlag%2Fdefinitions%2Fidentity)}
        Args:
            flag_id (str): The ID of the flag
        Returns:
            dict: Dictionary response of the flag data.
        """

        url = f"{self.base_url}/player-flags/{flag_id}"
        return await self.helpers._make_request(method="GET", url=url)

    async def list(self, filter_personal: bool = False) -> dict:
        """List existing player flags.
        Documentation:https://www.battlemetrics.com/developers/documentation#link-GET-playerFlag-/player-flags
        Args:
            filter_personal (bool, optional): Hide/show personal flags. Defaults to False.
        Returns:
            dict: Dictionary response of a list of flags.
        """

        url = f"{self.base_url}/player-flags"
        data = {
            "page[size]": "100",
            "include": "organization"
        }
        if filter_personal:
            data["filter[personal]"] = str(filter_personal).lower()
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def update(self, flag_id: str, color: str, description: str, icon_name: str, flag_name: str) -> dict:
        """Create a new flag
        Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-playerFlag-/player-flags
        Args:
            color (str): The color of the flag. pattern: ^#[0-9a-fA-F]{6}$
            description (str): Flag Description
            icon_name (str): Icon name. Refer to documentation
            flag_name (str): Name of flag
        Returns:
            dict: Response from server.
        """

        url = f"{self.base_url}/player-flags/{flag_id}"
        data = {
            "data": {
                "type": "playerFlag",
                "id": f"{flag_id}",
                "attributes": {
                    "icon": f"{icon_name}",
                    "name": f"{flag_name}",
                    "color": f"{color}",
                    "description": f"{description}"
                }
            }
        }
        return await self.helpers._make_request(method="PATCH", url=url, json_dict=data)
