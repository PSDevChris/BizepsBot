import random

from discord.ext import commands

from Main import RequestTwitchToken, _is_banned, aiohttp, datetime, discord, json, logging


class Twitch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.TwitchClips = {}
        self.bot.loop.create_task(self._get_twitch_clips())
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

    async def cog_check(self, ctx):
        return await _is_banned(ctx)

    async def _get_twitch_clips(self):
        # My ID is entered, change it to yours, 20 Clips are returned at max, so we have to go through pages
        async with (
            aiohttp.ClientSession(headers={"Authorization": f"Bearer {TWITCH_TOKEN}", "Client-Id": f"{TWITCH_CLIENT_ID}"}) as session,
            session.get("https://api.twitch.tv/helix/clips?broadcaster_id=41503263&first=100") as r,
        ):
            Clips = {"data": [{"creatorname": "Doto", "url": "Gab keine Clips :("}], "pagination": {"cursor": ""}}
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

            self.TwitchClips = Clips

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    # Commands
    @commands.slash_command(name="doto_clip", description="Zeigt einen zufälligen Twitch Clip", brief="Zeigt einen zufälligen Twitch Clip")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _show_twitch_clip(self, ctx):
        if self.TwitchClips["data"] == []:
            await self._get_twitch_clips()
            logging.info("Twitch Clips were empty, refreshed the clips.")
        else:
            Clip = random.SystemRandom().choice(self.TwitchClips["data"])
            await ctx.defer()
            await ctx.followup.send(f"Dieser Clip wurde bereitgestellt durch {Clip['creator_name']}!\n{Clip['url']}")
            logging.info(f"{ctx.author} requested a Twitch Clip, chosen was [{Clip['url']}]")
            self.TwitchClips["data"].remove(Clip)

    @_show_twitch_clip.error
    async def _twitchclip_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam the twitchclipcommand!")
        elif isinstance(error, discord.CheckFailure):
            await ctx.respond("Du bist gebannt und damit von der Verwendung des Bots ausgeschlossen.", ephemeral=True)
        else:
            logging.error(f"ERROR: {error}")


def setup(bot):
    bot.add_cog(Twitch(bot))
