import random

from discord.ext import commands

from Main import _is_banned, _write_json, discord, logging


class Counter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await _is_banned(ctx)

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    # Functions
    async def _inc_counter(self, invoker: discord.ApplicationContext, name: str, incnum: int):
        self.bot.Settings["Settings"]["Counter"][f"{name.title()}"] = self.bot.Settings["Settings"]["Counter"][f"{name.title()}"] + incnum
        LastAboNumber = self.bot.Settings["Settings"]["Counter"]["LastAboAt"]
        NewResult = self.bot.Settings["Settings"]["Counter"][f"{name}"]
        if name == "Luck" and ((NewResult - LastAboNumber) + random.SystemRandom().randint(0, 50) >= (LastAboNumber + 100)):
            logging.info(f"{invoker.author.name} increased the counter of {name} with invokeparameter {name} and had dotoluck. Subs are given out next stream.")
            await invoker.respond(
                f"Doto hatte schon wieder Glück! Damit hat er {NewResult} Mal unverschämtes Glück gehabt! Als Strafe verschenkt er im nächsten Stream {random.SystemRandom().randint(1,3)} Abos!"
            )
            self.bot.Settings["Settings"]["Counter"]["LastAboAt"] = NewResult
        else:
            match name:
                case "Puns" | "puns":
                    ReplyTxt = "Es wurde bereits ###REPLACE### Mal ein Gagfeuerwerk gezündet!"
                case "Salz" | "salz":
                    ReplyTxt = "Man konnte sich schon ###REPLACE### Mal nicht beherrschen! Böse Salzstreuer hier!<:salt:826091230156161045>"
                case "Leak" | "leak":
                    ReplyTxt = "Da hat wohl jemand nicht aufgepasst... Es wurde bereits ###REPLACE### Mal geleakt! Obacht!"
                case "Mobbing" | "mobbing" | "Hasssprech" | "hasssprech":
                    ReplyTxt = "Das ist Hasssprech! ###REPLACE### Mal wurde schon Hasssprech betrieben! Pfui!"
                case "Luck" | "luck" | "Dotoluck" | "dotoluck":
                    ReplyTxt = "Doto hatte schon wieder Glück! Damit hat er ###REPLACE### Mal unverschämtes Glück gehabt!"
                case "Schnenko" | "schnenko" | "Schnenk" | "schnenk" | "lieferando" | "Lieferando":
                    ReplyTxt = "Schnenko hat dieses Jahr bereits für ###REPLACE###€ bei Lieferando bestellt. Ein starkes Zeichen für die Wirtschaft!"
                case _:
                    logging.error(f"ERROR: {invoker.author.name} wanted to increase the counter for {name} but there is none!")
                    await invoker.respond("Dieser Counter konnte nicht gefunden werden.")
                    return
            logging.info(f"{invoker.author.name} increased the counter of {name} with invokeparameter {name}.")
            await invoker.respond(ReplyTxt.replace("###REPLACE###", f"{NewResult}"))
        _write_json("Settings.json", self.bot.Settings)

    async def _show_counter(self, invoker: discord.ApplicationContext, name: str):
        match name:
            case "Pun" | "pun":
                InvokedVar = "Puns"
                ReplyTxt = "Es gab bereits ###REPLACE### Gagfeuerwerke im Discord!"
            case "Salz" | "salz":
                InvokedVar = "Salz"
                ReplyTxt = "Bisher wurden ###REPLACE### Salzstreuer geleert!<:salt:826091230156161045>"
            case "Leak" | "leak":
                InvokedVar = "Leak"
                ReplyTxt = "Bis dato wurden ###REPLACE### Mal sensible Informationen geleakt! Obacht!"
            case "Mobbing" | "mobbing" | "Hasssprech" | "hasssprech":
                InvokedVar = "Mobbing"
                ReplyTxt = "Bereits ###REPLACE### Mal wurde Hasssprech betrieben! Warum so toxisch?"
            case "Luck" | "luck" | "Dotoluck" | "dotoluck":
                InvokedVar = "Luck"
                ReplyTxt = "Doto hatte bereits ###REPLACE### Mal unverschämtes Glück!"
            case "Schnenko" | "schnenko" | "Schnenk" | "schnenk" | "lieferando" | "Lieferando":
                InvokedVar = "Lieferando"
                ReplyTxt = "Aktuell hat Schnenko ###REPLACE###€ Umsatz bei Lieferando generiert, Investoren können sich freuen!"
            case _:
                logging.error(f"ERROR: {invoker.author.name} wanted to list the counter for {name} but there is none!")
                await invoker.respond("Dieser Counter konnte nicht gefunden werden.")
                return
        logging.info(f"{invoker.author.name} requested the current counter for {InvokedVar}.")
        await invoker.respond(ReplyTxt.replace("###REPLACE###", f"{self.bot.Settings['Settings']['Counter'][f'{InvokedVar}']}"))

    # Commands

    @commands.slash_command(name="pun", description="Erhöht den Puncounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _puncounter(self, ctx, option: discord.Option(str, "Zeigt den aktuellen Zählerstand", choices=["show"], required=False)):
        if option == "show":
            await Counter._show_counter(self, ctx, "Puns")
        else:
            await Counter._inc_counter(self, ctx, "Puns", 1)

    @commands.slash_command(name="leak", description="Erhöht den Leakcounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _leakcounter(self, ctx, option: discord.Option(str, "Zeigt den aktuellen Zählerstand", choices=["show"], required=False)):
        if option == "show":
            await Counter._show_counter(self, ctx, "Leak")
        else:
            await Counter._inc_counter(self, ctx, "Leak", 1)

    @commands.slash_command(name="hasssprech", description="Erhöht den Hasssprechcounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _mobbingcounter(self, ctx, option: discord.Option(str, "Zeigt den aktuellen Zählerstand", choices=["show"], required=False)):
        if option == "show":
            await Counter._show_counter(self, ctx, "Mobbing")
        else:
            await Counter._inc_counter(self, ctx, "Mobbing", 1)

    @commands.slash_command(name="salz", description="Erhöht den Salzcounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _saltcounter(self, ctx, option: discord.Option(str, "Zeigt den aktuellen Zählerstand", choices=["show"], required=False)):
        if option == "show":
            await Counter._show_counter(self, ctx, "Salz")
        else:
            await Counter._inc_counter(self, ctx, "Salz", 1)

    @commands.slash_command(name="lieferando", description="Erhöht den Schnenkocounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _schnenkcounter(self, ctx, option: discord.Option(str, "Zeigt den aktuellen Zählerstand", choices=["show"], required=False)):
        if option == "show":
            await Counter._show_counter(self, ctx, "Lieferando")
        else:
            await Counter._inc_counter(self, ctx, "Lieferando", 25)

    @commands.slash_command(name="dotoluck", description="Erhöht den Dotoluckcounter")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def _luckcounter(self, ctx, option: discord.Option(str, "Zeigt den aktuellen Zählerstand", choices=["show"], required=False)):
        if option == "show":
            await Counter._show_counter(self, ctx, "Luck")
        else:
            await Counter._inc_counter(self, ctx, "Luck", 1)

    # @_counter.error
    # async def _counter_error(self, ctx, error):
    #     if isinstance(error, commands.CommandOnCooldown):
    #         await ctx.send("Dieser Befehl ist noch im Cooldown.")
    #         logging.warning(
    #             f"{ctx.author} wanted to raise a counter fast!")


def setup(bot):
    bot.add_cog(Counter(bot))
