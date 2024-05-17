import asyncio
import random
import re

import zoneinfo
from discord import Option
from discord.ext import commands

from Main import RequestTwitchToken, _is_banned, aiohttp, datetime, discord, json, logging


async def _get_twitch_clips():
    async with aiohttp.ClientSession(headers={"Authorization": f"Bearer {TWITCH_TOKEN}", "Client-Id": f"{TWITCH_CLIENT_ID}"}) as session, session.get(
        "https://api.twitch.tv/helix/clips?broadcaster_id=41503263"
    ) as r:
        # My ID is entered, change it to yours, 20 Clips are returned at max, so we have to go through pages
        if r.status == 200:
            Clips = await r.json()
            KeysToRemove = []
            for key in Clips["data"][0]:  # Cleaning up the JSON to reduce memory
                if key not in ["creator_name", "url"]:
                    KeysToRemove.append(key)
            for index in range(len(Clips["data"])):
                for keyvalue in KeysToRemove:
                    Clips["data"][index].pop(keyvalue, None)
            Pagination = Clips["pagination"]["cursor"] if Clips["pagination"] else ""
            while Pagination != "":
                async with session.get(f"https://api.twitch.tv/helix/clips?broadcaster_id=41503263&after={Pagination}") as r:
                    if r.status == 200:
                        NextPage = await r.json()
                        for index in range(len(NextPage["data"])):
                            for keyvalue in KeysToRemove:
                                NextPage["data"][index].pop(keyvalue, None)
                        # Append new list to old one
                        Clips["data"] = Clips["data"] + NextPage["data"]
                        Pagination = NextPage["pagination"]["cursor"] if NextPage["pagination"] else ""
            logging.info(f"Loaded the Twitch Clips, I found {len(Clips['data'])} Clips.")
        else:
            logging.error("ERROR: Twitch Clips could not be loaded!", exc_info=True)

    return Clips


async def _get_esa_schedule(esa_url, option):
    current_time = datetime.datetime.now(tz=zoneinfo.ZoneInfo("Europe/Berlin")).replace(microsecond=0)
    async with aiohttp.ClientSession() as ESASchedule, ESASchedule.get(esa_url) as RequestToESASchedule:
        if RequestToESASchedule.status == 200:
            ESAScheduleJSON = await RequestToESASchedule.json()
            for index, Run in enumerate(ESAScheduleJSON["data"]):
                try:
                    if (
                        datetime.datetime.strptime(Run["scheduled"], "%Y-%m-%dT%H:%M:%S%z").astimezone(zoneinfo.ZoneInfo("Europe/Berlin")) < current_time
                        and datetime.datetime.strptime(ESAScheduleJSON["data"][index + 1]["scheduled"], "%Y-%m-%dT%H:%M:%S%z").astimezone(zoneinfo.ZoneInfo("Europe/Berlin")) > current_time
                    ):
                        FoundESARun = ESAScheduleJSON["data"][index + 1] if option == "spaeter" and index != -1 else ESAScheduleJSON["data"][index]
                        esa_runners = list(FoundESARun["players"])
                        esa_runners = ", ".join(esa_runners)
                        esa_runners = re.sub(r"\(http.+\)", "", esa_runners).replace("[", "").replace("]", "")
                        if option == "spaeter":
                            next_run = f"Danach läuft bei ESA {FoundESARun['game']} {FoundESARun['category']} mit {esa_runners}!"
                            ReturnString = next_run
                            break
                        current_run = f"Aktuell läuft bei ESA {FoundESARun['game']} {FoundESARun['category']} mit {esa_runners}!"
                        ReturnString = current_run
                        break
                    ReturnString = "ESA ist vorbei oder hat noch nicht begonnen. Besuche uns bald wieder!"
                except IndexError:  # ESA ended, dirty fix for now, need to have a look at length property
                    ReturnString = "ESA ist vorbei oder hat noch nicht begonnen. Besuche uns bald wieder!"
        else:
            ReturnString = "ESA ist vorbei oder hat noch nicht begonnen. Besuche uns bald wieder!"
    return ReturnString


