﻿from discord.ext import commands
from Main import _is_banned
from Main import _get_banned_users


class DDC(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.BannedUsers = _get_banned_users()

    async def cog_check(self, ctx):
        return _is_banned(ctx, self.BannedUsers)

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
