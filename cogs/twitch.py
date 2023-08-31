import asyncio
import random

from discord.ext import commands

from Main import (RequestTwitchToken, _get_banned_users, _is_banned, aiohttp,
                  datetime, discord, json, logging, requests)


async def _get_twitch_clips():
    async with aiohttp.ClientSession(headers={'Authorization': f'Bearer {TWITCH_TOKEN}', 'Client-Id': f'{TWITCH_CLIENT_ID}'}) as session:
        # My ID is entered, change it to yours, 20 Clips are returned at max, so we have to go through pages
        async with session.get(f'https://api.twitch.tv/helix/clips?broadcaster_id=41503263') as r:
            if r.status == 200:
                Clips = await r.json()
                KeysToRemove = []
                for key in Clips['data'][0]:  # Cleaning up the JSON to reduce memory
                    if key not in ['creator_name', 'url']:
                        KeysToRemove.append(key)
                for index in range(len(Clips['data'])):
                    for keyvalue in KeysToRemove:
                        Clips['data'][index].pop(keyvalue, None)
                if Clips['pagination']:
                    Pagination = Clips['pagination']['cursor']
                else:
                    Pagination = ""
                while Pagination != "":
                    async with session.get(f'https://api.twitch.tv/helix/clips?broadcaster_id=41503263&after={Pagination}') as r:
                        if r.status == 200:
                            NextPage = await r.json()
                            for index in range(len(NextPage['data'])):
                                for keyvalue in KeysToRemove:
                                    NextPage['data'][index].pop(keyvalue, None)
                            # Append new list to old one
                            Clips['data'] = Clips['data'] + NextPage['data']
                            if NextPage['pagination']:
                                Pagination = NextPage['pagination']['cursor']
                            else:
                                Pagination = ""
                logging.info(
                    f"Loaded the Twitch Clips, I found {len(Clips['data'])} Clips.")
            else:
                logging.error(
                    "ERROR: Twitch Clips could not be loaded!", exc_info=True)

    return Clips


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
        if self.TwitchClips['data'] == []:
            self.TwitchClips = await _get_twitch_clips()
            logging.info("Twitch Clips were empty, refreshed the clips.")
        else:
            Clip = random.SystemRandom().choice(self.TwitchClips['data'])
            await ctx.defer()
            await ctx.followup.send(f"Dieser Clip wurde bereitgestellt durch {Clip['creator_name']}!\n{Clip['url']}")
            logging.info(
                f"{ctx.author} requested a Twitch Clip, chosen was [{Clip['url']}]")
            self.TwitchClips['data'].remove(Clip)

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

    @_show_twitch_clip.error
    async def _twitchclip_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(
                f"{ctx.author} wanted to spam the twitchclipcommand!")
        elif isinstance(error, discord.CheckFailure):
            await ctx.respond(f"Du bist gebannt und damit von der Verwendung des Bots ausgeschlossen.", ephemeral=True)
        else:
            logging.error(f"ERROR: {error}")

    @_esagame.error
    async def _esagame_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam the esagamecommand!")
        elif isinstance(error, discord.CheckFailure):
            await ctx.respond(f"Du bist gebannt und damit von der Verwendung des Bots ausgeschlossen.", ephemeral=True)
        else:
            logging.error(f"ERROR: {error}")


def setup(bot):
    bot.add_cog(Twitch(bot))
