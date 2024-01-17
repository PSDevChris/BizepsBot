from datetime import datetime

import aiohttp
import zoneinfo
from discord import Option
from discord.ext import commands

from Main import _get_banned_users, _is_banned, logging


class GDQ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.BannedUsers = _get_banned_users()

    async def cog_check(self, ctx):
        return await _is_banned(ctx)

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    # Commands
    @commands.slash_command(name="gdq", description="Zeigt das aktuelle GDQ Game, inkl. Kategorie und Runner!", brief="Zeigt das aktuelle GDQ Game, inkl. Kategorie und Runner!")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _gdqgame(self, ctx, option: Option(str, "Zeigt das nächste Spiel", choices=["spaeter"], required=False)):
        GDQURL = "https://gamesdonequick.com/tracker/api/v2/events/46/runs/"
        CURRENTTIME = datetime.now(tz=zoneinfo.ZoneInfo("Europe/Berlin")).replace(microsecond=0)
        try:
            async with aiohttp.ClientSession() as GDQSession, GDQSession.get(GDQURL) as RequestToGDQSchedule:
                if RequestToGDQSchedule.status == 200:
                    await ctx.defer()
                    GDQScheduleJSON = await RequestToGDQSchedule.json()
                    for index, Run in enumerate(GDQScheduleJSON["results"]):
                        if (
                            datetime.strptime(Run["starttime"], "%Y-%m-%dT%H:%M:%S%z").astimezone(zoneinfo.ZoneInfo("Europe/Berlin")) < CURRENTTIME
                            and datetime.strptime(Run["endtime"], "%Y-%m-%dT%H:%M:%S%z").astimezone(zoneinfo.ZoneInfo("Europe/Berlin")) > CURRENTTIME
                            and Run["type"] == "speedrun"
                        ):
                            FoundRun = GDQScheduleJSON["results"][index + 1] if option == "spaeter" and index != -1 else GDQScheduleJSON["results"][index]
                            Speedrunners = [runner["name"] for runner in FoundRun["runners"]]
                            if option == "spaeter":
                                await ctx.followup.send(f"Bei GDQ läuft danach **{FoundRun['display_name']}** mit der Kategorie *{FoundRun['category']}* von {', '.join(Speedrunners)}.")
                                logging.info(f"{ctx.author} wanted to know the next game that is run at GDQ.")
                                break
                            await ctx.followup.send(f"Aktuell läuft bei GDQ **{FoundRun['display_name']}** mit der Kategorie *{FoundRun['category']}* von {', '.join(Speedrunners)}.")
                            logging.info(f"{ctx.author} wanted to know the current game that is run at GDQ.")
                            break
                    else:
                        await ctx.followup.send("GDQ ist vorbei oder noch nicht angefangen, beehre uns bald wieder.")
                        logging.info(f"{ctx.author} wanted to know the current game that is run at GDQ, but GDQ has not started or is done.")
                else:
                    await ctx.followup.send("GDQ ist vorbei oder noch nicht angefangen, beehre uns bald wieder.")
                    logging.error(f"{ctx.author} wanted to know the current game that is run at GDQ, the website is not responding.")
        except ValueError:
            await ctx.followup.send("GDQ ist vorbei oder noch nicht angefangen, beehre uns bald wieder.")
            logging.warning(f"{ctx.author} wanted to know the current game that is run at GDQ, but there is no schedule live.")
        except:
            logging.error("ERROR: ", exc_info=True)

    @_gdqgame.error
    async def _gdqgame_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.", ephemeral=True)
            logging.warning(f"{ctx.author} wanted to spam the GDQ command!")


def setup(bot):
    bot.add_cog(GDQ(bot))
