from discord import Option
from discord.ext import commands
from Main import _is_banned
from Main import _get_banned_users
from Main import random

class Diceroll(commands.Cog):

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
    @commands.slash_command(name="roll", description="Rollt einen X seitigen Würfel, Standardwert ist 3", brief="Rollt einen X seitigen Würfel, Standardwert ist 3")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _rolldice(self, ctx, maxroll: Option(int, "Die Anzahl der Seiten des Würfels", required=False, default=3)):
        await ctx.respond(f"{random.SystemRandom().randrange(1, maxroll)}")


def setup(bot):
    bot.add_cog(Diceroll(bot))
