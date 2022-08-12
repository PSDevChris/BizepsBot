import discord
from discord.ext import commands
from Main import _is_banned
from Main import _get_banned_users
from Main import logging

class Fun2(commands.Cog):

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
    @commands.slash_command(name="josch", description="Entwickler...", brief="Entwickler...")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _blamedevs(self, ctx):
        await ctx.respond(file=discord.File('memes/josch700#3680/josch.png'))
        logging.info(f"{ctx.author} blamed the devs.")

    @commands.slash_command(name="turnup", description="Was für Saft?", brief="Was für Saft?")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _orangejuice(self, ctx):
        if str(ctx.author) != "Schnenko#9944":
            await ctx.respond(f"Frag nicht was für Saft, einfach Orangensaft! Tuuuuuuuurn up! Fassen Sie mich nicht an!")
        else:
            await ctx.respond(f"https://tenor.com/view/nerd-moneyboy-money-boy-hau-gif-16097814")
        logging.info(f"{ctx.author} turned up the orangensaft.")

    @commands.slash_command(name="ehrenmann", description="Der erwähnte User ist ein Ehrenmann!", brief="Der erwähnte User ist ein Ehrenmann!")
    async def _ehrenmann(self, ctx, user: discord.Option(discord.User, description="Wähle den ehrenhaften User", required=True)):
        await ctx.respond(f"{user.mention}, du bist ein gottverdammter Ehrenmann!<:Ehrenmann:955905863154036748>")
        logging.info(f"{ctx.author} wanted to let {user.name} know he is an ehrenmann.")

    @commands.slash_command(name="lebonk", description="Don't mess with him...", brief="Don't mess with him...")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _lebonk(self, ctx):
        LastMessages = await ctx.channel.history(limit=1).flatten()
        LastMessage = LastMessages[0]
        await ctx.respond("Die Nachricht wurde gebonkt!", ephemeral=True)
        await LastMessage.reply("Mess with Lechonk, you get the bonk!", file=discord.File('fun/LeBonk.png'))

    @commands.slash_command(name="pub", description="Typos...")
    async def _pubtypo(self, ctx):
        await ctx.respond(f"Das Discord Pub ist geschlossen, {ctx.author.name}! Du meintest wohl !pun?")

def setup(bot):
    bot.add_cog(Fun2(bot))
