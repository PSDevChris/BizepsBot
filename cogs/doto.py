import random

from discord import Option
from discord.ext import commands

from Main import _get_banned_users, _is_banned, _read_json, logging


def _refresh_dotojokes():
    DotoJokesJSON = _read_json('Settings.json')
    DotoJokes = list(DotoJokesJSON['Settings']['DotoJokes']['Jokes'])
    return DotoJokes


class DotoJokes(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.BannedUsers = _get_banned_users()
        bot.DotoJokes = _refresh_dotojokes()

    async def cog_check(self, ctx):
        return await _is_banned(ctx)

    # Events

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    # Commands
    @commands.slash_command(name="doto", description="Gute Witze, schlechte Witze", brief="Gute Witze, schlechte Witze")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _dotojokes(self, ctx, options: Option(str, "Zeigt oder zählt die Witze", choices=["show", "count"], required=False)):
        if options == "show":
            DotoJokesJSON = _read_json('Settings.json')
            DotoOutputString = ""
            DotoOutputLength = 0
            await ctx.respond(f"Doto hat folgende Gagfeuerwerke gezündet:\n")
            for DotoTaskEntry in DotoJokesJSON['Settings']['DotoJokes']['Jokes']:
                DotoOutputLength += len(DotoTaskEntry)
                if DotoOutputLength >= 1994:
                    await ctx.respond(f"```{DotoOutputString}```")
                    DotoOutputString = ""
                    DotoOutputLength = 0
                DotoOutputString += DotoTaskEntry + "\n\n"
                DotoOutputLength = DotoOutputLength + len(DotoTaskEntry)
            await ctx.respond(f"```{DotoOutputString}```")
        elif options == "count":
            DotoJokesJSON = _read_json('Settings.json')
            DotoJokesCount = len(
                DotoJokesJSON['Settings']['DotoJokes']['Jokes'])
            await ctx.respond(f"Doto hat bereits {DotoJokesCount} Knaller im Discord gezündet!")
        else:
            if len(self.bot.DotoJokes) == 0:
                _refresh_dotojokes()
            DotoJoke = random.SystemRandom().choice(self.bot.DotoJokes)
            await ctx.respond(f"{DotoJoke}")
            self.bot.DotoJokes.remove(DotoJoke)

    @_dotojokes.error
    async def _dotojokes_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam Doto-Jokes!")


def setup(bot):
    bot.add_cog(DotoJokes(bot))
