import json
import random

import aiohttp
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

    async def get_waifu_img(self) -> dict[str, str | list] | None:
        waifurl = "https://api.waifu.im/search"

        return_dict = {
            "url": "",
            "name": "",
            "urls": [],
        }
        async_timeout = aiohttp.ClientTimeout(total=2)

        async with aiohttp.ClientSession(headers={"Content-Type": "application/json"}, timeout=async_timeout) as aiosession, aiosession.get(waifurl) as res:
            if res.status != 200:
                logging.error("Waifu API returned status code != 200!")
                return None

            try:
                img_json = (await res.json())["images"][0]
                return_dict["url"] = img_json["url"]
                if (artist := img_json["artist"]) is not None:
                    return_dict["name"] = artist["name"]
                    return_dict["urls"] = [page[1] for page in artist.items() if page[0] in ["patreon", "pixiv", "twitter", "deviant_art"] and page[1] is not None]
            except json.decoder.JSONDecodeError:
                logging.error("Waifu JSON Decode failed!")
                return None
            except KeyError:
                logging.error("Waifu key error: Something is wrong with the JSON file!")
                return None

            return return_dict

    # Commands
    @commands.slash_command(name="josch", description="Entwickler...", brief="Entwickler...")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _blamedevs(self, ctx):
        await ctx.defer()
        await ctx.followup.send(file=discord.File("memes/josch700 (josch700)/josch.png"))
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

    @commands.slash_command(name="schnabi", description="Er malt gerne!", brief="Er malt gerne!")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _schnabi(self, ctx: discord.context.ApplicationContext):
        if (waifu_data := await self.get_waifu_img()) is None:
            await ctx.respond("Heute keine Waifus für dich, fass mal Gras an :)")
            return

        embed = discord.Embed(title="Hat da jemand Waifu gesagt?", colour=discord.Colour(0xA53D8F)).set_image(url=waifu_data["url"])

        if waifu_data["name"]:
            embed.add_field(name="**Künstler*in**", value=waifu_data["name"])
        if waifu_data["urls"]:
            embed.add_field(name="**Artist Links (Achtung, vielleicht NSFW Content)**", value="\n".join(waifu_data["urls"]), inline=False)

        await ctx.respond(embed=embed)

    @commands.Cog.listener("on_message")
    async def _uwumsg(self, message):
        if isinstance(message.channel, discord.channel.DMChannel) or message.channel.category_id == 539547423782207488 or message.channel.id == 539549544585756693 or message.author == self.bot.user:
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

    @_schnabi.error
    async def _schnabi_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.", ephemeral=True)
            logging.warning(f"{ctx.author} wanted to spam the Schnabicommand!")


def setup(bot):
    bot.add_cog(Fun(bot))
