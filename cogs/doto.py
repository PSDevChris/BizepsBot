import io
import random

from discord import Option
from discord.ext import commands

from Main import _is_banned, _read_json, logging


def _refresh_dotojokes():
    DotoJokesJSON = _read_json("Settings.json")
    DotoJokes = list(DotoJokesJSON["Settings"]["DotoJokes"]["Jokes"])
    logging.info("Refreshed the list of Doto Jokes.")
    random.shuffle(DotoJokes)
    return DotoJokes


class DotoJokes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
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
            DotoJokesJSON = self.bot.Settings
            DotoOutputBuffer = io.StringIO()
            DotoOutputLength = 0
            await ctx.respond("Doto hat folgende Gagfeuerwerke gezündet:\n", ephemeral=True)
            for DotoTaskEntry in DotoJokesJSON["Settings"]["DotoJokes"]["Jokes"]:
                DotoOutputLength += len(DotoTaskEntry)
                if DotoOutputLength >= 1994:
                    await ctx.respond(f"```{DotoOutputBuffer.getvalue()}```", ephemeral=True)
                    DotoOutputBuffer.truncate(0)
                    DotoOutputBuffer.seek(0)  # Needs to be done in Python 3
                    DotoOutputLength = 0
                DotoOutputBuffer.write(DotoTaskEntry + "\n\n")
                DotoOutputLength = DotoOutputLength + len(DotoTaskEntry)
            if DotoOutputLength > 0:
                await ctx.followup.send(f"```{DotoOutputBuffer.getvalue()}```", ephemeral=True)
            DotoOutputBuffer.close()
            logging.info(f"{ctx.author} requested the list of Doto Jokes.")
        elif options == "count":
            DotoJokesJSON = self.bot.Settings
            DotoJokesCount = len(DotoJokesJSON["Settings"]["DotoJokes"]["Jokes"])
            await ctx.respond(f"Doto hat bereits {DotoJokesCount} Knaller im Discord gezündet!")
        else:
            if len(self.bot.DotoJokes) == 0:
                _refresh_dotojokes()
                await ctx.defer()
            DotoJoke = self.bot.DotoJokes.pop()
            logging.info(f"{ctx.author} requested a Doto Joke, the joke was [{DotoJoke}].")
            await ctx.respond(f"{DotoJoke}")
            self.bot.DotoJokes.remove(DotoJoke)

    @_dotojokes.error
    async def _dotojokes_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam Doto-Jokes!")


def setup(bot):
    bot.add_cog(DotoJokes(bot))
