import random

from discord.ext import commands

from Main import (BeautifulSoup, _get_banned_users, _is_banned, json, logging,
                  requests)


class Misc(commands.Cog):

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

    @commands.slash_command(name="zucker", description="Zuckersüß")
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def _zuggishow(self, ctx):
        await ctx.defer()
        RandomIndex = random.randrange(0, 990, 30)
        RecipURL = requests.get(
            f"https://www.chefkoch.de/rs/s{RandomIndex}/kartoffel/Rezepte.html")
        if RecipURL.status_code == 200:
            RecipHTML = BeautifulSoup(RecipURL.text, "html.parser")
            RecipJSON = json.loads("".join(RecipHTML.find_all(
                "script", {"type": "application/ld+json"})[1]))
            RandomRecipIndex = random.randint(0, 30)
            RecipElementName = RecipJSON['itemListElement'][RandomRecipIndex]['name']
            RecipElementURL = RecipJSON['itemListElement'][RandomRecipIndex]['url']
            await ctx.followup.send(f"{RecipElementName}\n{RecipElementURL}")
        else:
            await ctx.respond("Kartoffel API ist leider down T_T")

    # Error Handling for Commands
    @_zuggishow.error
    async def _zuggishow_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond("Dieser Befehl ist noch im Cooldown.")
            logging.warning(f"{ctx.author} wanted to spam the zuggicommand!")


def setup(bot):
    bot.add_cog(Misc(bot))
