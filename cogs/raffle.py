from discord.ext import commands
from Main import _is_banned
from Main import _read_json
from Main import _write_json
from Main import _get_banned_users
import random

### Checks ###


def _raffle_active(self):
    RaffleJSON = _read_json('Settings.json')
    return RaffleJSON['Settings']['Raffle']['Active']


class Raffle(commands.Cog, name="Raffle"):

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
    @commands.group(name="Raffle", aliases=["raffle"], brief="Startet ein Raffle oder beendet es.")
    @commands.has_role("Admin")
    async def _raffle(self, ctx):
        pass

    @_raffle.command(name="active", aliases=["Active"], brief="Aktiviert das Raffle")
    @commands.has_role("Admin")
    async def _setactive(self, ctx, activeval: bool):
        activeval = bool(activeval)
        RaffleJSON = _read_json('Settings.json')
        RaffleJSON['Settings']['Raffle']['Active'] = activeval
        _write_json('Settings.json', RaffleJSON)
        if activeval == True:
            await ctx.send(f"Das neue Raffle wurde aktiviert! Teilnehmen könnt ihr über !raffle join, verlost wird {RaffleJSON['Settings']['Raffle']['Title']}!")
        else:
            RaffleJSON = _read_json('Settings.json')
            EntryList = list(RaffleJSON['Settings']
                             ['Raffle']['Entries'].items())
            if EntryList == []:
                await ctx.send("Leider hat niemand teilgenommen. Viel Glück beim nächsten Mal!")
            else:
                Entry = random.SystemRandom().choice(EntryList)
                await ctx.send(f"Das Raffle wurde beendet! Gewonnen hat {Entry[0]}! {Entry[1]}")
            RaffleJSON['Settings']['Raffle']['Entries'] = {}
            RaffleJSON['Settings']['Raffle']['Title'] = ""
            _write_json('Settings.json', RaffleJSON)

    @_raffle.command(name="price", aliases=["Price"], brief="Setzt den Preis fest")
    @commands.has_role("Admin")
    async def _setprize(self, ctx, title: str):
        RaffleJSON = _read_json('Settings.json')
        RaffleJSON['Settings']['Raffle']['Title'] = title
        _write_json('Settings.json', RaffleJSON)
        await ctx.send(f"Das Raffle für {title} wurde angelegt.")

    @_raffle.command(name="join", aliases=["Join", "enter", "Enter"], brief="Tritt dem Raffle bei")
    @commands.check(_raffle_active)
    async def _joinraffle(self, ctx):
        RaffleJSON = _read_json('Settings.json')
        NewEntry = {
            f"{ctx.author.name}": ctx.author.mention
        }
        if ctx.author.name not in RaffleJSON['Settings']['Raffle']['Entries'].keys():
            RaffleJSON['Settings']['Raffle']['Entries'].update(NewEntry)
            await ctx.send("Du wurdest zum Raffle hinzugefügt.")
        else:
            await ctx.send("Du bist bereits im Raffle, jeder nur ein Los!")
        _write_json('Settings.json', RaffleJSON)


def setup(bot):
    bot.add_cog(Raffle(bot))
