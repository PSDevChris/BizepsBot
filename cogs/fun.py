import discord
from discord.ext import commands
from Main import _is_banned
from Main import _get_banned_users
from Main import logging
import uwuify

class Fun2(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.BannedUsers = _get_banned_users()

    async def cog_check(self, ctx):
        return _is_banned(ctx)
    
    # Checks 
    def _is_zuggi(ctx):
        return ctx.author.id == 232561052573892608
    
    def _is_nouwuchannel(ctx):
        return ctx.channel.category_id != 539547423782207488 and ctx.channel.id != 539549544585756693

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

    @commands.slash_command(name="nein", description="Nein.")
    @commands.check(_is_zuggi)
    async def _zuggisaysno(self, ctx: discord.ApplicationContext):
        LastMessages = await ctx.channel.history(limit=1).flatten()
        LastMessage = LastMessages[0]
        logging.info(f"{ctx.author.name} has invoked the nein command.")
        await LastMessage.reply(f"Zuggi sagt nein.")
        await ctx.respond("Nachricht wurde verneint!", ephemeral=True)

    @commands.slash_command(name="uwu", description="Weebt die Message UwU")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.check(_is_nouwuchannel)
    async def _uwuthis(self, ctx):
        LastMessages = await ctx.channel.history(limit=1).flatten()
        if LastMessages[0].author == self.bot.user:
            await ctx.respond("Ich uwue meine Nachricht nicht!", ephemeral=True)
            return
        flags = uwuify.SMILEY | uwuify.YU
        await ctx.respond(uwuify.uwu(LastMessages[0].content, flags=flags))
        logging.info(
            f"{ctx.author} hat die Nachricht [{LastMessages[0].content}] geUwUt.")

    @_zuggisaysno.error
    async def _zuggisaysno_error(self, ctx, error):
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Du bist nicht Zuggi.", ephemeral=True)
            logging.warning(
                f"{ctx.author} wanted to nein something, but is not Zuggi.")

    @_uwuthis.error
    async def _uwuthis_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.", ephemeral=True)
            logging.warning(f"{ctx.author} wanted to spam the UwUcommand!")
            
def setup(bot):
    bot.add_cog(Fun2(bot))
