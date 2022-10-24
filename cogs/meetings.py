from discord.ext import commands
from Main import _is_banned
from Main import _get_banned_users
from Main import logging
from Main import discord
from Main import _read_json
from Main import _write_json
from Main import json
from Main import datetime


def _is_gamechannel(ctx):
    if isinstance(ctx.channel, discord.channel.DMChannel):
        return False
    else:
        return ctx.channel.category_id == 539553136222666792


class Meetings(commands.Cog):

    """
    Diese Klasse handelt alle Verabredungen, sowie deren Funktionen, wie zum Beispiel Beitritt ab.

    !Game [Uhrzeit]:        Erstellt eine Verabredung zur Uhrzeit im Format HH:mm
    !Join                   Tritt der Verabredung bei
    !RemGame                Löscht die Verabredung
    !LeaveGame              Verlässt die Verabredung, ist man Owner, wird diese gelöscht
    !UpdateGame [Uhrzeit]   Aktualisiert die Verabredung auf die angegebene Uhrzeit
    !ShowGame               Zeigt die Verabredung in diesem Channel
    """

    def __init__(self, bot):
        self.bot = bot
        self.BannedUsers = _get_banned_users()

    async def cog_check(self, ctx):
        return await _is_banned(ctx)

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.slash_command(name="startgame", description="Startet eine Verabredung")
    @commands.check(_is_gamechannel)
    async def _playgame(self, ctx, timearg):
        try:
            CurrentDate = datetime.datetime.now()
            GameTime = datetime.datetime.strptime(timearg, "%H:%M").time()
            GameDateTime = datetime.datetime.combine(CurrentDate, GameTime)
            GameDateTimeTimestamp = GameDateTime.timestamp()
        except ValueError:
            await ctx.respond("Na na, das ist keine Uhrzeit!")
            logging.warning(
                f"{ctx.author} entered a wrong time for the gamecommand!")
            return

        group = {
            f"{ctx.channel.name}": {
                "id": ctx.channel.id,
                "owner": ctx.author.mention,
                "time": GameDateTimeTimestamp,
                "members": [f"{ctx.author.mention}"]
            }
        }

        try:
            groups = _read_json('Settings.json')

            if not groups:
                groups["Settings"]["Groups"].update(group)
                _write_json('Settings.json', groups)
                await ctx.respond("Die Spielrunde wurde eröffnet!")
                logging.info(
                    f"Meeting started in {ctx.channel.name}.")
            else:
                if ctx.channel.name in groups["Settings"]["Groups"].keys():
                    await ctx.respond(f"{ctx.author.name}, hier ist schon eine Spielrunde geplant. Joine einfach mit !join")
                else:
                    groups["Settings"]["Groups"].update(group)
                    _write_json('Settings.json', groups)
                    await ctx.respond("Die Spielrunde wurde eröffnet!")
                    logging.info(
                        f"Meeting started in {ctx.channel.name}.")
        except json.decoder.JSONDecodeError:
            groups = {}
            groups["Settings"]["Groups"].update(group)
            _write_json('Settings.json', groups)
            await ctx.respond("Die Spielrunde wurde eröffnet!")
            logging.warning(
                f"The settingsfile is corrupted, overwrote the file and started meeting in {ctx.channel.name}!")

    @commands.slash_command(name="showgame", description="Zeigt die Mitglieder der Verabredung")
    @commands.check(_is_gamechannel)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def _showgame(self, ctx):
        CurrentChannel = ctx.channel.name
        GameSettings = _read_json('Settings.json')
        if ctx.channel.name in GameSettings["Settings"]["Groups"].keys():
            GameMembersString = "\n".join(
                GameSettings["Settings"]["Groups"][f"{CurrentChannel}"]["members"])
            await ctx.respond(f"Folgende Personen sind verabredet:\n{GameMembersString}")
        else:
            await ctx.respond("Hier gibt es noch keine Verabredung.")

    @commands.slash_command(name="joingame", description="Tritt einer Verabredung bei")
    @commands.check(_is_gamechannel)
    async def _joingame(self, ctx):
        CurrentChannel = ctx.channel.name
        groups = _read_json('Settings.json')

        if ctx.channel.name in groups["Settings"]["Groups"].keys() and ctx.author.mention in groups["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
            await ctx.respond(f"{ctx.author.name}, du bist bereits als Teilnehmer im geplanten Spiel.")
        elif ctx.channel.name in groups["Settings"]["Groups"].keys() and f"{ctx.author.mention}" not in groups["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
            groups["Settings"]["Groups"][f"{CurrentChannel}"]["members"].append(
                f"{ctx.author.mention}")
            await ctx.respond(f"{ctx.author.mention}, du wurdest dem Spiel hinzugefügt.")
            logging.info(
                f"{ctx.author} joined the meeting in {ctx.channel.name}.")
            _write_json('Settings.json', groups)
        else:
            await ctx.respond("In diesem Channel wurde noch kein Spiel geplant.")

    @commands.slash_command(name="updategame", description="Verschiebt das Spiel auf die gewünschte Zeit")
    @commands.check(_is_gamechannel)
    async def _movegame(self, ctx, timearg):
        CurrentChannel = ctx.channel.name
        groups = _read_json('Settings.json')

        if ctx.channel.name in groups["Settings"]["Groups"].keys() and ctx.author.mention == groups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            try:
                CurrentDate = datetime.datetime.now()
                GameTime = datetime.datetime.strptime(timearg, "%H:%M").time()
                GameDateTime = datetime.datetime.combine(CurrentDate, GameTime)
                GameDateTimeTimestamp = GameDateTime.timestamp()
            except ValueError:
                await ctx.respond("Na na, das ist keine Uhrzeit!")
                logging.warning(
                    f"{ctx.author} entered a wrong time for the updategamecommand!")
                return

            groups["Settings"]["Groups"][f"{CurrentChannel}"]["time"] = GameDateTimeTimestamp
            _write_json('Settings.json', groups)
            await ctx.respond(f"Die Uhrzeit der Verabredung wurde auf {timearg} geändert.")
            logging.info(
                f"{ctx.author} moved the meeting in {CurrentChannel} to {timearg}.")
        elif ctx.channel.name in groups["Settings"]["Groups"].keys() and ctx.author.mention != groups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            await ctx.respond("Na na, du bist nicht der Besitzer dieser Verabredung! Frag bitte den Besitzer, ob er es verschiebt!")
            logging.warning(
                f"{ctx.author} tried to move the meeting in {CurrentChannel} but is not the owner!")
        elif ctx.channel.name not in groups["Settings"]["Groups"].keys():
            await ctx.respond("Hier gibt es noch keine Verabredung. Starte doch eine!")

    @commands.slash_command(name="deletegame", description="Löscht die Verabredung")
    @commands.check(_is_gamechannel)
    async def _gameremover(self, ctx):
        CurrentChannel = ctx.channel.name
        groups = _read_json('Settings.json')
        if ctx.channel.name in groups["Settings"]["Groups"].keys() and ctx.author.mention == groups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            groups["Settings"]["Groups"].pop(CurrentChannel)
            _write_json('Settings.json', groups)
            await ctx.respond("Die Verabredung in diesem Channel wurde gelöscht.")
            logging.info(
                f"{ctx.author} deleted the meeting in {CurrentChannel}.")
        elif ctx.channel.name in groups["Settings"]["Groups"].keys() and ctx.author.mention != groups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            await ctx.respond("Na na, du bist nicht der Besitzer dieser Verabredung! Frag bitte den Besitzer, ob er diese löscht!")
            logging.warning(
                f"{ctx.author} tried to delete a meeting in {CurrentChannel} but is not the owner!")
        elif ctx.channel.name not in groups["Settings"]["Groups"].keys():
            await ctx.respond("Hier gibt es noch keine Verabredung. Starte doch eine!")

    @commands.slash_command(name="leavegame", description="Verlässt die aktuelle Verabredung")
    @commands.check(_is_gamechannel)
    async def _leavegame(self, ctx):
        CurrentChannel = ctx.channel.name
        StartedGroups = _read_json('Settings.json')
        if ctx.channel.name in StartedGroups["Settings"]["Groups"].keys() and ctx.author.mention == StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            StartedGroups["Settings"]["Groups"].pop(CurrentChannel)
            _write_json('Settings.json', StartedGroups)
            await ctx.respond(f"{ctx.author.mention}, die Verabredung in diesem Channel wurde gelöscht, da du der Besitzer warst.")
            logging.info(
                f"{ctx.author} left the meeting in {CurrentChannel} and was the owner. Meeting deleted.")
        elif ctx.channel.name in StartedGroups["Settings"]["Groups"].keys() and ctx.author.mention in StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
            StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["members"].remove(
                ctx.author.mention)
            await ctx.respond(f"{ctx.author.mention}, du wurdest aus der Verabredung entfernt.")
            logging.info(
                f"{ctx.author} removed from meeting in {CurrentChannel}.")
            _write_json('Settings.json', StartedGroups)
        elif ctx.channel.name in StartedGroups["Settings"]["Groups"].keys() and ctx.author.mention not in StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
            await ctx.respond(f"{ctx.author.mention}, du bist der Verabredung nicht beigetreten und wurdest daher auch nicht entfernt.")
            logging.info(
                f"{ctx.author} wanted to leave the meeting in {CurrentChannel}, but was not a member.")
        else:
            await ctx.respond(f"{ctx.author.mention}, hier gibt es keine Verabredung, die du verlassen könntest.")
            logging.info(
                f"{ctx.author} wanted to leave a meeting in {CurrentChannel}, but there was none.")

    ## Error Handling for Meetings Cog ###

    @_playgame.error
    async def _playgame_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond("Bitte gib eine Uhrzeit an!")
            logging.warning(f"{ctx.author} hat keine Uhrzeit angegeben!")
        elif isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Das hier ist kein Unterhaltungschannel, hier kann man sich nicht verabreden.")
            logging.warning(
                f"{ctx.author} wanted to meet outside of an entertainment channel!")

    @_joingame.error
    async def _joingame_error(self, ctx, error):
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Das hier ist kein Unterhaltungschannel, hier kann man sich nicht verabreden.")
            logging.warning(
                f"{ctx.author} wanted to meet outside of an entertainment channel!")

    @_leavegame.error
    async def _leavegame_error(self, ctx, error):
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Das hier ist kein Unterhaltungschannel, hier gibt es keine Verabredungen.")
            logging.warning(
                f"{ctx.author} wanted to leave a meeting outside of an entertainment channel!")

    @_showgame.error
    async def _showgame_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Der Befehl ist noch im Cooldown. Versuche es in {int(error.retry_after)} nocheinmal.")
            logging.warning(
                f"{ctx.author} wanted to spam the members of a game in {ctx.channel.name}!")


def setup(bot):
    bot.add_cog(Meetings(bot))
