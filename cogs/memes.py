import os
import random

import aiohttp
import discord
from discord.ext import commands

from Main import _get_banned_users, _is_banned, datetime, logging


def RefreshMemes():
    global AllFiles
    AllFiles = []
    # Easiest way to walk was with a replace
    for MemeFolder, _MemberFolder, Files in os.walk(os.getcwd() + "/memes/"):
        for FileName in Files:
            if FileName.endswith(("gif", "jpg", "png", "jpeg", "webp")):
                AllFiles.append(f"{MemeFolder}/{FileName}")
    logging.info("Refreshed Memelist.")
    return AllFiles


def _find_url_in_string(Message: str):
    split_message = Message.split()
    found_url = []
    for split in split_message:
        if split.startswith(("http://", "https://")):
            found_url.append(split)
    return found_url


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
    async def _memearchiv(
        self,
        ctx,
        add: discord.Option(str, "Hinzufügen des zuletzt geposteten Memes ", choices=["meme"], required=False),
        collect: discord.Option(commands.MessageConverter, "Hinzufügen von Memes per collect und Message ID", required=False),
    ):
        await ctx.defer()
        if add:
            LastMessages = await ctx.channel.history(limit=2).flatten()
            if LastMessages[1].author != self.bot.user:
                if LastMessages[1].author != ctx.author:
                    if os.path.exists(f"{os.getcwd() + '/memes/'}{LastMessages[1].author}") is False:
                        os.mkdir(f"{os.getcwd() + '/memes/'}{LastMessages[1].author}")
                    NumberOfMemes = next(os.walk(f"{os.getcwd() + '/memes/'}{LastMessages[1].author}"))[2]
                    NumberOfFiles = len(NumberOfMemes)
                    if LastMessages[1].attachments:
                        for index, meme in enumerate(LastMessages[1].attachments):
                            if meme.filename.lower().endswith(("gif", "jpg", "png", "jpeg", "webp")) and meme.size <= 8000000:
                                await meme.save(f"{os.getcwd() + '/memes/'}{LastMessages[1].author}/{NumberOfFiles + 1 + index}_{meme.filename}")
                                AllFiles.append(f"{os.getcwd() + '/memes/'}{LastMessages[1].author}/{NumberOfFiles + 1 + index}_{meme.filename}")
                                await ctx.followup.send("Meme hinzugefügt.")
                                logging.info(f"{ctx.author} has added a meme, filename was [{meme.filename}].")
                            else:
                                logging.error(f"ERROR: Meme was not under 8mb or not a supported format. Filename was [{meme.filename}], size was [{meme.size}]!")
                    else:
                        found_urls = _find_url_in_string(LastMessages[1].content)
                        if found_urls:
                            async with aiohttp.ClientSession() as MemeSession:
                                for index, url in enumerate(found_urls):
                                    async with MemeSession.get(url=url) as meme_img_req:
                                        if meme_img_req.headers["content-type"] in ["image/gif", "image/png", "image/jpeg", "image/webp"]:
                                            if int(meme_img_req.headers["content-length"]) > 8000000:
                                                await ctx.followup.send("Das Meme ist über 8MB groß und wurde daher nicht gespeichert.")
                                            else:
                                                meme_bimage = await meme_img_req.read()
                                                dl_filename = url.split("/")[-1]
                                                file_ending = meme_img_req.headers["content-type"].split("/")[-1]
                                                with open(f"{os.getcwd() + '/memes/'}{LastMessages[1].author}/{NumberOfFiles + 1 + index}_{dl_filename}.{file_ending}", "wb") as write_file:
                                                    write_file.write(meme_bimage)
                                                await ctx.followup.send("Meme hinzugefügt.")
                                                logging.info(f"Added Meme {LastMessages[1].author}/{NumberOfFiles + 1 + index}_{dl_filename}.{file_ending} to the Gallery.")
                                        else:
                                            await ctx.followup.send("Es wurde eine URL gefunden, diese liefert aber kein Bild zurück. Bitte das Meme als Anhang einreichen.")
                        else:
                            await ctx.followup.send(
                                "Es wurde weder ein Anhang, noch eine Bild-URL gefunden. Bitte das Meme erneut einreichen in passendem Bildformat (jpg, gif, png, webp) oder als Anhang."
                            )
                else:
                    await ctx.followup.send("Das Meme stammt von dir, jemand anderes muss es in die Sammlung aufnehmen.")
            else:
                await ctx.followup.send("Das Meme stammt von mir, das füge ich nicht nochmal hinzu.")
        elif collect:
            Message = collect
            if Message.author != self.bot.user:
                if Message.author != ctx.author:
                    if os.path.exists(f"{os.getcwd() + '/memes/'}{Message.author}") is False:
                        os.mkdir(f"{os.getcwd() + '/memes/'}{Message.author}")
                    NumberOfMemes = next(os.walk(f"{os.getcwd() + '/memes/'}{Message.author}"))[2]
                    NumberOfFiles = len(NumberOfMemes)
                    if Message.attachments:
                        for index, meme in enumerate(Message.attachments):
                            if meme.filename.lower().endswith(("gif", "jpg", "png", "jpeg", "webp")) and meme.size <= 8000000:
                                await meme.save(f"{os.getcwd() + '/memes/'}{Message.author}/{NumberOfFiles + 1 + index}_{meme.filename}")
                                await ctx.followup.send("Dieses spicy Meme wurde eingesammelt.", file=await meme.to_file())
                                AllFiles.append(f"{os.getcwd() + '/memes/'}{Message.author}/{NumberOfFiles + 1 + index}_{meme.filename}")
                                logging.info(f"{ctx.author} has collected the meme [{meme.filename}].")
                            else:
                                logging.error(f"ERROR: Meme was not under 8mb or not a supported format. Filename was [{meme.filename}], size was [{meme.size}]!")
                    else:
                        found_urls = _find_url_in_string(Message.content)
                        if found_urls:
                            async with aiohttp.ClientSession() as MemeSession:
                                for index, url in enumerate(found_urls):
                                    async with MemeSession.get(url=url) as meme_img_req:
                                        if meme_img_req.headers["content-type"] in ["image/gif", "image/png", "image/jpeg", "image/webp"]:
                                            if int(meme_img_req.headers["content-length"]) > 8000000:
                                                await ctx.followup.send("Das Meme ist über 8MB groß und wurde daher nicht gespeichert.")
                                            else:
                                                meme_bimage = await meme_img_req.read()
                                                dl_filename = url.split("/")[-1]
                                                file_ending = meme_img_req.headers["content-type"].split("/")[-1]
                                                with open(f"{os.getcwd() + '/memes/'}{Message.author}/{NumberOfFiles + 1 + index}_{dl_filename}.{file_ending}", "wb") as write_file:
                                                    write_file.write(meme_bimage)
                                                    meme_filename = write_file.name
                                                    await ctx.followup.send("Meme hinzugefügt.", file=discord.File(meme_filename))
                                                    logging.info(f"Added Meme {Message.author}/{NumberOfFiles + 1 + index}_{dl_filename}.{file_ending} to the Gallery.")
                                        else:
                                            await ctx.followup.send("Es wurde eine URL gefunden, diese liefert aber kein Bild zurück. Bitte das Meme als Anhang einreichen.")
                        else:
                            await ctx.followup.send(
                                "Es wurde weder ein Anhang, noch eine Bild-URL gefunden. Bitte das Meme erneut einreichen in passendem Bildformat (jpg, gif, png, webp) oder als Anhang."
                            )
                else:
                    await ctx.followup.send("Das Meme stammt von dir, jemand anderes muss es in die Sammlung aufnehmen.")
            else:
                await ctx.followup.send("Das Meme stammt von mir, das füge ich nicht nochmal hinzu.")
        else:
            if len(AllFiles) == 0:
                RefreshMemes()
            NoWednesdayMemes = list(filter(lambda x: "Mittwoch" not in x, AllFiles))
            if NoWednesdayMemes == []:
                RefreshMemes()
            NoWednesdayMemes = list(filter(lambda x: "Mittwoch" not in x, AllFiles))
            RandomMeme = random.SystemRandom().choice(NoWednesdayMemes)
            AuthorOfMeme = RandomMeme.split("/")[-2].split("#")[0]
            logging.info(f"{ctx.author} wanted a random meme. Chosen was [{RandomMeme}].")
            await ctx.followup.send(f"Zufalls-Meme! Dieses Meme wurde eingereicht von {AuthorOfMeme}", file=discord.File(f"{RandomMeme}"))
            AllFiles.remove(RandomMeme)

    @commands.slash_command(name="mittwoch", description="Gibt ein Mittwochmeme aus, meine Kerle")
    @commands.cooldown(2, 180, commands.BucketType.user)
    async def _wedmeme(
        self,
        ctx,
        add: discord.Option(str, "Hinzufügen des zuletzt geposteten Mittwochmemes per add", choices=["mittwochmeme"], required=False),
        collect: discord.Option(commands.MessageConverter, "Hinzufügen eines Mittwochmemes per collect und Message ID", required=False),
    ):
        if add:
            await ctx.defer()
            LastMessages = await ctx.channel.history(limit=2).flatten()
            if LastMessages[1].author != self.bot.user:
                if LastMessages[1].author != ctx.author:
                    NumberOfMemes = next(os.walk(f"{os.getcwd() + '/memes/'}Mittwoch meine Kerle#"))[2]
                    NumberOfFiles = len(NumberOfMemes)
                    if LastMessages[1].attachments:
                        for index, meme in enumerate(LastMessages[1].attachments):
                            if meme.filename.lower().endswith(("gif", "jpg", "png", "jpeg", "webp")) and meme.size <= 8000000:
                                await meme.save(f"{os.getcwd() + '/memes/'}Mittwoch meine Kerle#/{NumberOfFiles + 1 + index}_{meme.filename}")
                                AllFiles.append(f"{os.getcwd() + '/memes/'}Mittwoch meine Kerle#/{NumberOfFiles + 1 + index}_{meme.filename}")
                                await ctx.followup.send("Mittwoch Memes hinzugefügt.")
                                logging.info(f"{ctx.author} has added a wednesday meme. Name was [{meme.filename}]")
                            else:
                                logging.error(f"ERROR: Meme was not under 8mb or not a supported format. Filename was [{meme.filename}], size was [{meme.size}]!")
                    else:
                        found_urls = _find_url_in_string(LastMessages[1].content)
                        if found_urls:
                            async with aiohttp.ClientSession() as WedMemeSession:
                                for index, url in enumerate(found_urls):
                                    async with WedMemeSession.get(url=url) as wed_meme_img_req:
                                        if wed_meme_img_req.headers["content-type"] in ["image/gif", "image/png", "image/jpeg", "image/webp"]:
                                            if int(wed_meme_img_req.headers["content-length"]) > 8000000:
                                                await ctx.followup.send("Das Mittwoch Meme ist über 8MB groß und wurde daher nicht gespeichert.")
                                            else:
                                                wed_meme_bimage = await wed_meme_img_req.read()
                                                dl_filename = url.split("/")[-1]
                                                file_ending = wed_meme_img_req.headers["content-type"].split("/")[-1]
                                                with open(f"{os.getcwd() + '/memes/'}Mittwoch meine Kerle#/{NumberOfFiles + 1 + index}_{dl_filename}.{file_ending}", "wb") as write_file:
                                                    write_file.write(wed_meme_bimage)
                                                    await ctx.followup.send("Meme hinzugefügt.")
                                                    logging.info(f"Added Wednesday Meme /Mittwoch meine Kerle#/{NumberOfFiles + 1 + index}_{dl_filename}.{file_ending} to the Gallery.")

                                        else:
                                            await ctx.followup.send("Es wurde eine URL gefunden, diese liefert aber kein Bild zurück. Bitte das Meme als Anhang einreichen.")
                        else:
                            await ctx.followup.send(
                                "Es wurde weder ein Anhang, noch eine Bild-URL gefunden. Bitte das Meme erneut einreichen in passendem Bildformat (jpg, gif, png, webp) oder als Anhang."
                            )
                else:
                    await ctx.followup.send("Das Mittwoch-Meme stammt von dir, jemand anderes muss es in die Sammlung aufnehmen.")
            else:
                await ctx.followup.send("Das Meme stammt von mir, das füge ich nicht nochmal hinzu.")
        elif collect:
            await ctx.defer()
            Message = collect
            if Message.author != self.bot.user:
                if Message.author != ctx.author:
                    NumberOfMemes = next(os.walk(f"{os.getcwd() + '/memes/'}Mittwoch meine Kerle#"))[2]
                    NumberOfFiles = len(NumberOfMemes)
                    if Message.attachments:
                        for index, meme in enumerate(Message.attachments):
                            if meme.filename.lower().endswith(("gif", "jpg", "png", "jpeg", "webp")) and meme.size <= 8000000:
                                await meme.save(f"{os.getcwd() + '/memes/'}Mittwoch meine Kerle#/{NumberOfFiles + 1 + index}_{meme.filename}")
                                logging.info(f"{ctx.author} has added the wednesday meme {meme.filename}.")
                                await ctx.followup.send("Folgendes Mittwoch Meme hinzugefügt:", file=await meme.to_file())
                                AllFiles.append(f"{os.getcwd() + '/memes/'}Mittwoch meine Kerle#/{NumberOfFiles + 1 + index}_{meme.filename}")
                            else:
                                logging.error(f"ERROR: Meme was not under 8mb or not a supported format. Filename was [{meme.filename}], size was [{meme.size}]!")
                    else:
                        found_urls = _find_url_in_string(Message.content)
                        if found_urls:
                            async with aiohttp.ClientSession() as WedMemeSession:
                                for index, url in enumerate(found_urls):
                                    async with WedMemeSession.get(url=url) as wed_meme_img_req:
                                        if wed_meme_img_req.headers["content-type"] in ["image/gif", "image/png", "image/jpeg", "image/webp"]:
                                            if int(wed_meme_img_req.headers["content-length"]) > 8000000:
                                                await ctx.followup.send("Das Mittwoch Meme ist über 8MB groß und wurde daher nicht gespeichert.")
                                            else:
                                                wed_meme_bimage = await wed_meme_img_req.read()
                                                dl_filename = url.split("/")[-1]
                                                file_ending = wed_meme_img_req.headers["content-type"].split("/")[-1]
                                                with open(f"{os.getcwd() + '/memes/'}Mittwoch meine Kerle#/{NumberOfFiles + 1 + index}_{dl_filename}.{file_ending}", "wb") as write_file:
                                                    write_file.write(wed_meme_bimage)
                                                    wed_meme_filename = write_file.name
                                                    await ctx.followup.send("Meme hinzugefügt.", file=discord.File(wed_meme_filename))
                                                    logging.info(f"Added Mittwoch Meme /Mittwoch meine Kerle#/{NumberOfFiles + 1 + index}_{dl_filename}.{file_ending} to the Gallery.")
                                        else:
                                            await ctx.followup.send("Es wurde eine URL gefunden, diese liefert aber kein Bild zurück. Bitte das Meme als Anhang einreichen.")
                        else:
                            await ctx.followup.send(
                                "Es wurde weder ein Anhang, noch eine Bild-URL gefunden. Bitte das Meme erneut einreichen in passendem Bildformat (jpg, gif, png, webp) oder als Anhang."
                            )
                else:
                    await ctx.followup.send("Das Mittwoch-Meme stammt von dir, jemand anderes muss es in die Sammlung aufnehmen.")
            else:
                await ctx.followup.send("Das Meme stammt von mir, das füge ich nicht nochmal hinzu.")
        else:
            if datetime.datetime.now().isoweekday() == 3:
                await ctx.defer()
                WednesdayMemes = list(filter(lambda x: "Mittwoch" in x, AllFiles))
                if WednesdayMemes == []:
                    RefreshMemes()
                    WednesdayMemes = list(filter(lambda x: "Mittwoch" in x, AllFiles))
                RandomWedMeme = random.SystemRandom().choice(WednesdayMemes)
                MyDudesAdjectives = ["ehrenhaften", "hochachtungsvollen", "kerligen", "verehrten", "memigen", "standhaften", "stabilen", "froschigen"]
                RandomAdjective = random.SystemRandom().choice(MyDudesAdjectives)
                logging.info(f"{ctx.author} wanted a wednesday meme, chosen adjective was [{RandomAdjective}], chosen meme was [{RandomWedMeme}].")
                await ctx.followup.send(f"Es ist Mittwoch, meine {RandomAdjective} Kerl*innen und \*außen!!!", file=discord.File(f"{RandomWedMeme}"))
                AllFiles.remove(RandomWedMeme)
            else:
                await ctx.defer(ephemeral=True)
                await ctx.followup.send("Es ist noch nicht Mittwoch, mein Kerl.")

    @_memearchiv.error
    async def _memearchiv_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuche es erneut in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam random memes!")
        elif isinstance(error, commands.MessageNotFound):
            await ctx.respond("Die Nachricht mit dem Meme konnte nicht gefunden werden.")
        else:
            logging.error(f"ERROR: {error}!")

    @_wedmeme.error
    async def _wedmeme_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuche es erneut in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam random memes!")
        elif isinstance(error, commands.MessageNotFound):
            await ctx.respond("Die Nachricht mit dem Meme konnte nicht gefunden werden.")
        else:
            logging.error(f"ERROR: {error}!")


def setup(bot):
    bot.add_cog(Memes(bot))
