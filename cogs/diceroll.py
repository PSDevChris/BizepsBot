import random
from discord import Option
from discord.ext import commands
from Main import _is_banned
from Main import _get_banned_users
from Main import logging


class Diceroll(commands.Cog):

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
    @commands.slash_command(name="roll", description="Rollt einen X seitigen Würfel, Standardwert ist 3", brief="Rollt einen X seitigen Würfel, Standardwert ist 3")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _rolldice(self, ctx, maxroll: Option(int, "Die Anzahl der Seiten des Würfels", required=False, default=3)):
        if maxroll == 0:
            await ctx.respond("Es gibt keinen 0 seitigen Würfel!", ephemeral=True)
        elif maxroll == 1 or maxroll == -1:
            await ctx.respond("1")
        else:
            await ctx.respond(f"{random.SystemRandom().randrange(1, abs(maxroll))}")
            logging.info(
                f"{ctx.author} rolled with value {maxroll} as max value, negative numbers were turned to absolutes.")


def setup(bot):
    bot.add_cog(Diceroll(bot))
