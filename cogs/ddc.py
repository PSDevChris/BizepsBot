import discord
from discord.ext import commands
from Main import _is_banned


class DDC(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return _is_banned(ctx)

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    # Commands
    @commands.command(name="ping", aliases=["Ping"], brief="Macht Pong")
    async def _ping(self, ctx):
        await ctx.send("Pong!")


def setup(bot):
    bot.add_cog(DDC(bot))
