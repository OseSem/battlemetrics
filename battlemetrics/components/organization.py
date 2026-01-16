import datetime
import uuid

from datetime import datetime, timedelta
from battlemetrics.components.helpers import Helpers

class Organization:
    def __init__(self, helpers: Helpers, base_url: str) -> None:
        self.helpers = helpers
        self.base_url = base_url


    async def info(self, organization_id: int) -> dict:
        """Returns an organizations profile.
        Documentation: Not documented in the API.
        Args:
            organization_id (int): An organizations battlemetrics ID.
        Returns:
            dict: The information about your organization or a targeted organization
        """

        url = f"{self.base_url}/organizations/{organization_id}"
        data = {
            "include": "organizationUser,banList,role,organizationStats"
        }
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def stats(self, organization_id: int, start: str, end: str, game: str = None) -> dict:
        """Gets the player stats for the organization
        Documentation: https://www.battlemetrics.com/developers/documentation#resource-organizationStats
        Args:
            organization_id (int): Organization ID
            start (str): UTC start time. Defaults to 7 days ago.
            end (str): UTC end time. Defaults to today.
            game (str, optional): Targeted game, example: rust. Defaults to None.
        Returns:
            dict: Player stats for the organization.
        """

        if not start:
            now = datetime.utcnow()
            start = now - timedelta(days=1)
            start = start.strftime('%Y-%m-%dT%H:%M:%SZ')
        if not end:
            end = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        url = f"{self.base_url}/organizations/{organization_id}/stats/players"
        data = {
            "filter[range]": f"{start}:{end}"
        }
        if game:
            data["filter[game]"] = game
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def friends_list(self, organization_id: str, filter_accepted: bool = True, filter_origin: bool = True, filter_name: str = None, filter_reciprocated: bool = True) -> dict:
        """Gets all the organization friends.
        Documentation: https://www.battlemetrics.com/developers/documentation#resource-organizationFriend
        Args:
            organization_id (str): Your organization ID
            filter_accepted (bool, optional): True or False. Have they accepted our friendship?. Defaults to True.
            filter_origin (bool, optional): True or False. Defaults to True.
            filter_name (str, optional): Name of a specific organization. Defaults to None.
            filter_reciprocated (bool, optional): True or False. Are the feelings mutual?. Defaults to True.
        Returns:
            dict: Returns all the friendship information based on the paramaters set.
        """

        url = f"{self.base_url}/organizations/{organization_id}/relationships/friends"
        data = {
            "include": "organization",
            "filter[accepted]": str(filter_accepted).lower(),
            "filter[origin]": str(filter_origin).lower(),
            "filter[reciprocated]": str(filter_reciprocated).lower()
        }
        if filter_name:
            data['filter[name]'] = filter_name
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def friend(self, organization_id: int, friend_organization_id: int) -> dict:
        """Gets the friend information for your organization.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-organizationFriend-/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}/relationships/friends/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}
        Args:
            organization_id (int): Your organization ID
            friend_organization_id (int): Friend organization ID
        Returns:
            dict: Dictionary response about the organization friendship
        """

        url = f"{self.base_url}/organizations/{organization_id}/relationships/friends/{friend_organization_id}"
        data = {
            "include": "organization,playerFlag,organizationStats"
        }
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def friend_update(self, organization_id: int, friend_organization_id: int, identifiers: list, playerflag: str, shared_notes: bool = True, accepted: bool = True) -> dict:
        """Updates your organizations friendship.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-PATCH-organizationFriend-/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}/relationships/friends/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}
        Args:
            organization_id (int): Your organization ID
            friend_organization_id (int): The friendly organizations ID.
            identifiers (list): [ip, steamID], identifiers to be shared.
            shared_notes (bool, optional): Sharing Notes?
            accepted (bool, optional):Accepted friendship?
        Returns:
            dict: Returns a dictionary response on the new updated friendship.
        """

        url = f"https://api.battlemetrics.com/organizations/{organization_id}/relationships/friends/{friend_organization_id}"
        data = {
            "data": {
                "id": friend_organization_id,
                "type": "organizationFriend",
                "attributes": {
                    "accepted": str(accepted).lower(),
                    "identifiers": identifiers,
                    "notes": str(shared_notes).lower()
                }
            }
        }
        return await self.helpers._make_request(method="PATCH", url=url, json_dict=data)

    async def friend_create(self, organization_id: int, friendly_org: int, identifiers: list, shared_notes: bool = True) -> dict:
        """Creates a new friend invite to the targeted organization ID
        Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-organizationFriend-/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}/relationships/friends
        Args:
            organization_id (int): Your organization ID
            friendly_org (int): Targeted organization ID
            identifiers (list): ["steamID", "ip"]
            shared_notes (bool, optional): Sharing notes? Defaults to True.
        Returns:
            dict: Returns the dictionary response from the server
        """

        url = f"https://api.battlemetrics.com/organizations/{organization_id}/relationships/friends"
        data = {
            "data": {
                "type": "organizationFriend",
                "attributes": {
                    "identifiers": identifiers,
                    "notes": str(shared_notes).lower()
                },
                "relationships": {
                    "friend": {
                        "data": {
                            "type": "organization",
                            "id": f"{friendly_org}"
                        }
                    },
                    "flagsShared": {
                        "data": [
                            {
                                "type": "playerFlag",
                                "id": f"{uuid.uuid5}"
                            }
                        ]
                    }
                }
            }
        }
        return await self.helpers._make_request(method="POST", url=url, json_dict=data)

    async def friend_delete(self, organization_id: int, friends_id: int) -> dict:
        """Deletes a friendship
        Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-organizationFriend-/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}/relationships/friends/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}
        Args:
            organization_id (int): Your organization ID
            friends_id (int): Friends organization ID
        Returns:
            dict: Response from the server.
        """

        url = f"{self.base_url}/organizations/{organization_id}/relationships/friends/{friends_id}"
        return await self.helpers._make_request(method="DELETE", url=url)

    async def player_stats(self, organization_id: int, start_date: str = None, end_date: str = None, game:str = None) -> dict:
        """Returns the statistics of all the players who have joined your server and where they're from.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-organization-/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}/stats/players
        Args:
            organization_id (int): Your organization ID
            start_date (str, optional): Start date, max 90 days. Defaults to 90 days ago.
            end_date (str, optional): End date, defaults to now.
            game (str, optional): The game you wish to filter by. Defaults to None
        Returns:
            dict: Returns a dictionary of all the stats!
        """

        url = f"{self.base_url}/organizations/{organization_id}/stats/players"
        if not start_date:
            now = datetime.utcnow()
            start_date = now - timedelta(days=1)
            start_date = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        if not end_date:
            end_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        data = {
            
            "filter[range]": f"{start_date}:{end_date}"
        }
        
        if game:
            data["filter[game]"] = game
        
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def commands_activity(self, organization_id: int, summary: bool = False, users: str = None, commands: str = None, time_start: str = None, time_end: str = None, servers: int = None) -> dict:
        """Grabs all the command activity related to the targeted organization
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-commandStats-/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}/relationships/command-stats
        Args:
            organization_id (int): The Organization ID
            summary (bool, optional): A summary. Defaults to False.
            users (str, optional): Specific users?. Defaults to None.
            commands (str, optional): Specific Commands?. Defaults to None.
            time_start (str, optional): UTC start time. Defaults to 7 days ago.
            time_end (str, optional): UTC end time. Defaults to today.
            servers (int, optional): Targeted servers. Defaults to None.
        Returns:
            dict: Returns command usage data.
        """

        if not time_start:
            now = datetime.utcnow()
            time_start = now - timedelta(days=1)
            time_start = time_start.strftime('%Y-%m-%dT%H:%M:%SZ')
        if not time_end:
            time_end = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        data = {
            "filter[timestamp]": f"{time_start}:{time_end}"
        }
        if summary:
            data['filter[summary]'] = str(summary).lower()
        if users:
            data['filter[users]'] = users
        if commands:
            data['filter[commands]'] = commands
        if servers:
            data['filter[servers]'] = servers
        url = f"{self.base_url}/organizations/{organization_id}/relationships/command-stats"
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def user_organization_view(self) -> dict:
        """Retrieves the organizations the current API token can view.
        Documentation: This endpoint is not documented.

        Returns:
            dict: Returns a dictionary of all the organizations the user can view.
        """
        url = f"{self.base_url}/organizations"
        data = {
            "page[size]": "100",
            "include": "organizationUser,banList,organizationStats"
        }

        return await self.helpers._make_request(method="GET", url=url, params=data)


    async def auditlogs(self, organization_id:int):
        """_summary_

        Args:
            organization_id (int): _description_

        Returns:
            _type_: _description_
        """
        
        url = f"{self.base_url}/audit-log"
        data = {
            "filter[organizations]": organization_id,
            
            "page[size]": "100",
            "include": "flagPlayer,playerFlag,identifier,player,playerCounter,activityMessage,server,organization,organizationUser"
        }
        return await self.helpers._make_request(method="GET", url=url, params=data)