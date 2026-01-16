from battlemetrics.components.helpers import Helpers

class BanList:
    def __init__(self, helpers: Helpers, base_url: str) -> None:
        self.helpers = helpers
        self.base_url = base_url

    async def rust_banlist_export(self, organization_id:int, server_id:int = None) -> list[dict]:
        """Exports your rust banlist.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-ban-/bans/export
        
        Args:
            organization_id (int): Organization ID the banlist belongs to
            server_id (int): Server ID the banlist is associated with.

        Returns:
            list[dict]: A list of dictionaries that provide the ban data.
        """
        
        url = f"{self.base_url}/bans/export"
        data = {
            "filter[organization]": organization_id,
            "format": "rust/bans.cfg"
        }
        if server_id:
            data["filter[server]"] = server_id
            
        return await self.helpers._make_request(method="GET", url=url, params=data)
    
    async def create_invite(self, organization_id: int, banlist_id: str, permManage: bool, 
                            permCreate: bool, permUpdate: bool, permDelete: bool, uses: int = 1, limit: int = 1) -> dict:
        """Creates an invite to 
        Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-banListInvite-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}/relationships/invites
        Args:
            organization_id (int): The target organization to be invited.
            banlist_id (str): The ID of the banlist you want to create the invite for
            permManage (bool): Are they allowed to manage it?
            permCreate (bool): Can they create stuff related to this banlist?
            permUpdate (bool): Can they update the banlist?
            permDelete (bool): Can they delete stuff related to this banlist?
            uses (int, optional): Number of times this banlist invite has been used.. Defaults to 1.
            limit (int, optional): How many times it's allowed to be used. Defaults to 1.
        Returns:
            dict: Returns whether it was successful or not.
        """

        url = f"{self.base_url}/ban-lists/{banlist_id}/relationships/invites"
        data = {
            "data": {
                "type": "banListInvite",
                "attributes": {
                    "uses": uses,
                    "limit": limit,
                    "permManage": str(permManage).lower(),
                    "permCreate": str(permCreate).lower(),
                    "permUpdate": str(permUpdate).lower(),
                    "permDelete": str(permDelete).lower()
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}"
                        }
                    }
                }
            }
        }
        return await self.helpers._make_request(method="POST", url=url, json_dict=data)

    async def read_invitation(self, invite_id: str) -> dict:
        """Allows you to see the information about a specific banlist invite, such as uses.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banListInvite-/ban-list-invites/{(%23%2Fdefinitions%2FbanListInvite%2Fdefinitions%2Fidentity)}
        Args:
            invite_id (str): The banlist invite id.
        Returns:
            dict: The banlist invite information
        """

        url = f"{self.base_url}/ban-list-invites/{invite_id}"
        data = {
            "include": "banList",
            "fields[organization]": "tz,banTemplate",
            "fields[user]": "nickname",
            "fields[banList]": "name, action",
            "fields[banListInvite]": "uses"
        }
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def invite_list(self, banlist_id: str) -> dict:
        """Returns all the invites for a specific banlist ID
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banListInvite-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}/relationships/invites
        Args:
            banlist_id (str): The ID of a banlist
        """

        url = f"{self.base_url}/ban-lists/{banlist_id}/relationships/invites"
        data = {
            "include": "banList",
            "fields[organization]": "tz,banTemplate",
            "fields[user]": "nickname",
            "fields[banList]": "name,action",
            "fields[banListInvite]": "uses",
            "page[size]": "100"
        }
        return await self.helpers. _make_request(method="GET", url=url, params=data)

    async def delete_invite(self, banlist_id: str, banlist_invite_id: str) -> dict:
        """Deletes an invite from a targeted banlist
        Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-banListInvite-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}/relationships/invites/{(%23%2Fdefinitions%2FbanListInvite%2Fdefinitions%2Fidentity)}
        Args:
            banlist_id (str): The target banlist
            banlist_invite_id (str): The target invite.
        Returns:
            dict: Whether it was successful or not.
        """

        url = f"{self.base_url}/ban-lists/{banlist_id}/relationships/invites/{banlist_invite_id}"
        return await self.helpers._make_request(method="DELETE", url=url)

    async def exemption_create(self, banid: str, organization_id: int, reason: str = None) -> dict:
        """Creates an exemption to the banlist.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-banExemption-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}/relationships/exemptions
        Args:
            banid (str): The banid you want to create an exemption for.
            organization_id (str): The organization associated to the exemption
            reason (str, optional): Reason for the exemption. Defaults to None.
        Returns:
            dict: Whether it was successful or not.
        """

        url = f"{self.base_url}/bans/{banid}/relationships/exemptions"
        data = {
            "data": {
                "type": "banExemption",
                "attributes": {
                        "reason": reason
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}"
                        }
                    }
                }
            }
        }
        return await self.helpers._make_request(method="POST", url=url, json_dict=data)

    async def exemption_delete(self, banid: str) -> dict:
        """Deletes an exemption
        Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-banExemption-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}/relationships/exemptions
        Args:
            banid (str): The ban that has an exemption
        Returns:
            dict: Whether it was successful or not
        """

        url = f"{self.base_url}/bans/{banid}/relationships/exemptions"
        return await self.helpers._make_request(method="DELETE", url=url)

    async def exemption_info_single(self, banid: str, exemptionid: str) -> dict:
        """Pulls information from a ban regarding a specific exemption
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banExemption-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}/relationships/exemptions/{(%23%2Fdefinitions%2FbanExemption%2Fdefinitions%2Fidentity)}
        Args:
            banid (str): Target ban
            exemptionid (str): Target exemption
        Returns:
            dict: Information about the exemption
        """

        url = f"{self.base_url}/bans/{banid}/relationships/exemptions/{exemptionid}"
        return await self.helpers._make_request(method="GET", url=url)

    async def exemption_info_all(self, banid: str) -> dict:
        """Pulls all exemptions related to the targeted ban
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banExemption-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}/relationships/exemptions
        Args:
            banid (str): Target ban
        Returns:
            dict: All ban exemptions
        """

        url = f"{self.base_url}/bans/{banid}/relationships/exemptions"
        data = {
            "fields[banExemption]": "reason"
        }
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def exemption_update(self, banid: str, exemptionid: str, reason: str) -> dict:
        """Updates a ban exemption
        Documentation: https://www.battlemetrics.com/developers/documentation#link-PATCH-banExemption-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}/relationships/exemptions
        Args:
            banid (str): The target ban
            exemptionid (str): The target exemption
            reason (str): New reason
        Returns:
            dict: Whether you were successful or not.
        """

        banexemption = await self.exemption_info_single(banid=banid, exemptionid=exemptionid)
        banexemption['data']['attributes']['reason'] = reason
        url = f"{self.base_url}/bans/{banid}/relationships/exemptions"
        return await self.helpers._make_request(method="PATCH", url=url, json=banexemption)

    async def create(self, organization_id: int, action: str, autoadd: bool, 
                     ban_identifiers: list, native_ban: bool, list_default_reasons: list, ban_list_name: str) -> dict:
        """Creates a new banlist for your targeted organization.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-banList-/ban-lists
        Args:
            organization_id (str): The organization ID.
            action (str): "none", "log", "kick"
            autoadd (bool): true or false
            ban_identifiers (list): ["steamID", "ip"]
            native_ban (bool): Should this be a native ban as well?
            list_default_reasons (list): Default reason for the ban if no new reason is specified
            ban_list_name (str): Name of the banlist
        Returns:
            dict: Returns a dictionary response of the new banlist created.
        """

        url = f"{self.base_url}/ban-lists"
        data = {
            "data": {
                "type": "banList",
                "attributes": {
                    "name": f"{ban_list_name}",
                    "action": f"{action}",
                    "defaultIdentifiers": ban_identifiers,
                    "defaultReasons": list_default_reasons,
                    "defaultAutoAddEnabled": str(autoadd).lower(),
                    "defaultNativeEnabled": str(native_ban).lower(),
                    "nativeBanTTL": None,
                    "nativeBanTempMaxExpires": None,
                    "nativeBanPermMaxExpires": None
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}"
                        }
                    },
                    "owner": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}"
                        }
                    }
                }
            }
        }
        return await self.helpers._make_request(method="POST", url=url, json_dict=data)

    async def accept_invite(self, code: str, action: str, autoadd: bool, ban_identifiers: list, native_ban: bool, 
                            list_default_reasons: list, organization_id: str, organization_owner_id: str) -> dict:
        """Accepts an invitation to subscribe to a banlist.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-POST-banList-/ban-lists/accept-invite
        Args:
            code (str): Invitation code.
            action (str): "none", "log" or "kick"
            autoadd (bool): True or False
            ban_identifiers (list): ["steamID", "ip"]
            native_ban (bool): True or False
            list_default_reasons (list): ["Banned for hacking"]
            organization_id (str): ID of your organization?
            organization_owner_id (str): ID of the owner of the organization
        Returns:
            dict: Response from server.
        """

        url = f"{self.base_url}/ban-lists/accept-invite"
        data = {
            "data": {
                "type": "banList",
                "attributes": {
                    "code": code,
                    "action": action,
                    "defaultIdentifiers": ban_identifiers,
                    "defaultReasons": list_default_reasons,
                    "defaultAutoAddEnabled": str(autoadd).lower(),
                    "defaultNativeEnabled": str(native_ban).lower(),
                    "nativeBanTTL": None,
                    "nativeBanTempMaxExpires": None,
                    "nativeBanPermMaxExpires": None
                },
                "relationships": {
                    "organization": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_id}"
                        }
                    },
                    "owner": {
                        "data": {
                            "type": "organization",
                            "id": f"{organization_owner_id}"
                        }
                    }
                }
            }
        }
        return await self.helpers._make_request(method="POST", url=url, json_dict=data)

    async def unsubscribe(self, banlist_id: str, organization_id: str) -> dict:
        """Unscubscribes from a banlist
        Documentation: https://www.battlemetrics.com/developers/documentation#link-DELETE-banList-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}/relationships/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}
        Args:
            banlist_id (str): ID of the banlist
            organization_id (str): Your organization ID
        Returns:
            dict: Response from server.
        """

        url = f"{self.base_url}/ban-lists/{banlist_id}/relationships/organizations/{organization_id}"
        return await self.helpers._make_request(method="DELETE", url=url)

    async def list(self) -> dict:
        """Lists all your banlists for you.
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banList-/ban-lists
        Returns:
            dict: A dictionary response of all the banlists you have access to.
        """

        url = f"{self.base_url}/ban-lists"
        data = {
            "include": "server,organization,owner",
            "page[size]": "100"
        }
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def subscribed_orgs(self, banlist_id: str) -> dict:
        """Lists all the organizations that are subscribed to the targeted banlist. You require manage perms to use this list (or be the owner)
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banList-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}/relationships/organizations
        Args:
            banlist_id (str): The Banlist ID
        Returns:
            dict: A dictionary response of all the organizations subbed to the targeted banlist.
        """

        url = f"{self.base_url}/ban-lists/{banlist_id}/relationships/organizations"
        data = {
            "include": "server,organization,owner",
            "page[size]": "100"
        }
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def subscribers(self, banlist_id: str, organization_id: str) -> dict:
        """Gets the subscriber information for a specific banlist.

        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banList-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}/relationships/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}
        Args:
            banlist_id (str): The ID of the targeted banlist.
            organization_id (_type_): The ID of the targeted organization subscribed to the targeted banlist.
        Returns:
            dict: A dictionary response of all the information requested.
        """

        url = f"{self.base_url}/ban-lists/{banlist_id}/relationships/{organization_id}"
        data = {
            "include": "organization, owner, server"
        }
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def read(self, banlist_id: str) -> dict:
        """Retrieves the name of a banlist by the banlist id
        Documentation: https://www.battlemetrics.com/developers/documentation#link-GET-banList-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}
        Args:
            banlist_id (str): The ID of the banlist.
        Returns:
            dict: Returns a dictionary response of the requested data.
        """

        url = f"{self.base_url}/ban-lists/{banlist_id}"
        data = {
            "include": "owner"
        }
        return await self.helpers._make_request(method="GET", url=url, params=data)

    async def update(self, banlist_id: str, organization_id: str, action: str = None, 
                     autoadd: bool = None, ban_identifiers: list = None, native_ban: bool = None, 
                     list_default_reasons: list = None, ban_list_name: str = None) -> dict:
        """Updates the targeted banlist with the altered information you supply
        Documentation: https://www.battlemetrics.com/developers/documentation#link-PATCH-banList-/ban-lists/{(%23%2Fdefinitions%2FbanList%2Fdefinitions%2Fidentity)}/relationships/organizations/{(%23%2Fdefinitions%2Forganization%2Fdefinitions%2Fidentity)}
        Args:
            banlist_id (str): Banlist ID.
            organization_id (str): Organization ID
            Optional paramaters default to the banlist settings.
            action (str, optional): "none", "log" or "kick"
            autoadd (bool, optional): True or False
            ban_identifiers (list, optional): ["steamID", "ip"]
            native_ban (bool, optional): True or False
            list_default_reasons (list, optional): [List of default reasons]
            ban_list_name (str, optional): Name of the banlist
        Returns:
            dict: Dictionary response of the new banlist.
        """

        banlist = await self.get_list(banlist_id=banlist_id)
        if not banlist:
            return None
        if action:
            banlist['attributes']['action'] = action
        if autoadd:
            banlist['attributes']['defaultAutoAddEnabled'] = str(
                autoadd).lower()
        if ban_identifiers:
            banlist['attributes']['defaultIdentifiers'] = ban_identifiers
        if native_ban:
            banlist['attributes']['defaultNativeEnabled'] = str(
                native_ban).lower()
        if list_default_reasons:
            banlist['attributes']['defaultReasons'] = list_default_reasons
        if ban_list_name:
            banlist['attributes']['name'] = ban_list_name
        url = f"{self.base_url}/ban-lists/{banlist_id}/relationships/organizations/{organization_id}"
        return await self.helpers._make_request(method="PATCH", url=url, json=banlist)

    async def get_list(self, banlist_id: str = None) -> dict:
        """Returns the banlist information of the targeted banlist
        Documentation: None. Custom code.
        Args:
            banlist_id (str): The ID of the banlist you want.
        Returns:
            dict: The dictionary response of the targeted banlist.
        """

        url = f"https://api.battlemetrics.com/ban-lists"
        data = {
            "page[size]": "100",
            "include": "organization,owner,server"
        }
        banlists = await self.helpers._make_request(method="GET", url=url, params=data)
        for banlist in banlists:
            if banlist['id'] == banlist_id:
                return banlist
        return banlists
