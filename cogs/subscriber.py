from discord.ext import commands

from Main import _is_banned, discord, logging


class TwitchButton(discord.ui.Button):
    def __init__(self, label, customid):
        super().__init__(label=label, custom_id=customid, style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: discord.interactions.Interaction):
        await interaction.response.defer(ephemeral=True)
        creator = self.custom_id.replace("Button", "")
        user = interaction.user
        role = discord.utils.get(interaction.guild.roles, name=f"{creator} Alert")
        if role not in user.roles:
            await interaction.user.add_roles(role)
            await interaction.followup.send(f"Du wurdest der Rolle {role.name} hinzugefügt.", ephemeral=True)
            logging.info(f"{user} added himself to the alertgroup for {role.name}.")
        else:
            await interaction.user.remove_roles(role)
            await interaction.followup.send(f"Du wurdest aus der Rolle {role.name} entfernt.", ephemeral=True)
            logging.info(f"{user} removed himself from the alertgroup of {role.name}.")


class FreeStuffButton(discord.ui.Button):
    def __init__(self, label, customid):
        super().__init__(label=label, custom_id=customid, style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.interactions.Interaction):
        await interaction.response.defer(ephemeral=True)
        stuff = self.custom_id.replace("Button", "")
        user = interaction.user
        role = discord.utils.get(interaction.guild.roles, name=f"Free {stuff}Alert")  # no blank since it is not getting replaced
        if role not in user.roles:
            await interaction.user.add_roles(role)
            await interaction.followup.send(f"Du wurdest der Rolle {role.name} hinzugefügt.", ephemeral=True)
            logging.info(f"{user} added himself to the alertgroup for {role.name}.")
        else:
            await interaction.user.remove_roles(role)
            await interaction.followup.send(f"Du wurdest aus der Rolle {role.name} entfernt.", ephemeral=True)
            logging.info(f"{user} removed himself from the alertgroup of {role.name}.")


class DMFreeStuffButton(discord.ui.Button):
    def __init__(self, label, customid):
        super().__init__(label=label, custom_id=customid, style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.interactions.Interaction):
        await interaction.response.defer(ephemeral=True)
        stuff = self.custom_id.replace(" Button", "")
        user = interaction.user
        role = discord.utils.get(interaction.guild.roles, name=f"{stuff}")
        if role not in user.roles:
            await interaction.user.add_roles(role)
            await interaction.followup.send(f"Du wurdest der Rolle {role.name} hinzugefügt.", ephemeral=True)
            logging.info(f"{user} added himself to the alertgroup for {role.name}.")
        else:
            await interaction.user.remove_roles(role)
            await interaction.followup.send(f"Du wurdest aus der Rolle {role.name} entfernt.", ephemeral=True)
            logging.info(f"{user} removed himself from the alertgroup of {role.name}.")


class Subscriber(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        SubscribeUserView = discord.ui.View()
        for twitchuser in sorted(self.bot.Settings["Settings"]["TwitchUser"].keys()):
            twitchuserbutton = TwitchButton(f"{twitchuser} abonnieren", f"{twitchuser}Button")
            SubscribeUserView.add_item(twitchuserbutton)
        FreeSteamButton = FreeStuffButton("Gratis Steam-Games abonnieren", "Steam Game Button")
        FreeEpicButton = FreeStuffButton("Gratis Epic-Games abonnieren", "Epic Game Button")
        FreeGOGButton = FreeStuffButton("Gratis GOG-Games abonnieren", "GOG Game Button")
        DMSteamButton = DMFreeStuffButton("Privatnachricht bei gratis Steam Game", "DM Alert Steam Button")
        DMGOGButton = DMFreeStuffButton("Privatnachricht bei gratis GOG Game", "DM Alert GOG Button")
        DMEpicButton = DMFreeStuffButton("Privatnachricht bei gratis Epic Game", "DM Alert Epic Button")
        # FreeOWLButton = FreeStuffButton(
        # "Gratis OWL-Tokens abonnieren", f"OWL Tokens Button")
        SubscribeUserView.add_item(FreeSteamButton)
        SubscribeUserView.add_item(FreeEpicButton)
        SubscribeUserView.add_item(FreeGOGButton)
        SubscribeUserView.add_item(DMSteamButton)
        SubscribeUserView.add_item(DMGOGButton)
        SubscribeUserView.add_item(DMEpicButton)
        # SubscribeUserView.add_item(FreeOWLButton)

        await ctx.respond(view=SubscribeUserView, ephemeral=True)

    @_subscribe.error
    async def _subscribe_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam the hanscommand!")
        elif isinstance(error, discord.CheckFailure):
            await ctx.respond("Du bist gebannt und damit von der Verwendung des Bots ausgeschlossen.", ephemeral=True)
        else:
            logging.error(f"ERROR: {error}")


def setup(bot):
    bot.add_cog(Subscriber(bot))
