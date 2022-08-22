from discord.ext import commands
from Main import _is_banned
from Main import _get_banned_users
from Main import logging


class DDC(commands.Cog):

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
    @commands.slash_command(name="ping", description="Macht Pong!", brief="Macht Pong")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _ping(self, ctx):
        await ctx.respond("Pong!")
        logging.info(f"{ctx.author} requested a pong.")


def setup(bot):
    bot.add_cog(DDC(bot))
