from discord.ext import commands
from Main import _is_banned
from Main import _get_banned_users
from Main import logging
from Main import random
from Main import aiohttp
from Main import RequestTwitchToken
from Main import json
from Main import datetime


class Twitch(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.BannedUsers = _get_banned_users()
        global TWITCH_TOKEN, TWITCH_TOKEN_EXPIRES, TWITCH_CLIENT_ID
        with open("TOKEN.json", "r") as TOKENFILE:
            TOKENDATA = json.load(TOKENFILE)
            TWITCH_CLIENT_ID = TOKENDATA['TWITCH_CLIENT_ID']
            if 'TWITCH_TOKEN' in TOKENDATA.keys() and 'TWITCH_TOKEN_EXPIRES' in TOKENDATA.keys() and datetime.datetime.timestamp(datetime.datetime.now()) < TOKENDATA['TWITCH_TOKEN_EXPIRES']:
                TWITCH_TOKEN = TOKENDATA['TWITCH_TOKEN']
                TWITCH_TOKEN_EXPIRES = TOKENDATA['TWITCH_TOKEN_EXPIRES']
            else:
                RequestTwitchToken()
        logging.info("Token successfully loaded for Twitch Class.")

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
        async with aiohttp.ClientSession(headers={'Authorization': f'Bearer {TWITCH_TOKEN}', 'Client-Id': f'{TWITCH_CLIENT_ID}'}) as session:
            # My ID is entered, change it to yours
            async with session.get(f'https://api.twitch.tv/helix/clips?broadcaster_id=41503263&first=50') as r:
                if r.status == 200:
                    js = await r.json()
                    Clip = random.SystemRandom().choice(js['data'])
                    await ctx.respond(f"Dieser Clip wurde bereitgestellt durch {Clip['creator_name']}!\n{Clip['url']}")
        logging.info(
            f"{ctx.author} requested a Twitch Clip, chosen was [{Clip['url']}]")


def setup(bot):
    bot.add_cog(Twitch(bot))
