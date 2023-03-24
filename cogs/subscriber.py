from discord.ext import commands

from Main import _get_banned_users, _is_banned, _read_json, discord, logging


class TwitchButton(discord.ui.Button):

    def __init__(self, label, customid):
        super().__init__(label=label, custom_id=customid, style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: discord.interactions.Interaction):
        await interaction.response.defer(ephemeral=True)
        creator = self.custom_id.replace('Button', '')
        user = interaction.user
        role = discord.utils.get(
            interaction.guild.roles, name=f"{creator} Alert")
        if role not in user.roles:
            await interaction.user.add_roles(role)
            await interaction.followup.send(f"Du wurdest der Rolle {role.name} hinzugefügt.", ephemeral=True)
            logging.info(
                f"{user} added himself to the alertgroup for {role.name}.")
        else:
            await interaction.user.remove_roles(role)
            await interaction.followup.send(f"Du wurdest aus der Rolle {role.name} entfernt.", ephemeral=True)
            logging.info(
                f"{user} removed himself from the alertgroup of {role.name}.")


class Subscriber(commands.Cog):

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
    @commands.slash_command(name="subscribe", description="Füge dich Benachrichtigungsgruppen hinzu!", brief="Füge dich Benachrichtigungsgruppen hinzu")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _subscribe(self, ctx):

        TwitchUserView = discord.ui.View()
        Settings = _read_json('Settings.json')
        for twitchuser in sorted(Settings['Settings']['TwitchUser'].keys()):
            twitchuserbutton = TwitchButton(
                f"{twitchuser} abonnieren", f"{twitchuser}Button")
            TwitchUserView.add_item(twitchuserbutton)

        await ctx.respond(view=TwitchUserView, ephemeral=True)


def setup(bot):
    bot.add_cog(Subscriber(bot))
