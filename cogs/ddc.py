import discord
from discord.ext import commands

class DDC(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    # Commands
    @commands.command()
    async def ping(self, ctx):
        await ctx.send("Pong!")

def setup(bot):
    bot.add_cog(DDC(bot))