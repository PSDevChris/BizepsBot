import os

import discord
from discord import Option
from discord.ext import commands

from Main import _get_banned_users, _is_banned, _write_json, logging, requests


class Management(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await _is_banned(ctx)

    # Events

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    # Commands
    @commands.slash_command(name="reload_settings", description="Lädt alle Einstellungen des Bots neu", brief="Lädt alle Einstellungen des Bots neu")
    @discord.default_permissions(administrator=True)
    async def _reload_settings(self, ctx):
        self.bot.reload_settings()
        await ctx.respond("Die Boteinstellungen wurden neugeladen.")

    @commands.slash_command(name="add_dotojoke", description="Ein guter oder schlechter Witz wird hinzugefügt", brief="Ein guter oder schlechter Witz wird hinzugefügt")
    @discord.default_permissions(administrator=True)
    # just added as safety so if the default_perm is missing, it is not invoking
    @commands.has_role("Admin")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _add_dotojoke(self, ctx, joke: Option(str, "Besagter Witz", required=True)):
        self.bot.Settings["Settings"]["DotoJokes"]["Jokes"].append(joke)
        _write_json("Settings.json", self.bot.Settings)
        self.bot.DotoJokes.append(joke)
        await ctx.respond(f"Der Schenkelklopfer '{joke}' wurde hinzugefügt.")

    @commands.slash_command(name="ip", description="Gibt die aktuelle public IP aus")
    @discord.default_permissions(administrator=True)
    @commands.has_any_role("Admin", "Moderatoren")
    async def _returnpubip(self, ctx):
        MyIP = requests.get("https://api.ipify.org").content.decode("UTF-8")
        await ctx.respond(f"Die aktuelle IP lautet: {MyIP}", ephemeral=True)
        logging.info(f"{ctx.author} requested the public ip.")

    @commands.slash_command(name="log", description="Zeigt die neusten Logeinträge des Bots", brief="Zeigt die neusten Logeinträge des Bots")
    @discord.default_permissions(administrator=True)
    @commands.has_role("Admin")
    async def _showlog(self, ctx):
        """
        Zeigt die letzten 10 Einträge des Logs.
        """
        AllLogFiles = next(os.walk("logs/"))[2]
        SortedLogFiles = sorted(AllLogFiles)
        LatestLogFile = SortedLogFiles[-1]
        with open(f"logs/{LatestLogFile}", "r") as LogFileRead:
            LogContent = LogFileRead.readlines()
            LatestLogLines = LogContent[-10:]
            LogOutputInString = "".join(LatestLogLines)
            await ctx.defer()
            await ctx.followup.send(f"```{LogOutputInString}```")
        logging.info(f"{ctx.author} has called for the log.")

    @commands.slash_command(name="block", description="Hindert den User am verwenden von Commands")
    @discord.default_permissions(moderate_members=True)
    @commands.has_any_role("Admin", "Moderatoren")
    async def _banuser(self, ctx, user: discord.Member):
        UserString = str(user)
        BannedUsers = self.bot.Settings["Settings"]["BannedUsers"]
        if UserString not in BannedUsers:
            BannedUsers.append(UserString)
            _write_json("Settings.json", self.bot.Settings)
            await ctx.respond(f"User {UserString} wurde für Befehle gebannt.")
            logging.info(f"User {UserString} was banned from using commands.")
            _get_banned_users()
        else:
            await ctx.respond("Dieser User ist bereits gebannt.")

    @commands.slash_command(name="unblock", description="Gibt den User für Commands frei")
    @discord.default_permissions(moderate_members=True)
    @commands.has_any_role("Admin", "Moderatoren")
    async def _unbanuser(self, ctx, user: discord.Member):
        UserString = str(user)
        BannedUsers = self.bot.Settings["Settings"]["BannedUsers"]
        if UserString in BannedUsers:
            BannedUsers.remove(UserString)
            _write_json("Settings.json", self.bot.Settings)
            await ctx.respond(f"Der User {UserString} wurde entbannt.")
            logging.info(f"User {UserString} was unbanned.")
            _get_banned_users()
        else:
            await ctx.respond(f"Der Benutzer {UserString} ist nicht gebannt.")

    TwitchManagement = discord.SlashCommandGroup("twitch", "Managed die Twitchliste")

    @TwitchManagement.command(name="add", description="Fügt jemanden der Twitchliste hinzu")
    @discord.default_permissions(administrator=True)
    @commands.cooldown(3, 900, commands.BucketType.user)
    @commands.has_role("Admin")
    async def _addtotwitchlist(self, ctx, member: str, custommsg: str):
        try:
            await ctx.defer()
            TwitchMember = {f"{member.lower()}": {"live": False, "custom_msg": f"{custommsg}"}}
            self.bot.Settings["Settings"]["TwitchUser"].update(TwitchMember)
            _write_json("Settings.json", self.bot.Settings)
            await ctx.followup.send(f"{member} zur Twitchliste hinzugefügt! Folgender Satz wurde hinterlegt: '{custommsg}'")
            logging.info(f"User {member} was added to twitchlist with custom message: '{custommsg}'")
        except Exception:
            await ctx.respond("Konnte User nicht hinzufügen.")
            logging.error(f"User {member} could not be added.", exc_info=True)

    @TwitchManagement.command(name="delete", description="Entfernt jemanden aus der Twitchliste")
    @discord.default_permissions(administrator=True)
    @commands.cooldown(3, 900, commands.BucketType.user)
    @commands.has_role("Admin")
    async def _deltwitchmember(self, ctx, member: str):
        try:
            self.bot.Settings["Settings"]["TwitchUser"].pop(f"{member.lower()}")
            _write_json("Settings.json", self.bot.Settings)
            twitchuserrole = discord.utils.get(ctx.guild.roles, name=f"{member.lower()} Alert")
            if twitchuserrole is not None:  # if it is None role is already gone
                await twitchuserrole.delete()
            logging.info(f"Removed Alertgroup for {member.lower()}.")
            await ctx.respond(f"{member} wurde aus der Twitchliste entfernt.")
            logging.info(f"User {member} was removed from twitchlist.")
        except Exception:
            await ctx.respond("Konnte User nicht entfernen.")
            logging.error(f"User {member} could not be removed from twitchlist.", exc_info=True)

    @TwitchManagement.command(name="show", description="Zeigt alle Mitglieder der Liste an")
    @discord.default_permissions(administrator=True)
    @commands.cooldown(3, 900, commands.BucketType.user)
    @commands.has_role("Admin")
    async def _showtwitchmembers(self, ctx):
        TwitchUserString = "\n".join(self.bot.Settings["Settings"]["TwitchUser"].keys())
        await ctx.defer()
        await ctx.followup.send(f"Folgende User sind hinterlegt:\n```{TwitchUserString}```")
        logging.info("Twitchlist was posted.")

    @commands.slash_command(name="extension", description="Verwaltet die Extensions")
    @discord.default_permissions(administrator=True)
    async def _extensions(self, ctx, changearg: Option(str, "laden/entladen", choices=["load", "unload"], required=True), extension):
        """
        Verwaltet die externen Cogs.

        Load:   Lädt die Cog in den Bot.
        Unload: Entfernt die Cog aus dem Bot.
        """
        if changearg == "load":
            self.bot.load_extension(f"cogs.{extension}")
            await ctx.respond(f"Extension {extension} wurde geladen und ist jetzt einsatzbereit.")
            logging.info(f"Extension {extension} was loaded.")
        elif changearg == "unload":
            self.bot.unload_extension(f"cogs.{extension}")
            await ctx.respond(f"Extension {extension} wurde entfernt und ist nicht mehr einsatzfähig.")
            logging.info(f"Extension {extension} was unloaded.")

    # Error Checking

    @TwitchManagement.error
    async def _twitchmanagement_error(self, ctx, error):
        if isinstance(error, discord.errors.CheckFailure):
            AdminToNotify = 248181624485838849
            await ctx.send(f"Na na, das darf nur der Admin! <@{AdminToNotify}>, hier möchte jemand in die Twitchliste oder aus der Twitchliste entfernt werden!")
            logging.warning(f"{ctx.author} wanted to edit the twitchlist!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Hier fehlte der User oder der Parameter!")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Der Befehl ist aktuell noch im Cooldown.")

    @_showlog.error
    async def _showlog_error(self, ctx, error):
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Na na, das darf nur der Admin.")
            logging.warning(f"{ctx.author} wanted to read the logs!")

    @_add_dotojoke.error
    async def _add_dotojokes_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam add Doto-Jokes!")
        elif isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Nur Doto darf so schlechte Witze machen und hinzufügen.")
            logging.warning(f"{ctx.author} wanted to add Doto-Jokes!")


def setup(bot):
    bot.add_cog(Management(bot))