class Twitch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global TWITCH_TOKEN, TWITCH_TOKEN_EXPIRES, TWITCH_CLIENT_ID
        with open("TOKEN.json", "r") as TOKENFILE:
            TOKENDATA = json.load(TOKENFILE)
            TWITCH_CLIENT_ID = TOKENDATA["TWITCH_CLIENT_ID"]
            if "TWITCH_TOKEN" in TOKENDATA and "TWITCH_TOKEN_EXPIRES" in TOKENDATA and datetime.datetime.timestamp(datetime.datetime.now()) < TOKENDATA["TWITCH_TOKEN_EXPIRES"]:
                TWITCH_TOKEN = TOKENDATA["TWITCH_TOKEN"]
                TWITCH_TOKEN_EXPIRES = TOKENDATA["TWITCH_TOKEN_EXPIRES"]
            else:
                RequestTwitchToken()
        logging.info("Token successfully loaded for Twitch Class.")
        self.TwitchClips = asyncio.run(_get_twitch_clips())

    async def cog_check(self, ctx):
        return await _is_banned(ctx)

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    # Commands
    @commands.slash_command(name="doto_clip", description="Zeigt einen zufälligen Twitch Clip", brief="Zeigt einen zufälligen Twitch Clip")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _show_twitch_clip(self, ctx):
        if self.TwitchClips["data"] == []:
            self.TwitchClips = await _get_twitch_clips()
            logging.info("Twitch Clips were empty, refreshed the clips.")
        else:
            Clip = random.SystemRandom().choice(self.TwitchClips["data"])
            await ctx.defer()
            await ctx.followup.send(f"Dieser Clip wurde bereitgestellt durch {Clip['creator_name']}!\n{Clip['url']}")
            logging.info(f"{ctx.author} requested a Twitch Clip, chosen was [{Clip['url']}]")
            self.TwitchClips["data"].remove(Clip)

    @commands.slash_command(name="esa", description="Gibt das aktuelle ESA Game aus", brief="Gibt das aktuelle ESA Game aus")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _esagame(self, ctx, option: Option(str, "Zeigt das nächste Spiel", choices=["spaeter"], required=False)):
        ESARun = await _get_esa_schedule("https://app.esamarathon.com/horaro-proxy/v2/esa/schedule/2024-winter1", option=option)
        await ctx.respond(ESARun)

    @commands.slash_command(name="esa2", description="Gibt das aktuelle ESA Game aus dem zweiten Stream aus", brief="Gibt das aktuelle ESA Game aus Stream 2 aus")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _esagame2(self, ctx, option: Option(str, "Zeigt das nächste Spiel", choices=["spaeter"], required=False)):
        ESARun2 = await _get_esa_schedule("https://app.esamarathon.com/horaro-proxy/v2/esa/schedule/2024-winter2", option=option)
        await ctx.respond(ESARun2)

    @_show_twitch_clip.error
    async def _twitchclip_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam the twitchclipcommand!")
        elif isinstance(error, discord.CheckFailure):
            await ctx.respond("Du bist gebannt und damit von der Verwendung des Bots ausgeschlossen.", ephemeral=True)
        else:
            logging.error(f"ERROR: {error}")

    @_esagame.error
    async def _esagame_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam the esagamecommand!")
        elif isinstance(error, discord.CheckFailure):
            await ctx.respond("Du bist gebannt und damit von der Verwendung des Bots ausgeschlossen.", ephemeral=True)
        else:
            logging.error(f"ERROR: {error}")

    @_esagame2.error
    async def _esagame2_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam the esagamecommand!")
        elif isinstance(error, discord.CheckFailure):
            await ctx.respond("Du bist gebannt und damit von der Verwendung des Bots ausgeschlossen.", ephemeral=True)
        else:
            logging.error(f"ERROR: {error}")


def setup(bot):
    bot.add_cog(Twitch(bot))
