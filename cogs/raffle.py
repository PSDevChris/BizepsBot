import random

import discord
from discord import Option
from discord.ext import commands

from Main import (_get_banned_users, _is_banned, _read_json, _write_json,
                  logging)

### Checks ###


def _raffle_active(self):
    return self.bot.Settings['Settings']['Raffle']['Active']


class Raffle(commands.Cog, name="Raffle"):

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
    giveaway = discord.SlashCommandGroup("giveaway", "Befehle für Giveaways")

    @giveaway.command(name="join", brief="Tritt dem Giveaway bei")
    @commands.check(_raffle_active)
    async def _joinraffle(self, ctx):
        NewEntry = {
            f"{ctx.author.name}": ctx.author.mention
        }
        if ctx.author.name not in self.bot.Settings['Settings']['Raffle']['Entries'].keys():
            self.bot.Settings['Settings']['Raffle']['Entries'].update(NewEntry)
            await ctx.respond("Du wurdest zum Raffle hinzugefügt.")
        else:
            await ctx.respond("Du bist bereits im Raffle, jeder nur ein Los!")
        _write_json('Settings.json', self.bot.Settings)

    @giveaway.command(name="show", brief="Zeigt das aktuelle Giveaway")
    @commands.check(_raffle_active)
    async def _showraffle(self, ctx):
        ctx.respond(
            f"Aktuell wird {self.bot.Settings['Settings']['Raffle']['Title']} verlost!")

    @commands.slash_command(name="set_giveaway", description="Setzt ein Giveaway Preis")
    @discord.default_permissions(administrator=True)
    @commands.has_role("Admin")
    async def _set_giveaway(self, ctx, prize: Option(str, description="Der Preis", required=True)):
        """
        Setzt den Preis für ein Giveaway.
        """
        CurrentPrize = self.bot.Settings['Settings']['Raffle']['Title']
        if CurrentPrize != "":
            await ctx.respond(f"Aktuell ist {CurrentPrize} noch im Giveaway eingetragen!")
        else:
            self.bot.Settings['Settings']['Raffle']['Title'] = prize
            self.bot.Settings['Settings']['Raffle']['Active'] = True
            _write_json('Settings.json', self.bot.Settings)
            await ctx.respond(f"{prize} wurde zum Giveaway hinzugefügt!")

    @commands.slash_command(name="start_giveaway", description="Startet ein Giveaway", brief="Startet ein Giveaway")
    @discord.default_permissions(administrator=True)
    @commands.has_role("Admin")
    async def _start_giveaway(self, ctx):
        """
        Startet ein Giveaway.
        """
        CurrentPrize = self.bot.Settings['Settings']['Raffle']['Title']
        CurrentState = self.bot.Settings['Settings']['Raffle']['Active']
        if CurrentPrize != "" and CurrentState:
            await ctx.respond(f"Das neue Raffle wurde aktiviert! Teilnehmen könnt ihr über /giveaway join, verlost wird {self.bot.Settings['Settings']['Raffle']['Title']}!")
        else:
            await ctx.respond(f"Es fehlt der Preis oder der Status wurde nicht auf aktiv gesetzt! Preis: {CurrentPrize} State: {CurrentState}!")

    @commands.slash_command(name="stop_giveaway", description="Beendet ein Giveaway")
    @discord.default_permissions(administrator=True)
    @commands.has_role("Admin")
    async def _stop_giveaway(self, ctx):
        """
        Beendet ein Giveaway.
        """
        EntryList = list(self.bot.Settings['Settings']
                         ['Raffle']['Entries'].items())
        if EntryList == []:
            await ctx.respond("Leider hat niemand teilgenommen. Viel Glück beim nächsten Mal!")
        else:
            Entry = random.SystemRandom().choice(EntryList)
            await ctx.respond(f"Das Raffle wurde beendet! {self.bot.Settings['Settings']['Raffle']['Title']} wurde von {Entry[0]}, {Entry[1]} gewonnen!")
        self.bot.Settings['Settings']['Raffle']['Entries'] = {}
        self.bot.Settings['Settings']['Raffle']['Title'] = ""
        self.bot.Settings['Settings']['Raffle']['Active'] = False
        _write_json('Settings.json', self.bot.Settings)

    @_start_giveaway.error
    async def _showlog_error(self, ctx, error):
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Na na, das darf nur der Admin.")
            logging.warning(f"{ctx.author} wanted to start a giveaway!")

    @_stop_giveaway.error
    async def _showlog_error(self, ctx, error):
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Na na, das darf nur der Admin.")
            logging.warning(f"{ctx.author} wanted to stop a giveaway!")

    @_set_giveaway.error
    async def _setgiveaway_error(self, ctx, error):
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Na na, das darf nur der Admin.")
            logging.warning(f"{ctx.author} wanted to set a giveaway!")

    @_joinraffle.error
    async def _giveaway_join_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Es ist kein Giveaway aktiv!")
            logging.info(
                f"{ctx.author} wanted to join a giveaway, but none are running.")
        else:
            logging.error(f"{error}")  # Raise other errors

    @_showraffle.error
    async def _giveaway_show_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Es ist kein Giveaway aktiv!")
            logging.info(
                f"{ctx.author} wanted to join a giveaway, but none are running.")
        else:
            logging.error(f"{error}")  # Raise other errors


def setup(bot):
    bot.add_cog(Raffle(bot))
