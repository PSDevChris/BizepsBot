import random

from discord.ext import commands

from Main import (RequestTwitchToken, _get_banned_users, _is_banned, aiohttp,
                  datetime, json, logging, requests)


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
            # My ID is entered, change it to yours, 1000 Clips are returned at max
            async with session.get(f'https://api.twitch.tv/helix/clips?broadcaster_id=41503263') as r:
                if r.status == 200:
                    js = await r.json()
                    Clip = random.SystemRandom().choice(js['data'])
                    await ctx.defer()
                    await ctx.followup.send(f"Dieser Clip wurde bereitgestellt durch {Clip['creator_name']}!\n{Clip['url']}")
        logging.info(
            f"{ctx.author} requested a Twitch Clip, chosen was [{Clip['url']}]")

    @commands.slash_command(name="esagame", description="Gibt das aktuelle ESA Game aus", brief="Gibt das aktuelle ESA Game aus")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _esagame(self, ctx):
        try:
            USER = "esamarathon"
            r = requests.get(f'https://api.twitch.tv/helix/search/channels?query={USER}',
                             headers={'Authorization': f'Bearer {TWITCH_TOKEN}', 'Client-Id': f'{TWITCH_CLIENT_ID}'})
            data = json.loads(r.content)['data']
            data = list(
                filter(lambda x: x["broadcaster_login"] == f"{USER}", data))[0]

            if data['game_id'] is not None:
                gamerequest = requests.get(f'https://api.twitch.tv/helix/games?id={data["game_id"]}',
                                           headers={'Authorization': f'Bearer {TWITCH_TOKEN}', 'Client-Id': f'{TWITCH_CLIENT_ID}'})
                game = json.loads(gamerequest.content)['data'][0]
            else:
                game = {"name": "Irgendwas"}
            await ctx.defer()
            await ctx.followup.send(f"Bei ESA wird gerade {game['name']} gespielt!")
            logging.info(f"{ctx.author} invoked the ESA command.")
        except IndexError:
            # Username does not exist or Username is wrong, greetings to Schnabeltier
            logging.error("ESA Channel not found. Was it deleted or banned?!")
        except json.decoder.JSONDecodeError:
            logging.error("Twitch API not available.")
            await ctx.respond(f"Die Twitch API antwortet nicht.", ephemeral=True)
        except KeyError:
            logging.error("Twitch API not available.")
            await ctx.respond(f"Die Twitch API antwortet nicht.", ephemeral=True)


def setup(bot):
    bot.add_cog(Twitch(bot))
