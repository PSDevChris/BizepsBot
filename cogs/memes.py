import os
import random

import discord
from discord.ext import commands

from Main import _get_banned_users, _is_banned, datetime, logging


def RefreshMemes():
    global AllFiles
    AllFiles = []
    # Easiest way to walk was with a replace
    for MemeFolder, MemberFolder, Files in os.walk(os.getcwd() + "/memes/"):
        for FileName in Files:
            if FileName.endswith(('gif', 'jpg', 'png', 'jpeg')):
                AllFiles.append(f"{MemeFolder}/{FileName}")
    return AllFiles


class Memes(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.BannedUsers = _get_banned_users()
        RefreshMemes()

    async def cog_check(self, ctx):
        return await _is_banned(ctx)

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.slash_command(name="meme", description="Gibt ein Zufallsmeme aus, kann auch Memes adden")
    @commands.cooldown(2, 180, commands.BucketType.user)
    @commands.has_permissions(attach_files=True)
    async def _memearchiv(self, ctx, add: discord.Option(str, "Hinzufügen von Memes per add oder collect", choices=["meme"], required=False), collect: discord.Option(commands.MessageConverter, "Hinzufügen von Memes per add oder collect", required=False)):
        if add:
            LastMessages = await ctx.channel.history(limit=1).flatten()
            if LastMessages[0].author != self.bot.user:
                if os.path.exists(f"{os.getcwd() + '/memes/'}{LastMessages[0].author}") == False:
                    os.mkdir(
                        f"{os.getcwd() + '/memes/'}{LastMessages[0].author}")
                NumberOfMemes = next(
                    os.walk(f"{os.getcwd() + '/memes/'}{LastMessages[0].author}"))[2]
                NumberOfFiles = len(NumberOfMemes)
                if LastMessages[0].attachments:
                    for index, meme in enumerate(LastMessages[0].attachments):
                        if meme.filename.lower().endswith(('gif', 'jpg', 'png', 'jpeg')) and meme.size <= 8000000:
                            await meme.save(f"{os.getcwd() + '/memes/'}{LastMessages[0].author}/{NumberOfFiles + 1 + index}_{meme.filename}")
                            AllFiles.append(
                                f"{os.getcwd() + '/memes/'}{LastMessages[0].author}/{NumberOfFiles + 1 + index}_{meme.filename}")
                            await ctx.respond("Memes hinzugefügt.")
                            logging.info(
                                f"{ctx.author} has added a meme, filename was {meme.filename}.")
                        else:
                            logging.error(
                                f"ERROR: Meme was not under 8mb or not a supported format. Filename was {meme.filename}, size was {meme.size}!")
                else:
                    await ctx.respond("Bitte das Meme als Anhang einreichen.")
            else:
                await ctx.respond("Das Meme stammt von mir, das füge ich nicht nochmal hinzu.")
        elif collect:
            Message = collect
            if Message.author != self.bot.user:
                if os.path.exists(f"{os.getcwd() + '/memes/'}{Message.author}") == False:
                    os.mkdir(f"{os.getcwd() + '/memes/'}{Message.author}")
                NumberOfMemes = next(
                    os.walk(f"{os.getcwd() + '/memes/'}{Message.author}"))[2]
                NumberOfFiles = len(NumberOfMemes)
                if Message.attachments:
                    for index, meme in enumerate(Message.attachments):
                        if meme.filename.lower().endswith(('gif', 'jpg', 'png', 'jpeg')) and meme.size <= 8000000:
                            await meme.save(f"{os.getcwd() + '/memes/'}{Message.author}/{NumberOfFiles + 1 + index}_{meme.filename}")
                            await ctx.respond("Dieses spicy Meme wurde eingesammelt.", file=await meme.to_file())
                            AllFiles.append(
                                f"{os.getcwd() + '/memes/'}{Message.author}/{NumberOfFiles + 1 + index}_{meme.filename}")
                            logging.info(
                                f"{ctx.author} has collected the meme {meme.filename}.")
                        else:
                            logging.error(
                                f"ERROR: Meme was not under 8mb or not a supported format. Filename was {meme.filename}, size was {meme.size}!")
                else:
                    await ctx.respond("Bitte das Meme als Anhang einreichen.")
            else:
                await ctx.respond("Das Meme stammt von mir, das füge ich nicht nochmal hinzu.")
        else:
            if len(AllFiles) == 0:
                RefreshMemes()
            NoWednesdayMemes = list(
                filter(lambda x: 'Mittwoch' not in x, AllFiles))
            if NoWednesdayMemes == []:
                RefreshMemes()
                NoWednesdayMemes = list(
                    filter(lambda x: 'Mittwoch' not in x, AllFiles))
            RandomMeme = random.SystemRandom().choice(NoWednesdayMemes)
            AuthorOfMeme = RandomMeme.split("/")[-2].split("#")[0]
            logging.info(
                f"{ctx.author} wanted a random meme. Chosen was [{RandomMeme}].")
            await ctx.defer()
            await ctx.followup.send(f"Zufalls-Meme! Dieses Meme wurde eingereicht von {AuthorOfMeme}", file=discord.File(f"{RandomMeme}"))
            AllFiles.remove(RandomMeme)

    @commands.slash_command(name="mittwoch", description="Gibt ein Mittwochmeme aus, meine Kerle")
    @commands.cooldown(2, 180, commands.BucketType.user)
    async def _wedmeme(self, ctx, add: discord.Option(str, "Hinzufügen von Memes per add oder collect", choices=["mittwochmeme"], required=False), collect: discord.Option(commands.MessageConverter, "Hinzufügen von Memes per add oder collect", required=False)):
        await ctx.defer()
        if add:
            LastMessages = await ctx.channel.history(limit=1).flatten()
            if LastMessages[0].author != self.bot.user:
                NumberOfMemes = next(
                    os.walk(f"{os.getcwd() + '/memes/'}Mittwoch meine Kerle#"))[2]
                NumberOfFiles = len(NumberOfMemes)
                if LastMessages[0].attachments:
                    for index, meme in enumerate(LastMessages[0].attachments):
                        if meme.filename.lower().endswith(('gif', 'jpg', 'png', 'jpeg')) and meme.size <= 8000000:
                            await meme.save(f"{os.getcwd() + '/memes/'}Mittwoch meine Kerle#/{NumberOfFiles + 1 + index}_{meme.filename}")
                            AllFiles.append(
                                f"{os.getcwd() + '/memes/'}Mittwoch meine Kerle#/{NumberOfFiles + 1 + index}_{meme.filename}")
                            await ctx.followup.send("Mittwoch Memes hinzugefügt.")
                            logging.info(
                                f"{ctx.author} has added a wednesday meme. Name was {meme.filename}")
                        else:
                            logging.error(
                                f"ERROR: Meme was not under 8mb or not a supported format. Filename was {meme.filename}, size was {meme.size}!")
                else:
                    await ctx.followup.send("Bitte das Meme als Anhang einreichen.")
            else:
                await ctx.followup.send("Das Meme stammt von mir, das füge ich nicht nochmal hinzu.")
        elif collect:
            Message = collect
            if Message.author != self.bot.user:
                NumberOfMemes = next(
                    os.walk(f"{os.getcwd() + '/memes/'}Mittwoch meine Kerle#"))[2]
                NumberOfFiles = len(NumberOfMemes)
                if Message.attachments:
                    for index, meme in enumerate(Message.attachments):
                        if meme.filename.lower().endswith(('gif', 'jpg', 'png', 'jpeg')) and meme.size <= 8000000:
                            await meme.save(f"{os.getcwd() + '/memes/'}Mittwoch meine Kerle#/{NumberOfFiles + 1 + index}_{meme.filename}")
                            logging.info(
                                f"{ctx.author} has added the wednesday meme {meme.filename}.")
                            await ctx.followup.send("Folgendes Mittwoch Meme hinzugefügt:", file=await meme.to_file())
                            AllFiles.append(
                                f"{os.getcwd() + '/memes/'}Mittwoch meine Kerle#/{NumberOfFiles + 1 + index}_{meme.filename}")
                        else:
                            logging.error(
                                f"ERROR: Meme was not under 8mb or not a supported format. Filename was {meme.filename}, size was {meme.size}!")
                else:
                    await ctx.followup.send("Bitte das Meme als Anhang einreichen.")
            else:
                await ctx.followup.send("Das Meme stammt von mir, das füge ich nicht nochmal hinzu.")
        else:
            if datetime.datetime.now().isoweekday() == 3:
                WednesdayMemes = list(
                    filter(lambda x: 'Mittwoch' in x, AllFiles))
                if WednesdayMemes == []:
                    RefreshMemes()
                    WednesdayMemes = list(
                        filter(lambda x: 'Mittwoch' in x, AllFiles))
                RandomWedMeme = random.SystemRandom().choice(WednesdayMemes)
                MyDudesAdjectives = ["ehrenhaften", "hochachtungsvollen",
                                     "kerligen", "verehrten", "memigen", "standhaften", "stabilen"]
                RandomAdjective = random.SystemRandom().choice(MyDudesAdjectives)
                logging.info(
                    f"{ctx.author} wanted a wednesday meme, chosen adjective was [{RandomAdjective}], chosen meme was [{RandomWedMeme}].")
                await ctx.followup.send(f"Es ist Mittwoch, meine {RandomAdjective} Kerl*innen und \*außen!!!", file=discord.File(f"{RandomWedMeme}"))
                AllFiles.remove(RandomWedMeme)
            else:
                await ctx.followup.send("Es ist noch nicht Mittwoch, mein Kerl.", ephemeral=True)

    @_memearchiv.error
    async def _memearchiv_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuche es erneut in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam random memes!")
        else:
            logging.error(f"ERROR: {error}!")

    @_wedmeme.error
    async def _wedmeme_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuche es erneut in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam random memes!")
        else:
            logging.error(f"ERROR: {error}!")


def setup(bot):
    bot.add_cog(Memes(bot))
