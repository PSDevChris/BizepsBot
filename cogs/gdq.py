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
        ListOfRuns = []
        ListOfTime = []
        GDQ_URL = "https://gamesdonequick.com/schedule"
        GDQ_REQ = requests.get(GDQ_URL)
        GDQ_DATAFRAME = pd.read_html(GDQ_REQ.text)
        for Entry in GDQ_DATAFRAME:
            ListOfRuns.append(Entry["Run"])
            ListOfTime.append(Entry["Time & Length"])
        mydf = pd.DataFrame()
        for ListElement in ListOfRuns:
            mydf["Runs"] = ListElement
        for ListElement in ListOfTime:
            mydf["Time and Length"] = ListElement
        for i in range(len(mydf["Time and Length"])):
            if i % 2 == 0:
                GameTime = parse(mydf["Time and Length"].iloc[i])
                GameDuration = datetime.strptime(
                    mydf["Time and Length"].iloc[i+1], "%H:%M:%S")
                GameDelta = timedelta(
                    hours=GameDuration.hour, minutes=GameDuration.minute, seconds=GameDuration.second)
                GameTimeStamp = datetime.timestamp(GameTime + GameDelta)
                if datetime.timestamp(datetime.now()) < GameTimeStamp:
                    await ctx.send(f"Bei GDQ läuft gerade {mydf['Runs'].iloc[i]} {mydf['Runs'].iloc[i+1]}!")
                    break
            else:
                if i == len(mydf["Time and Length"])-1:
                    await ctx.send("GDQ ist vorbei, beehre uns bald wieder.")
                else:
                    continue

def setup(bot):
    bot.add_cog(GDQ(bot))