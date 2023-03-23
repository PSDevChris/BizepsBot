from discord.ext import commands

from Main import (_get_banned_users, _is_banned, _read_json, _write_json,
                  datetime, discord, json, logging)


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
    !RemGame                Löscht den Erinnerer
    !LeaveGame              Verlässt den Erinnerer, ist man Owner, wird diese gelöscht
    !UpdateGame [Uhrzeit]   Aktualisiert den Erinnerer auf die angegebene Uhrzeit
    !ShowGame               Zeigt die Erinnerer in diesem Channel
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

    @commands.slash_command(name="startgame", description="Startet einen Erinnerer")
    @commands.check(_is_gamechannel)
    async def _playgame(self, ctx, time, theme):
        try:
            CurrentDate = datetime.datetime.now()
            GameTime = datetime.datetime.strptime(time, "%H:%M").time()
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
                "theme": theme,
                "time": GameDateTimeTimestamp,
                "members": [f"{ctx.author.mention}"]
            }
        }

        try:
            groups = self.bot.Settings

            if not groups:
                groups["Settings"]["Groups"].update(group)
                _write_json('Settings.json', groups)
                await ctx.respond(f"Der Erinnerer wurde erstellt mit dem Thema {theme} um {time}!")
                logging.info(
                    f"Meeting started in {ctx.channel.name} with theme: [{theme}] at {time}.")
            else:
                if ctx.channel.name in groups["Settings"]["Groups"].keys():
                    await ctx.respond(f"{ctx.author.name}, hier ist schon eine Spielrunde geplant. Joine einfach mit !join")
                else:
                    groups["Settings"]["Groups"].update(group)
                    _write_json('Settings.json', groups)
                    await ctx.respond(f"Der Erinnerer wurde erstellt mit dem Thema {theme} um {time}!")
                    logging.info(
                        f"Meeting started in {ctx.channel.name} with theme: [{theme}] at {time}.")
        except json.decoder.JSONDecodeError:
            groups = {}
            groups["Settings"]["Groups"].update(group)
            _write_json('Settings.json', groups)
            await ctx.respond(f"Der Erinnerer wurde erstellt mit dem Thema {theme} um {time}!")
            logging.warning(
                f"The settingsfile is corrupted, overwrote the file and started meeting in {ctx.channel.name}!")

    @commands.slash_command(name="showgame", description="Zeigt die Mitglieder des Erinnerers")
    @commands.check(_is_gamechannel)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def _showgame(self, ctx):
        CurrentChannel = ctx.channel.name
        GameSettings = self.bot.Settings
        if ctx.channel.name in GameSettings["Settings"]["Groups"].keys():
            CleanUsernames = []
            for user in GameSettings["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
                CleanUsername = await self.bot.get_or_fetch_user(user[2:-1])
                CleanUsernames.append(CleanUsername.display_name)
            GameMembersString = "\n".join(CleanUsernames)
            ReminderTheme = GameSettings["Settings"]["Groups"][f"{CurrentChannel}"]["theme"]
            ReminderTime = datetime.datetime.fromtimestamp(
                GameSettings["Settings"]["Groups"][f"{CurrentChannel}"]["time"], tz=datetime.datetime.utcnow().astimezone().tzinfo)
            await ctx.respond(f"Folgende Personen sind verabredet zum {ReminderTheme} um {ReminderTime:%H:%M}:\n{GameMembersString}")
        else:
            await ctx.respond("Hier gibt es noch keine Verabredung.")

    @commands.slash_command(name="joingame", description="Tritt einem Erinnerer bei")
    @commands.check(_is_gamechannel)
    async def _joingame(self, ctx):
        CurrentChannel = ctx.channel.name
        groups = self.bot.Settings

        if ctx.channel.name in groups["Settings"]["Groups"].keys() and ctx.author.mention in groups["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
            await ctx.respond(f"{ctx.author.name}, du bist bereits als Teilnehmer im geplanten Erinnerer.")
        elif ctx.channel.name in groups["Settings"]["Groups"].keys() and f"{ctx.author.mention}" not in groups["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
            groups["Settings"]["Groups"][f"{CurrentChannel}"]["members"].append(
                f"{ctx.author.mention}")
            await ctx.respond(f"{ctx.author.mention}, du wurdest dem Erinnerer hinzugefügt.")
            logging.info(
                f"{ctx.author} joined the meeting in {ctx.channel.name}.")
            _write_json('Settings.json', groups)
        else:
            await ctx.respond("In diesem Channel wurde noch kein Spiel geplant.")

    @commands.slash_command(name="updategame", description="Verschiebt den Erinnerer auf die gewünschte Zeit")
    @commands.check(_is_gamechannel)
    async def _movegame(self, ctx, time):
        CurrentChannel = ctx.channel.name
        groups = self.bot.Settings

        if ctx.channel.name in groups["Settings"]["Groups"].keys() and ctx.author.mention == groups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            try:
                CurrentDate = datetime.datetime.now()
                GameTime = datetime.datetime.strptime(time, "%H:%M").time()
                GameDateTime = datetime.datetime.combine(CurrentDate, GameTime)
                GameDateTimeTimestamp = GameDateTime.timestamp()
            except ValueError:
                await ctx.respond("Na na, das ist keine Uhrzeit!")
                logging.warning(
                    f"{ctx.author} entered a wrong time for the updategamecommand!")
                return

            ReminderTheme = groups["Settings"]["Groups"][f"{CurrentChannel}"]["theme"]
            groups["Settings"]["Groups"][f"{CurrentChannel}"]["time"] = GameDateTimeTimestamp
            _write_json('Settings.json', groups)
            await ctx.respond(f"Die Uhrzeit des Erinnerers für {ReminderTheme} wurde auf {time} geändert.")
            logging.info(
                f"{ctx.author} moved the meeting in {CurrentChannel} for {ReminderTheme} to {time}.")
        elif ctx.channel.name in groups["Settings"]["Groups"].keys() and ctx.author.mention != groups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            await ctx.respond("Na na, du bist nicht der Besitzer dieser Verabredung! Frag bitte den Besitzer, ob er es verschiebt!")
            logging.warning(
                f"{ctx.author} tried to move the meeting for {ReminderTheme} in {CurrentChannel} but is not the owner!")
        elif ctx.channel.name not in groups["Settings"]["Groups"].keys():
            await ctx.respond("Hier gibt es noch keine Verabredung. Starte doch eine!")

    @commands.slash_command(name="deletegame", description="Löscht den Erinnerer")
    @commands.check(_is_gamechannel)
    async def _gameremover(self, ctx):
        CurrentChannel = ctx.channel.name
        groups = self.bot.Settings
        ReminderTheme = groups["Settings"]["Groups"][f"{CurrentChannel}"]["theme"]
        if ctx.channel.name in groups["Settings"]["Groups"].keys() and ctx.author.mention == groups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            groups["Settings"]["Groups"].pop(CurrentChannel)
            _write_json('Settings.json', groups)
            await ctx.respond(f"Der Erinnerer für {ReminderTheme} in diesem Channel wurde gelöscht.")
            logging.info(
                f"{ctx.author} deleted the meeting in {CurrentChannel}.")
        elif ctx.channel.name in groups["Settings"]["Groups"].keys() and ctx.author.mention != groups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            await ctx.respond("Na na, du bist nicht der Besitzer dieses Erinners! Frag bitte den Besitzer, ob er diese löscht!")
            logging.warning(
                f"{ctx.author} tried to delete a meeting in {CurrentChannel} for {ReminderTheme} but is not the owner!")
        elif ctx.channel.name not in groups["Settings"]["Groups"].keys():
            await ctx.respond("Hier gibt es noch keinen Erinnerer. Starte doch eine!")

    @commands.slash_command(name="leavegame", description="Verlässt den aktuellen Erinnerer")
    @commands.check(_is_gamechannel)
    async def _leavegame(self, ctx):
        CurrentChannel = ctx.channel.name
        StartedGroups = self.bot.Settings
        ReminderTheme = StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["theme"]
        ReminderTime = datetime.datetime.fromtimestamp(
            StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["time"], tz=datetime.datetime.utcnow().astimezone().tzinfo)
        if ctx.channel.name in StartedGroups["Settings"]["Groups"].keys() and ctx.author.mention == StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            StartedGroups["Settings"]["Groups"].pop(CurrentChannel)
            _write_json('Settings.json', StartedGroups)
            await ctx.respond(f"{ctx.author.mention}, der Erinnerer für {ReminderTheme} um {ReminderTime:%H:%M} in diesem Channel wurde gelöscht, da du der Besitzer warst.")
            logging.info(
                f"{ctx.author} left the meeting for {ReminderTheme} in {CurrentChannel} and was the owner. Meeting deleted.")
        elif ctx.channel.name in StartedGroups["Settings"]["Groups"].keys() and ctx.author.mention in StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
            StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["members"].remove(
                ctx.author.mention)
            await ctx.respond(f"{ctx.author.mention}, du wurdest aus dem Erinnerer für {ReminderTheme} um {ReminderTime:%H:%M} entfernt.")
            logging.info(
                f"{ctx.author} removed from meeting for {ReminderTheme} in {CurrentChannel}.")
            _write_json('Settings.json', StartedGroups)
        elif ctx.channel.name in StartedGroups["Settings"]["Groups"].keys() and ctx.author.mention not in StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
            await ctx.respond(f"{ctx.author.mention}, du bist dem Erinnerer für {ReminderTheme} nicht beigetreten und wurdest daher auch nicht entfernt.")
            logging.info(
                f"{ctx.author} wanted to leave the meeting for {ReminderTheme} in {CurrentChannel}, but was not a member.")
        else:
            await ctx.respond(f"{ctx.author.mention}, hier gibt es keinen Erinnerer, den du verlassen könntest.")
            logging.info(
                f"{ctx.author} wanted to leave a meeting for {ReminderTheme} in {CurrentChannel}, but there was none.")

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
