from datetime import datetime, timedelta

import pandas as pd
import requests
from dateutil.parser import parse
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
        GDQ_URL = "https://gamesdonequick.com/schedule"
        GDQ_REQ = requests.get(GDQ_URL)
        if GDQ_REQ.status_code == 200:
            try:
                GDQ_DATAFRAME = pd.read_html(GDQ_REQ.text)
                for Entry in GDQ_DATAFRAME:
                    for index in range(0, len(Entry["Run"]), 2):
                        runEntry = Entry["Run"]
                        timeEntry = Entry["Time & Length"].fillna(
                            "0:00:00")  # For NaN Times
                        GameTime = parse(timeEntry[index])
                        GameDuration = datetime.strptime(
                            timeEntry[index+1], "%H:%M:%S")
                        GameDelta = timedelta(
                            hours=GameDuration.hour, minutes=GameDuration.minute, seconds=GameDuration.second)
                        GameTimeStamp = datetime.timestamp(
                            GameTime + GameDelta)
                        if datetime.timestamp(datetime.now()) < GameTimeStamp and datetime.now().date() <= GameTime.date():
                            if index == 0:
                                await ctx.respond(f"Zu Beginn von GDQ am {('Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag')[GameTime.weekday()]} den {GameTime.date().strftime('%d.%m.%Y')} läuft {runEntry[index]} {runEntry[index+1]} mit {Entry['Runners & Host'][index]}!")
                            elif index != 0 and option == "spaeter":
                                await ctx.respond(f"Bei GDQ läuft als nächstes {runEntry[index+2]} {runEntry[index+3]} von {Entry['Runners & Host'][index+2]}!")
                                logging.info(
                                    f"{ctx.author} wanted to know the current game that is run at GDQ.")
                            else:
                                await ctx.respond(f"Bei GDQ läuft gerade {runEntry[index]} {runEntry[index+1]} von {Entry['Runners & Host'][index]}!")
                                logging.info(
                                    f"{ctx.author} wanted to know the next game that is run at GDQ.")
                            break
                    else:
                        await ctx.respond("GDQ ist vorbei oder noch nicht angefangen, beehre uns bald wieder.")
                        logging.info(
                            f"{ctx.author} wanted to know the current game that is run at GDQ, but GDQ has not started or is done.")
            except ValueError:
                await ctx.respond("GDQ ist vorbei oder noch nicht angefangen, beehre uns bald wieder.")
                logging.warning(
                    f"{ctx.author} wanted to know the current game that is run at GDQ, but there is no schedule live.")
            except:
                logging.error("ERROR: ", exc_info=True)
        else:
            await ctx.respond("GDQ ist vorbei oder noch nicht angefangen, beehre uns bald wieder.")
            logging.error(
                f"{ctx.author} wanted to know the current game that is run at GDQ, the website is not responding.")

    @_gdqgame.error
    async def _gdqgame_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.", ephemeral=True)
            logging.warning(f"{ctx.author} wanted to spam the GDQ command!")

def setup(bot):
    bot.add_cog(GDQ(bot))
