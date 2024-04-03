import random

import discord
import uwuify
from discord.ext import commands

from Main import _get_banned_users, _is_banned, logging


# Checks
def _is_zuggi(ctx):
    return ctx.author.id == 232561052573892608


def _is_nouwuchannel(ctx):
    return ctx.channel.category_id != 539547423782207488 and ctx.channel.id != 539549544585756693


class Fun(commands.Cog):
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
    @commands.slash_command(name="josch", description="Entwickler...", brief="Entwickler...")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _blamedevs(self, ctx):
        await ctx.defer()
        await ctx.followup.send(file=discord.File("memes/josch700#0/josch.png"))
        logging.info(f"{ctx.author} blamed the devs.")

    @commands.slash_command(name="turnup", description="Was für Saft?", brief="Was für Saft?")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _orangejuice(self, ctx):
        if str(ctx.author) != "Schnenko#9944":
            await ctx.respond("Frag nicht was für Saft, einfach Orangensaft! Tuuuuuuuurn up! Fassen Sie mich nicht an!")
        else:
            await ctx.respond("https://tenor.com/view/nerd-moneyboy-money-boy-hau-gif-16097814")
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
        if LastMessage.author == self.bot.user:
            await ctx.respond("Das ist eine Nachricht von mir, die bonke ich nicht.", ephemeral=True)
        else:
            await ctx.defer(ephemeral=True)
            await ctx.followup.send("Die Nachricht wurde gebonkt!")
            await LastMessage.reply(f"Mess with Lechonk, you get the bonk! Du wurdest gebonkt von {ctx.author.name}!", file=discord.File("fun/LeBonk.png"))

    @commands.slash_command(name="pub", description="Typos...")
    async def _pubtypo(self, ctx):
        await ctx.respond(f"Das Discord Pub ist geschlossen, {ctx.author.name}! Du meintest wohl !pun?")

    @commands.slash_command(name="neinl", description="Sie sagte nein.")
    async def _noL(self, ctx):
        ElisabotList = [
            "frag doch einfach nochmal",
            "sie hat gerade einen kreativen Flow",
            "auch zu Lieferando",
            "denn es ist Käseabend, meine Kerl*innen",
            "denn das Arbeitszimmer ist besetzt",
            "weil die Aperolspur ist voll",
            "aber vielleicht morgen nicht mehr",
            "weil sie es kann",
            "auch wenn es keinen Grund gibt",
            "denn sie zahlt nicht umsonst Apple TV+",
            "Elisabot will wandern gehen",
            "die Bolo-Avocado ist gleich fertig",
            "denn die Bildschirmzeit ist aufgebraucht",
            "Fehler LC-208",
            "denn Elisabot hat Besuch",
            "denn er will es ja auch",
            "denn das 800€ Ticket muss genutzt werden",
            "denn Quinoa ist das neue Gyros",
            "es muss ein Innlandsflug gebucht werden",
        ]
        await ctx.respond(f"Elisabot sagt nein, {random.SystemRandom().choice(ElisabotList)}.")

    @commands.slash_command(name="nein", description="Nein.")
    @commands.check(_is_zuggi)
    async def _zuggisaysno(self, ctx: discord.ApplicationContext):
        LastMessages = await ctx.channel.history(limit=1).flatten()
        LastMessage = LastMessages[0]
        logging.info(f"{ctx.author.name} has invoked the nein command.")
        if LastMessage.author == self.bot.user:
            await ctx.respond("Das ist eine Nachricht von mir, die verneine ich nicht.", ephemeral=True)
        else:
            await LastMessage.reply("Zuggi sagt nein.")
            await ctx.respond("Nachricht wurde verneint!", ephemeral=True)

    @commands.slash_command(name="uwu", description="Weebt die Message UwU")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.check(_is_nouwuchannel)
    async def _uwuthis(self, ctx):
        LastMessages = await ctx.channel.history(limit=1).flatten()
        if LastMessages[0].author == self.bot.user:
            await ctx.respond("Ich uwue meine Nachricht nicht!", ephemeral=True)
            return
        if LastMessages[0].content == "":
            await ctx.respond("Die Nachricht enthält keinen Text!", ephemeral=True)
            return
        flags = uwuify.SMILEY | uwuify.YU
        await ctx.respond(uwuify.uwu(LastMessages[0].content, flags=flags))
        logging.info(f"{ctx.author} hat die Nachricht [{LastMessages[0].content}] geUwUt.")

    @commands.slash_command(name="pr", description="Pullrequests einreichen zur Übername... oder so")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def _dont_ask(self, ctx):
        await ctx.respond("https://i.redd.it/before-t8-was-announced-harada-said-dont-ask-me-for-shit-v0-e4arzhnywrda1.jpg?width=451&format=pjpg&auto=webp&s=0ec112c803a3a927add3aad4eabafcb83a0bedec")

    @commands.Cog.listener("on_message")
    async def _uwumsg(self, message):
        if isinstance(message.channel, discord.channel.DMChannel) or message.channel.category_id == 539547423782207488 or message.channel.id == 539549544585756693:
            pass
        else:
            if message.author == self.bot.user:
                return
            if random.randint(0, 75) == 1 and len(message.content) > 50 and "http://" not in message.content and "https://" not in message.content:  # noqa: S311
                LastMessageContent = message.content
                flags = uwuify.SMILEY | uwuify.YU
                await message.channel.send(f"{uwuify.uwu(LastMessageContent, flags=flags)} <:UwU:870283726704242698>")
                logging.info(f"The message [{LastMessageContent}] was UwUed.")

    @_lebonk.error
    async def _bonk_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuche in {int(error.retry_after)} Sekunden nochmal jemand zu bonken.", ephemeral=True)
            logging.warning(f"{ctx.author} wanted to spam the Bonkcommand!")

    @_zuggisaysno.error
    async def _zuggisaysno_error(self, ctx, error):
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Du bist nicht Zuggi.", ephemeral=True)
            logging.warning(f"{ctx.author} wanted to nein something, but is not Zuggi.")

    @_uwuthis.error
    async def _uwuthis_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.", ephemeral=True)
            logging.warning(f"{ctx.author} wanted to spam the UwUcommand!")

    @_dont_ask.error
    async def _dont_ask_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.", ephemeral=True)
            logging.warning(f"{ctx.author} wanted to spam the Haradacommand!")


def setup(bot):
    bot.add_cog(Fun(bot))
