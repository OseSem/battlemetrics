from battlemetrics.components.helpers import Helpers

class Bans:
    def __init__(self, helpers: Helpers, base_url: str) -> None:
        self.helpers = helpers
        self.base_url = base_url

    async def delete(self, banid: str) -> dict:
        """Deletes a ban.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-ban-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}
        Args:
            banid (str): The ID of the ban.
        Returns:
            dict: The response from the server.
        """

        url = f"{self.base_url}/bans/{banid}"
        
        return await self.helpers._make_request(method="DELETE", url=url)

    async def info(self, banid: str) -> dict:
        """The ban profile of a specific banid.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-ban-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}
        Args:
            banid (str): The banid.
        Returns:
            dict: The ban information
        """

        url = f"{self.base_url}/bans/{banid}"
        data = {
            "include": "server,user,playerIdentifiers,organization,banExemption"
        }
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def update(self, banid: str, reason: str = None, note: str = None, append: bool = False) -> dict:
        """Updates a targeted ban
        Documentation: https://www.battlemetrics.com/developers/documentation#link-PATCH-ban-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}
        Args:
            banid (str): The target ban
            reason (str, optional): Updated reason (not required)
            note (str, optional): Updated note (not required)
            append (bool, optional): Whether you want to append the new note to the old note.
        Returns:
            dict: The response from the server.
        """

        url = f"{self.base_url}/bans/{banid}"
        ban = await self.info(banid=banid)
        if reason:
            ban['data']['attributes']['reason'] = reason
        if note:
            if append:
                ban['data']['attributes']['note'] += f"\n{note}"
            else:
                ban['data']['attributes']['note'] = note
        return await self.helpers._make_request(method="PATCH", url=url, json=ban)

    async def search(self, search: str = None, player_id: int = None, banlist: str = None, 
                     expired: bool = True, exempt: bool = False, server: int = None, organization_id: int = None, userIDs: str = None):
        """List, search and filter existing bans.

        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-ban-/bans

        Args:
            search (str, optional): A search string, such as a steam ID. Defaults to None.
            player_id (int, optional): Battlemetrics ID of a specific user. Defaults to None.
            banlist (str, optional): Specific banlist to search. Defaults to None.
            expired (bool, optional): True/False - Do you want expired bans?. Defaults to True.
            exempt (bool, optional): True/False - Do you want to include exempt?. Defaults to False.
            server (int, optional): Server ID. Defaults to None.
            organization_id (int, optional): Organization ID. Defaults to None.
            userIDs (str, optional): User ID is the ID of the person who made the ban. Defaults to None.

        Returns:
            dict: A dictionary response of all the bans for the given parameters.
        """

        data = {
            "include": "server,user,player,organization",
            "filter[expired]": str(expired).lower(),
            "filter[exempt]": str(exempt).lower(),
            "sort": "-timestamp",
            "page[size]": "100"
        }

        if organization_id:
            data['filter[organization]'] = organization_id
        if player_id:
            data['filter[player]'] = player_id
        if server:
            data['filter[server]'] = server
        if search:
            data['filter[search]'] = search
        if banlist:
            data['filter[banList]'] = banlist
        if userIDs:
            data['filter[users]'] = userIDs
        url = f"{self.base_url}/bans"

        return await self.helpers._make_request(method="GET", url=url, params=data)
    
    
    async def native_ban_info(self, server: int = None, ban: str = None) -> dict:
        """Returns all the native bans
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banNative-/bans-native
        Args:
            server (int, optional): Target server. Defaults to None.
            ban (int, optional): Target ban. Defaults to None.
        Returns:
            dict: All native bans.
        """

        data = {
            "page[size]": "100",
            "include": "server,ban",
            "sort": "-createdAt",
            "fields[ban]": "reason",
            "fields[server]": "name",
            "fields[banNative]": "createdAt,reason"
        }
        if ban:
            data["filter[ban]"] = ban
        if server:
            data["filter[server]"] = server
        url = f"{self.base_url}/bans-native"
        return await self.helpers._make_request(method="GET", url=url, params=data)
    
    async def native_force_update(self, native_id: str) -> dict:
        """Forces an update on a native ban
        Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-banNative-/bans-native/{(%23%2Fdefinitions%2FbanNative%2Fdefinitions%2Fidentity)}/force-update
        Args:
            native_id (str): Targeted native ban
        Returns:
            dict: Response from the server.
        """
        
        url = f"{self.base_url}/bans-native/{native_id}/force-update"
        return await self.helpers._make_request(method="POST", url=url)