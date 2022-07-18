import discord
from discord import Option
from discord.ext import commands
from Main import _is_banned
from Main import _get_banned_users
from Main import _read_json
from Main import logging
from Main import _write_json

class Management(commands.Cog):

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
    @commands.slash_command(name="add_dotojoke", description="Ein guter oder schlechter Witz wird hinzugefügt", brief="Ein guter oder schlechter Witz wird hinzugefügt")
    @discord.default_permissions(administrator=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _add_dotojoke(self, ctx, joke: Option(str, "Besagter Witz", required=True)):
        DotoJokesJSON = _read_json('Settings.json')
        DotoJokesJSON['Settings']['DotoJokes']['Jokes'].append(joke)
        _write_json('Settings.json', DotoJokesJSON)
        self.bot.DotoJokes.append(joke)
        await ctx.respond(f"Der Schenkelklopfer '{joke}' wurde hinzugefügt.")
    
    @_add_dotojoke.error
    async def _add_dotojokes_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam add Doto-Jokes!")
        elif isinstance(error, commands.CheckFailure):
            await ctx.respond("Nur Doto darf so schlechte Witze machen und hinzufügen.")
            logging.warning(f"{ctx.author} wanted to add Doto-Jokes!")

def setup(bot):
    bot.add_cog(Management(bot))
