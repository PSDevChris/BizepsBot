from discord.ext import commands

from Main import _get_banned_users, _is_banned, aiohttp, datetime, discord


class xkcd(commands.Cog):

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
    @commands.slash_command(name="xkcd", description="Postet das aktuelle xkcd Comic", brief="Postet das aktuelle xkcd Comic")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def _show_xkcd(self, ctx):
        XkcdURL = "https://xkcd.com/info.0.json"
        async with aiohttp.ClientSession() as XkcdSession:
            async with XkcdSession.get(XkcdURL) as RequestToXkcd:
                if RequestToXkcd.status == 200:
                    JSONFromXkcd = await RequestToXkcd.json()
                    XkcdEmbed = discord.Embed(title=f'Aktuelles xkcd Comic: {JSONFromXkcd["safe_title"]}!\r\n', colour=discord.Colour(
                        0xFFFFFF), description=f'{JSONFromXkcd["alt"]}', timestamp=datetime.datetime.utcnow())
                    XkcdEmbed.set_image(
                        url=f'{JSONFromXkcd["img"]}')
                    XkcdEmbed.set_footer(text="Bizeps_Bot")
                    await ctx.respond("", embed=XkcdEmbed)


def setup(bot):
    bot.add_cog(xkcd(bot))
