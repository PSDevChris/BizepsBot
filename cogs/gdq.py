from datetime import datetime, timedelta
import discord
from discord.ext import commands
import requests
import pandas as pd
from dateutil.parser import parse

class GDQ(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    ### Get the GDQ Schedule and show which game is running ###
    @commands.command(name="gdqgame", aliases=["GDQgame", "GDQGame"], brief="Gibt das aktuelle GDQ Game, Runner und Kategorie aus")
    async def _gdqgame(self, ctx):
        GDQ_URL = "https://gamesdonequick.com/schedule"
        GDQ_REQ = requests.get(GDQ_URL)
        GDQ_DATAFRAME = pd.read_html(GDQ_REQ.text)
        for Entry in GDQ_DATAFRAME:
            for index in range(0, len(Entry["Run"]), 2):
                runEntry = Entry["Run"]
                timeEntry = Entry["Time & Length"]
                GameTime = parse(timeEntry[index])
                GameDuration = datetime.strptime(timeEntry[index+1], "%H:%M:%S")
                GameDelta = timedelta(hours=GameDuration.hour, minutes=GameDuration.minute, seconds=GameDuration.second)
                GameTimeStamp = datetime.timestamp(GameTime + GameDelta)
                if datetime.timestamp(datetime.now()) < GameTimeStamp and datetime.now().date() == GameTime.date():
                    await ctx.send(f"Bei GDQ läuft gerade {runEntry[index]} {runEntry[index+1]}!")
                    break
            else:
                await ctx.send("GDQ ist vorbei oder noch nicht angefangen, beehre uns bald wieder.")

def setup(bot):
    bot.add_cog(GDQ(bot))