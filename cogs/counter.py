import random

from discord.ext import commands

from Main import (_get_banned_users, _is_banned, _read_json, _write_json,
                  discord, logging)


async def _inc_counter(invoker: discord.ApplicationContext, name: str, incnum: int):
    data = _read_json('Settings.json')
    data['Settings']['Counter'][f'{name.title()}'] = data['Settings']['Counter'][f'{name.title()}'] + incnum
    LastAboNumber = data['Settings']['Counter']['LastAboAt']
    NewResult = data['Settings']['Counter'][f'{name}']
    if name == "luck" and ((NewResult - LastAboNumber) + random.SystemRandom().randint(0, 50) >= (LastAboNumber+100)):
        logging.info(
            f"{invoker.author.name} increased the counter of {name} with invokeparameter {name} and had dotoluck. Subs are given out next stream.")
        await invoker.respond(f"Doto hatte schon wieder Glück! Damit hat er {NewResult} Mal unverschämtes Glück gehabt! Als Strafe verschenkt er im nächsten Stream {random.SystemRandom().randint(1,3)} Abos!")
        data['Settings']['Counter']['LastAboAt'] = NewResult
    else:
        match (name):
            case ("Pun" | "pun"):
                ReplyTxt = "Es wurde bereits ###REPLACE### Mal ein Gagfeuerwerk gezündet!"
            case ("Salz" | "salz"):
                ReplyTxt = "Man konnte sich schon ###REPLACE### Mal nicht beherrschen! Böse Salzstreuer hier!<:salt:826091230156161045>"
            case ("Leak" | "leak"):
                ReplyTxt = "Da hat wohl jemand nicht aufgepasst... Es wurde bereits ###REPLACE### Mal geleakt! Obacht!"
            case ("Mobbing" | "mobbing" | "Hasssprech" | "hasssprech"):
                ReplyTxt = "Das ist Hasssprech! ###REPLACE### Mal wurde schon Hasssprech betrieben! Pfui!"
            case ("Pipi" | "pipi"):
                ReplyTxt = "Dotas Babyblase hat ihn schon ###REPLACE### Mal auf das stille Örtchen getrieben!"
            case ("Luck" | "luck" | "Dotoluck" | "dotoluck"):
                ReplyTxt = "Doto hatte schon wieder Glück! Damit hat er ###REPLACE### Mal unverschämtes Glück gehabt!"
            case ("Schnenko" | "schnenko" | "Schnenk" | "schnenk" | "lieferando" | "Lieferando"):
                ReplyTxt = "Schnenko hat dieses Jahr bereits für ###REPLACE###€ bei Lieferando bestellt. Ein starkes Zeichen für die Wirtschaft!"
            case _:
                logging.error(
                    f"ERROR: {invoker.author.name} wanted to increase the counter for {name} but there is none!")
                await invoker.respond("Dieser Counter konnte nicht gefunden werden.")
                return
        logging.info(
            f"{invoker.author.name} increased the counter of {name} with invokeparameter {name}.")
        await invoker.respond(ReplyTxt.replace('###REPLACE###', f'{NewResult}'))
    _write_json('Settings.json', data)


