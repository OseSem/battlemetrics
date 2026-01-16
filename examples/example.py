from battlemetrics import Battlemetrics
import asyncio

api = Battlemetrics("your token here")

player_info = asyncio.run(api.player.info(12345))


banplayer = asyncio.run(api.player.add_ban(
    reason="Example Ban Reason",
    note="Example Ban Note",
    org_id="!234",
    banlist="0506f1a0-0345-11eb-b314-AAAAAAAAA",
    battlemetrics_id=1234,
    steam_id=1234
))