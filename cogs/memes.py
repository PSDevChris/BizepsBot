import os
import random
from typing import Tuple

import aiohttp
import discord
from discord.ext import commands

from Main import _is_banned, datetime, logging

MAX_DISCORD_FILE_SIZE = 8_000_000


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Memes(bot))


def _fetch_urls_from_message(Message: discord.Message) -> list[str]:
    return [split for split in Message.content.split() if split.startswith(("http://", "https://"))]


class Memes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.Memes = []
        self.Mittwoch = []

        self.RefreshMemes()

    async def cog_check(self, ctx):
        return await _is_banned(ctx)

    def RefreshMemes(self):
        # Easiest way to walk was with a replace
        for MemeFolder, _, Files in os.walk(os.getcwd() + "/memes/"):
            ListOfMemes = self.Mittwoch if MemeFolder.split("/")[-1] == "Mittwoch meine Kerle#" else self.Memes

            for FileName in Files:
                if FileName.endswith(("gif", "jpg", "png", "jpeg", "webp")):
                    ListOfMemes.append(f"{MemeFolder}/{FileName}")

        random.shuffle(self.Memes)
        random.shuffle(self.Mittwoch)
        logging.info("Refreshed Memelist.")

    async def GetMeme(self, *, Mittwoch: bool = False) -> Tuple[str, str]:
        ListOfMemes = self.Memes if not Mittwoch else self.Mittwoch

        RandomMeme = ListOfMemes.pop()
        AuthorOfMeme = RandomMeme.split("/")[-2].split(" ")[0]

        return RandomMeme, AuthorOfMeme

    async def AddMeme(self, ctx, Message: discord.Message, *, Mittwoch: bool = False) -> None:
        Author = Message.author

        if Author == self.bot.user:
            await ctx.respond("Das Meme stammt von mir, das füge ich nicht nochmal hinzu.")
            return

        if Author == ctx.author:
            await ctx.respond("Das Meme stammt von dir, jemand anderes muss es in die Sammlung aufnehmen.")
            return

        AuthorName = str(Author) if not Mittwoch else "Mittwoch meine Kerle#"
        ListOfMemes = self.Mittwoch if Mittwoch else self.Memes

        AuthorPath = f"{os.getcwd()}/memes/{AuthorName}"

        if not os.path.exists(AuthorPath):
            os.mkdir(AuthorPath)

        NumberOfFiles = len(next(os.walk(AuthorPath))[2])

        if Message.attachments:
            for index, meme in enumerate(Message.attachments):
                if not meme.filename.lower().endswith(("gif", "jpg", "png", "jpeg", "webp")) and meme.size > MAX_DISCORD_FILE_SIZE:
                    logging.error(f"ERROR: Meme was not under 8mb or not a supported format. Filename was [{meme.filename}], size was [{meme.size}]!")
                    continue

                FilePath = f"{AuthorPath}/{NumberOfFiles + 1 + index}_{meme.filename}"

                await meme.save(FilePath)
                ListOfMemes.append(FilePath)

                await ctx.respond(f"Meme {meme.filename} hinzugefügt.")

                random.shuffle(ListOfMemes)

                logging.info(f"{ctx.author} has added a meme, filename was [{meme.filename}].")
        else:
            found_urls = _fetch_urls_from_message(Message)

            if not found_urls:
                await ctx.respond("Es wurde weder ein Anhang, noch eine Bild-URL gefunden. Bitte das Meme erneut einreichen in passendem Bildformat (jpg, gif, png, webp) oder als Anhang.")
                return

            async with aiohttp.ClientSession() as MemeSession:
                for index, url in enumerate(found_urls):
                    async with MemeSession.get(url=url) as meme_img_req:
                        if meme_img_req.headers["content-type"] not in ["image/gif", "image/png", "image/jpeg", "image/webp"]:
                            await ctx.respond("Es wurde eine URL gefunden, diese liefert aber kein Bild zurück. Bitte das Meme als Anhang einreichen.")
                            continue

                        if int(meme_img_req.headers["content-length"]) > MAX_DISCORD_FILE_SIZE:
                            await ctx.respond("Das Meme ist über 8MB groß und wurde daher nicht gespeichert.")
                            continue

                        meme_bimage = await meme_img_req.read()
                        dl_filename = url.split("/")[-1]
                        file_ending = meme_img_req.headers["content-type"].split("/")[-1]

                        FilePath = f"{AuthorPath}/{NumberOfFiles + 1 + index}_{dl_filename}.{file_ending}"

                        with open(FilePath, "wb") as write_file:
                            write_file.write(meme_bimage)

                        ListOfMemes.append(FilePath)

                        await ctx.respond(f"Meme {dl_filename}.{file_ending} hinzugefügt.")

                        random.shuffle(ListOfMemes)

                        logging.info(f"[{ctx.author}] added Meme {FilePath} to the Gallery.")

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
        if add:
            LastMessage = await ctx.channel.history(limit=2).flatten()
            LastMessage = LastMessage[0]  # Quick Fix, needs to be investigated
            await self.AddMeme(ctx, LastMessage)
        elif collect:
            await self.AddMeme(ctx, collect)
        else:
            if not self.Memes:
                await ctx.defer()
                self.RefreshMemes()

            RandomMeme, AuthorOfMeme = await self.GetMeme()

            logging.info(f"{ctx.author} wanted a random meme. Chosen was [{RandomMeme}].")
            await ctx.respond(f"Zufalls-Meme! Dieses Meme wurde eingereicht von {AuthorOfMeme}", file=discord.File(f"{RandomMeme}"))

    @commands.slash_command(name="mittwoch", description="Gibt ein Mittwochmeme aus, meine Kerle")
    @commands.cooldown(2, 180, commands.BucketType.user)
    async def _wedmeme(
        self,
        ctx,
        add: discord.Option(str, "Hinzufügen des zuletzt geposteten Mittwochmemes per add", choices=["mittwochmeme"], required=False),
        collect: discord.Option(commands.MessageConverter, "Hinzufügen eines Mittwochmemes per collect und Message ID", required=False),
    ):
        if add:
            LastMessage = await ctx.channel.history(limit=2).flatten()
            LastMessage = LastMessage[0]
            await self.AddMeme(ctx, LastMessage, Mittwoch=True)
        elif collect:
            await self.AddMeme(ctx, collect, Mittwoch=True)
        else:
            if datetime.datetime.now().isoweekday() != 3:
                await ctx.respond("Es ist noch nicht Mittwoch, mein Kerl.", ephemeral=True)
                return

            if not self.Mittwoch:
                await ctx.defer()
                self.RefreshMemes()

            RandomWedMeme, _ = await self.GetMeme(Mittwoch=True)
            MyDudesAdjectives = ["ehrenhaften", "hochachtungsvollen", "kerligen", "verehrten", "memigen", "standhaften", "stabilen", "froschigen", "prähistorischen"]
            RandomAdjective = random.SystemRandom().choice(MyDudesAdjectives)
            logging.info(f"[{ctx.author}] wanted a wednesday meme, chosen adjective was [{RandomAdjective}], chosen meme was [{RandomWedMeme}].")
            await ctx.respond(f"Es ist Mittwoch, meine {RandomAdjective} Kerl*innen und \*außen!!!", file=discord.File(f"{RandomWedMeme}"))

    @_memearchiv.error
    async def _memearchiv_error(self, ctx, error: discord.DiscordException) -> None:
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuche es erneut in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"[{ctx.author}] wanted to spam random memes!")
        elif isinstance(error, commands.MessageNotFound):
            await ctx.respond("Die Nachricht mit dem Meme konnte nicht gefunden werden.")
        else:
            logging.error(f"ERROR: {error}!")

    @_wedmeme.error
    async def _wedmeme_error(self, ctx, error: discord.DiscordException) -> None:
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuche es erneut in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam random memes!")
        elif isinstance(error, commands.MessageNotFound):
            await ctx.respond("Die Nachricht mit dem Meme konnte nicht gefunden werden.")
        else:
            logging.error(f"ERROR: {error}!")