async def _show_counter(invoker: discord.ApplicationContext, name: str):
    match (name):
        case ("Pun" | "pun"):
            InvokedVar = "Puns"
            ReplyTxt = "Es gab bereits ###REPLACE### Gagfeuerwerke im Discord!"
        case ("Salz" | "Salz"):
            InvokedVar = "Salz"
            ReplyTxt = "Bisher wurden ###REPLACE### Salzstreuer geleert!<:salt:826091230156161045>"
        case ("Leak" | "leak"):
            InvokedVar = "Leak"
            ReplyTxt = "Bis dato wurden ###REPLACE### Mal sensible Informationen geleakt! Obacht!"
        case ("Mobbing" | "mobbing" | "Hasssprech" | "hasssprech"):
            InvokedVar = "Mobbing"
            ReplyTxt = "Bereits ###REPLACE### Mal wurde Hasssprech betrieben! Warum so toxisch?"
        case ("Pipi" | "pipi"):
            InvokedVar = "Pipi"
            ReplyTxt = "Doto hat bereits ###REPLACE### Mal den Stream pausiert um das WC aufzusuchen!"
        case ("Luck" | "luck" | "Dotoluck" | "dotoluck"):
            InvokedVar = "Luck"
            ReplyTxt = "Doto hatte bereits ###REPLACE### Mal unverschämtes Glück!"
        case ("Schnenko" | "schnenko" | "Schnenk" | "schnenk" | "lieferando" | "Lieferando"):
            InvokedVar = "Lieferando"
            ReplyTxt = "Aktuell hat Schnenko ###REPLACE###€ Umsatz bei Lieferando generiert, Investoren können sich freuen!"
        case _:
            logging.error(
                f"ERROR: {invoker.author.name} wanted to list the counter for {name} but there is none!")
            await invoker.respond("Dieser Counter konnte nicht gefunden werden.")
            return
    data = _read_json('Settings.json')
    logging.info(
        f"{invoker.author.name} requested the current counter for {InvokedVar} with invokeparameter {name}.")
    await invoker.respond(ReplyTxt.replace("###REPLACE###", f"{data['Settings']['Counter'][f'{InvokedVar}']}"))


class Counter(commands.Cog):

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

    @commands.slash_command(name="pun", description="Erhöht den Puncounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _puncounter(self, ctx):
        await _inc_counter(ctx, "Pun", 1)

    @commands.slash_command(name="leak", description="Erhöht den Leakcounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _leakcounter(self, ctx):
        await _inc_counter(ctx, "Leak", 1)

    @commands.slash_command(name="hasssprech", description="Erhöht den Hasssprechcounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _mobbingcounter(self, ctx):
        await _inc_counter(ctx, "Mobbing", 1)

    @commands.slash_command(name="salz", description="Erhöht den Salzcounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _saltcounter(self, ctx):
        await _inc_counter(ctx, "Salz", 1)

    @commands.slash_command(name="lieferando", description="Erhöht den Schnenkocounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _schnenkcounter(self, ctx):
        await _inc_counter(ctx, "Lieferando", 20)

    @commands.slash_command(name="babyblase", description="Erhöht den Pipicounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _pipicounter(self, ctx):
        await _inc_counter(ctx, "Pipi", 1)

    @commands.slash_command(name="dotoluck", description="Erhöht den Dotoluckcounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _luckcounter(self, ctx):
        await _inc_counter(ctx, "Luck", 1)

    @commands.slash_command(name="showpun", description="Zeigt den Puncounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _show_puncounter(self, ctx):
        await _show_counter(ctx, "Pun")

    @commands.slash_command(name="showleak", description="Zeigt den Leakcounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _show_leakcounter(self, ctx):
        await _show_counter(ctx, "Leak")

    @commands.slash_command(name="showhasssprech", description="Zeigt den Hasssprechcounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _show_mobbingcounter(self, ctx):
        await _show_counter(ctx, "Mobbing")

    @commands.slash_command(name="showsalz", description="Zeigt den Salzcounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _show_salzcounter(self, ctx):
        await _show_counter(ctx, "Salz")

    @commands.slash_command(name="showschnenk", description="Zeigt den Schnenkocounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _show_schnenkcounter(self, ctx):
        await _show_counter(ctx, "Lieferando")

    @commands.slash_command(name="showschnenk", description="Zeigt den Schnenkocounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _show_schnenkcounter(self, ctx):
        await _show_counter(ctx, "Lieferando")

    @commands.slash_command(name="showbabyblase", description="Zeigt den Pipicounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _show_pipicounter(self, ctx):
        await _show_counter(ctx, "Pipi")

    @commands.slash_command(name="showdotoluck", description="Zeigt den Luckcounter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _show_luckcounter(self, ctx):
        await _show_counter(ctx, "Luck")

    # @_counter.error
    # async def _counter_error(self, ctx, error):
    #     if isinstance(error, commands.CommandOnCooldown):
    #         await ctx.send("Dieser Befehl ist noch im Cooldown.")
    #         logging.warning(
    #             f"{ctx.author} wanted to raise a counter fast!")


def setup(bot):
    bot.add_cog(Counter(bot))
