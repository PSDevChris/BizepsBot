import time
from datetime import datetime, timedelta, timezone
import json
import os
import random
import logging
import discord
from discord.ext import commands, tasks
from dateutil import parser
import requests
from requests.utils import quote
from bs4 import BeautifulSoup
import paramiko
import uwuify
import pandas as pd

logging.getLogger("discord").setLevel(logging.WARNING)
logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO, handlers=[logging.FileHandler(f'./logs/{datetime.now().date()}_bot.log'),
                                                                                      logging.StreamHandler()])

# To show the whole table, currently unused
# pd.set_option('display.max_rows', None)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=('!'), intents=intents)

### Functions ###


def RequestTwitchToken():
    """
    Beantragt ein neues Twitch Token zur Authentifizierung.
    """
    global TWITCH_TOKEN, TWITCH_TOKEN_EXPIRES

    rTwitchTokenData = requests.post('https://id.twitch.tv/oauth2/token', data={
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'grant_type': 'client_credentials'
    })

    TWITCHTOKENDATA = json.loads(rTwitchTokenData.content)
    TWITCH_TOKEN = TWITCHTOKENDATA['access_token']
    TWITCH_TOKEN_EXPIRES = datetime.timestamp(
        datetime.now()) + TWITCHTOKENDATA['expires_in']

    with open('TOKEN.json') as TokenJsonRead:
        data = json.load(TokenJsonRead)
        data['TWITCH_TOKEN'] = TWITCH_TOKEN
        data['TWITCH_TOKEN_EXPIRES'] = TWITCH_TOKEN_EXPIRES
    with open('TOKEN.json', 'w') as write_file:
        json.dump(data, write_file)
    logging.info("New Twitch Token requested.")


def _read_json(FileName):
    with open(f'{FileName}', 'r', encoding='utf-8') as JsonRead:
        return json.load(JsonRead)


def _write_json(FileName, Content):
    with open(f'{FileName}', 'w', encoding='utf-8') as JsonWrite:
        json.dump(Content, JsonWrite, indent=4)


def RefreshMemes():
    global AllFiles
    AllFiles = []
    for MemeFolder, MemberFolder, Files in os.walk("memes/"):
        for FileName in Files:
            if FileName.endswith(('gif', 'jpg', 'png', 'jpeg')):
                AllFiles.append(f"{MemeFolder}/{FileName}")
    return AllFiles


def RefreshJokes():
    global DotoJokes
    DotoJokesJSON = _read_json('Settings.json')
    DotoJokes = list(DotoJokesJSON['Settings']['DotoJokes']['Jokes'])
    return DotoJokes

### Permission Checks ###


def _is_owchannel(ctx):
    return ctx.message.channel.id == 554390037811167363


def _is_nouwuchannel(ctx):
    return ctx.message.channel.category_id != 539547423782207488 and ctx.message.channel.id != 539549544585756693


def _is_gamechannel(ctx):
    if isinstance(ctx.channel, discord.channel.DMChannel):
        return False
    else:
        return ctx.message.channel.category_id == 539553136222666792


def _get_banned_users():
    global BannedUsers
    BannedUsers = _read_json('Settings.json')['Settings']['BannedUsers']
    return BannedUsers


def _is_banned(ctx: commands.context.Context, BannedUsers):
    if str(ctx.author) in BannedUsers:
        logging.info(
            f"User {ctx.author} wanted to use a command but is banned.")
    return str(ctx.author) not in BannedUsers


def _is_zuggi(ctx):
    return ctx.author.id == 232561052573892608

### Commands and Cogs Section ###


class Counter(commands.Cog, name="Counter"):
    """
    Die Klasse die alle Counter enthält und diese erhöht oder anzeigt,
    die Counter werden in einem JSON File abgelegt und gespeichert.
    """

    async def cog_check(self, ctx):
        return _is_banned(ctx, BannedUsers)

    @commands.group(name="pun",  aliases=["Pun", "salz", "Salz", "mobbing", "Mobbing", "Hasssprech", "hasssprech", "Leak", "leak", "Schnenko", "schnenko", "Schnenk", "schnenk", "lieferando", "Lieferando", "Pipi", "pipi"], invoke_without_command=True, brief="Erhöht diverse Counter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _counter(self, ctx):
        IncNum = 1
        match (ctx.invoked_with):
            case ("Pun" | "pun"):
                InvokedVar = "Puns"
                ReplyTxt = "Es wurde bereits ###REPLACE### Mal ein Gagfeuerwerk gezündet!"
            case ("Salz" | "salz"):
                InvokedVar = "Salz"
                ReplyTxt = "Man konnte sich schon ###REPLACE### Mal nicht beherrschen! Böse Salzstreuer hier!<:salt:826091230156161045>"
            case ("Leak" | "leak"):
                InvokedVar = "Leak"
                ReplyTxt = "Da hat wohl jemand nicht aufgepasst... Es wurde bereits ###REPLACE### Mal geleakt! Obacht!"
            case ("Mobbing" | "mobbing" | "Hasssprech" | "hasssprech"):
                InvokedVar = "Mobbing"
                ReplyTxt = "Das ist Hasssprech! ###REPLACE### Mal wurde schon Hasssprech betrieben! Pfui!"
            case ("Pipi" | "pipi"):
                InvokedVar = "Pipi"
                ReplyTxt = "Dotas Babyblase hat ihn schon ###REPLACE### Mal auf das stille Örtchen getrieben!"
            case ("Schnenko" | "schnenko" | "Schnenk" | "schnenk" | "lieferando" | "Lieferando"):
                InvokedVar = "Lieferando"
                IncNum = 20
                ReplyTxt = "Schnenko hat dieses Jahr bereits für ###REPLACE###€ bei Lieferando bestellt. Ein starkes Zeichen für die Wirtschaft!"
            case _:
                await ctx.send("Dieser Counter konnte nicht gefunden werden.")
                return

        data = _read_json('Settings.json')
        data['Settings']['Counter'][f'{InvokedVar}'] = data['Settings']['Counter'][f'{InvokedVar}'] + IncNum
        NewResult = data['Settings']['Counter'][f'{InvokedVar}']
        _write_json('Settings.json', data)
        await ctx.send(ReplyTxt.replace("###REPLACE###", f"{NewResult}"))

    @_counter.command(name="show", aliases=["sh", "-s", "Show"], brief="Zeigt den aktuellen Counter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _show_counter(self, ctx):
        match (ctx.invoked_parents[0]):
            case ("Pun" | "pun"):
                InvokedVar = "Puns"
                ReplyTxt = "Es gab bereits ###REPLACE### Gagfeuerwerke im Discord!"
            case ("Salz" | "Salz"):
                InvokedVar = "Salz"
                ReplyTxt = "Bisher wurden ###REPLACE### Salzstreuer geleert!<:salt:826091230156161045>"
            case ("Leak" | "leak"):
                InvokedVar = "Leak"
                ReplyTxt = "Bis dato wurden ###REPLACE### Mal sensible Informationen geleakt! Obacht!"
            case ("Mobbing" | "mobbing" | "Hasssprech" | "hasssprech"):
                InvokedVar = "Mobbing"
                ReplyTxt = "Bereits ###REPLACE### Mal wurde Hasssprech betrieben! Warum so toxisch?"
            case ("Pipi" | "pipi"):
                InvokedVar = "Pipi"
                ReplyTxt = "Doto hat bereits ###REPLACE### Mal den Stream pausiert um das WC aufzusuchen!"
            case ("Schnenko" | "schnenko" | "Schnenk" | "schnenk" | "lieferando" | "Lieferando"):
                InvokedVar = "Lieferando"
                ReplyTxt = "Aktuell hat Schnenko ###REPLACE###€ Umsatz bei Lieferando generiert, Investoren können sich freuen!"
            case _:
                await ctx.send("Dieser Counter konnte nicht gefunden werden.")
                return
        data = _read_json('Settings.json')
        await ctx.send(ReplyTxt.replace("###REPLACE###", f"{data['Settings']['Counter'][f'{InvokedVar}']}"))

    @commands.command(name="Dedge", aliases=["dedge", "splatoon3", "Splatoon3", "Splatoon3FuerDedge", "splatoon3fuerdedge"], brief="Er wird mitspielen!")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def _sp3dedge(self, ctx):
        StreamLabsURL = f"https://streamlabs.com/api/v5/donation-goal/data/?token={STREAMLABS_TOKEN}"
        StreamLabsRequest = requests.get(StreamLabsURL)

        if StreamLabsRequest.status_code == 200:
            StreamLabsData = json.loads(StreamLabsRequest.content)['data']
            await ctx.send(f"Es wurden bereits {StreamLabsData['amount']['current']}€ von {StreamLabsData['amount']['target']}€ gesammelt, damit Dedge mit uns Splatoon 3 spielt!")

    @_counter.error
    async def _counter_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Dieser Befehl ist noch im Cooldown.")
            logging.warning(
                f"{ctx.author} wanted to raise a counter fast!")


class Fun(commands.Cog, name="Schabernack"):
    """
    Die Klasse für Spaßfunktionen, diverse Textausgaben, eine Funktion um Bilder in die Memegallery zu speichern,
    sie anzuzeigen und eine Textreplace Funktion um Texte zu UwUen wird alles hier abgehandelt.
    """

    async def cog_check(self, ctx):
        return _is_banned(ctx, BannedUsers)

    @commands.command(name="Pub", aliases=["pub"], brief="Typos...")
    async def _pubtypo(self, ctx):
        await ctx.send(f"Das Discord Pub ist geschlossen, {ctx.author.name}! Du meintest wohl !pun?")

    @commands.command(name="nein", aliases=["Nein", "NEIN"], brief="Nein.")
    @commands.check(_is_zuggi)
    async def _zuggisaysno(self, ctx):
        LastMessages = await ctx.message.channel.history(limit=2).flatten()
        LastMessages.reverse()
        LastMessage = LastMessages[0]
        await LastMessage.reply(f"Zuggi sagt nein.")

    @commands.command(name="Orangensaft", aliases=["orangensaft", "OrangenSaft"], brief="Frag nicht was für Saft...")
    async def _orangejuice(self, ctx):
        if str(ctx.author) != "Schnenko#9944":
            await ctx.send(f"Frag nicht was für Saft, einfach Orangensaft! Tuuuuuuuurn up! Fassen Sie mich nicht an!")
        else:
            await ctx.send(f"https://tenor.com/view/nerd-moneyboy-money-boy-hau-gif-16097814")

    @commands.command(name="Ehrenmann", aliases=["ehrenmann"], brief="Der erwähnte User ist ein Ehrenmann!")
    async def _ehrenmann(self, ctx, user: commands.MemberConverter):
        await ctx.send(f"{user.mention}, du bist ein gottverdammter Ehrenmann!<:Ehrenmann:762764389384192000>")

    @commands.group(name="meme", aliases=["Meme", "patti", "Patti", "Mittwoch", "mittwoch"], invoke_without_command=True, brief="Gibt ein Zufallsmeme aus, kann auch Memes adden")
    @commands.cooldown(2, 180, commands.BucketType.user)
    @commands.has_permissions(attach_files=True)
    async def _memearchiv(self, ctx):
        if len(AllFiles) == 0:
            RefreshMemes()
        match (ctx.invoked_with):
            case ("Patti" | "patti"):
                PattiMemes = list(filter(lambda x: 'patti' in x, AllFiles))
                if PattiMemes == []:
                    RefreshMemes()
                    PattiMemes = list(filter(lambda x: 'patti' in x, AllFiles))
                RandomPattiMeme = random.choice(PattiMemes)
                AuthorPatti = RandomPattiMeme.split("/")[1].split("#")[0]
                await ctx.send(f"Zufalls-Meme! Dieses Meme wurde eingereicht von {AuthorPatti}", file=discord.File(f"{RandomPattiMeme}"))
                AllFiles.remove(RandomPattiMeme)
                logging.info(f"{ctx.author} wanted a patti meme.")
            case ("Mittwoch" | "mittwoch"):
                if datetime.now().isoweekday() == 3:
                    WednesdayMemes = list(
                        filter(lambda x: 'Mittwoch' in x, AllFiles))
                    if WednesdayMemes == []:
                        RefreshMemes()
                        WednesdayMemes = list(
                            filter(lambda x: 'Mittwoch' in x, AllFiles))
                    RandomWedMeme = random.choice(WednesdayMemes)
                    WednesdayAuthor = RandomWedMeme.split("/")[1].split("#")[0]
                    MyDudesAdjectives = ["ehrenhaften", "hochachtungsvollen",
                                         "kerligen", "verehrten", "memigen", "standhaften", "stabilen"]
                    await ctx.send(f"Es ist Mittwoch, meine {random.choice(MyDudesAdjectives)} Kerle!!!", file=discord.File(f"{RandomWedMeme}"))
                    AllFiles.remove(RandomWedMeme)
                    logging.info(f"{ctx.author} wanted a wednesday meme.")
                else:
                    WednesdayMemes = list(
                        filter(lambda x: 'Mittwoch' not in x, AllFiles))
                    if NoWednesdayMemes == []:
                        RefreshMemes()
                        NoWednesdayMemes = list(
                            filter(lambda x: 'Mittwoch' not in x, AllFiles))
                    RandomWedMeme = random.choice(AllFiles)
                    WednesdayAuthor = RandomWedMeme.split("/")[1].split("#")[0]
                    await ctx.send(f"Zufalls-Meme! Dieses Meme wurde eingereicht von {WednesdayAuthor}", file=discord.File(f"{RandomWedMeme}"))
                    AllFiles.remove(RandomWedMeme)
                    logging.info(
                        f"{ctx.author} wanted a wednesday meme but it is not wednesday.")
            case _:
                NoWednesdayMemes = list(
                    filter(lambda x: 'Mittwoch' not in x, AllFiles))
                if NoWednesdayMemes == []:
                    RefreshMemes()
                    NoWednesdayMemes = list(
                        filter(lambda x: 'Mittwoch' not in x, AllFiles))
                RandomMeme = random.choice(NoWednesdayMemes)
                AuthorOfMeme = RandomMeme.split("/")[1].split("#")[0]
                await ctx.send(f"Zufalls-Meme! Dieses Meme wurde eingereicht von {AuthorOfMeme}", file=discord.File(f"{RandomMeme}"))
                AllFiles.remove(RandomMeme)
                logging.info(f"{ctx.author} wanted a random meme.")

    @_memearchiv.command(name="add", aliases=["+"], brief="Fügt das Meme der oberen Nachricht hinzu")
    @commands.cooldown(2, 180, commands.BucketType.user)
    async def _addmeme(self, ctx):
        LastMessages = await ctx.message.channel.history(limit=2).flatten()
        LastMessages.reverse()
        if LastMessages[0].author != bot.user:
            if ctx.invoked_parents[0] in ['Mittwoch', 'mittwoch']:
                NumberOfMemes = next(
                    os.walk(f"memes/Mittwoch meine Kerle#"))[2]
                NumberOfFiles = len(NumberOfMemes)
                for index, meme in enumerate(LastMessages[0].attachments):
                    if meme.filename.lower().endswith(('gif', 'jpg', 'png', 'jpeg')):
                        await meme.save(f"memes/Mittwoch meine Kerle#/{NumberOfFiles + 1 + index}_{meme.filename}")
                        await ctx.send("Mittwoch Memes hinzugefügt.")
                        logging.info(
                            f"{ctx.author} has added a wednesday meme.")
                        RefreshMemes()
                    else:
                        pass
            else:
                if os.path.exists(f"memes/{LastMessages[0].author}") == False:
                    os.mkdir(f"memes/{LastMessages[0].author}")
                NumberOfMemes = next(
                    os.walk(f"memes/{LastMessages[0].author}"))[2]
                NumberOfFiles = len(NumberOfMemes)
                for index, meme in enumerate(LastMessages[0].attachments):
                    if meme.filename.lower().endswith(('gif', 'jpg', 'png', 'jpeg')):
                        await meme.save(f"memes/{LastMessages[0].author}/{NumberOfFiles + 1 + index}_{meme.filename}")
                        await ctx.send("Memes hinzugefügt.")
                        logging.info(
                            f"{ctx.author} has added a meme.")
                        RefreshMemes()
                    else:
                        pass

    @_memearchiv.command(name="collect", aliases=["coll", "Collect", "Coll"], brief="Sammelt das Meme per ID ein")
    @commands.cooldown(2, 180, commands.BucketType.user)
    async def _collmeme(self, ctx, Message: commands.MessageConverter):
        if Message.author != bot.user:
            if ctx.invoked_parents[0] in ['Mittwoch', 'mittwoch']:
                NumberOfMemes = next(
                    os.walk(f"memes/Mittwoch meine Kerle#"))[2]
                NumberOfFiles = len(NumberOfMemes)
                for index, meme in enumerate(Message.attachments):
                    if meme.filename.lower().endswith(('gif', 'jpg', 'png', 'jpeg')):
                        await meme.save(f"memes/Mittwoch meine Kerle#/{NumberOfFiles + 1 + index}_{meme.filename}")
                        await ctx.send("Mittwoch Memes hinzugefügt.")
                        logging.info(
                            f"{ctx.author} has added a wednesday meme.")
                        RefreshMemes()
                    else:
                        pass
            else:
                if os.path.exists(f"memes/{Message.author}") == False:
                    os.mkdir(f"memes/{Message.author}")
                NumberOfMemes = next(os.walk(f"memes/{Message.author}"))[2]
                NumberOfFiles = len(NumberOfMemes)
                for index, meme in enumerate(Message.attachments):
                    if meme.filename.lower().endswith(('gif', 'jpg', 'png', 'jpeg')):
                        await meme.save(f"memes/{Message.author}/{NumberOfFiles + 1 + index}_{meme.filename}")
                        await ctx.send("Dieses spicy Meme wurde eingesammelt.", file=await meme.to_file())
                        logging.info(
                            f"{ctx.author} has collected a meme.")
                        RefreshMemes()
                    else:
                        pass

    @commands.Cog.listener("on_message")
    async def _uwumsg(self, message):
        if isinstance(message.channel, discord.channel.DMChannel):
            pass
        elif message.channel.category_id != 539547423782207488 and message.channel.id not in [539549544585756693, 539546796939149334]:
            pass
        else:
            if message.author == bot.user:
                return
            if random.randint(0, 75) == 1:
                LastMessageContent = message.content
                flags = uwuify.SMILEY | uwuify.YU
                await message.channel.send(f"{uwuify.uwu(LastMessageContent, flags=flags)} <:UwU:870283726704242698>")
                logging.info(
                    f"The message [{LastMessageContent}] was UwUed.")

    @commands.command(name="uwu", aliases=["UwU", "Uwu", "uWu", "uWU"], brief="Weebt die Message UwU")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.check(_is_nouwuchannel)
    async def _uwuthis(self, ctx):
        if ctx.message.author == bot.user:
            return
        LastMessages = await ctx.message.channel.history(limit=2).flatten()
        LastMessages.reverse()
        flags = uwuify.SMILEY | uwuify.YU
        await ctx.send(uwuify.uwu(LastMessages[0].content, flags=flags))
        logging.info(
            f"{ctx.message.author} hat die Nachricht [{LastMessages[0].content}] geUwUt.")

    @commands.group(name="Hans", invoke_without_command=True, aliases=["hans"], brief="Er muss arbeiten...?")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def _hansworks(self, ctx):
        HansTasks = _read_json('Settings.json')
        HansTask = random.choice(HansTasks['Settings']['HansTask']['Tasks'])
        await ctx.send(f"Hans muss {HansTask}...")

    @_hansworks.command(name="add", aliases=['+', 'Add'], brief="Fügt Hans einen Task hinzu")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def _add_hansworks(self, ctx, task):
        if "```" not in task:
            HansTasks = _read_json('Settings.json')
            HansTasks['Settings']['HansTask']['Tasks'].append(task)
            _write_json('Settings.json', HansTasks)
            await ctx.send(f"Der Task '{task}' wurde Hans hinzugefügt.")
        else:
            await ctx.send("Das füge ich nicht hinzu.")

    @_hansworks.command(name="show", aliases=['sh', '-s'], brief="Zeigt Hans Aufgaben an")
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def _show_hansworks(self, ctx):
        HansTasks = _read_json('Settings.json')
        HansOutputString = ""
        HansOutputLength = 0
        await ctx.send(f"Hans hat folgende Tasks:\n")
        for HansTaskEntry in HansTasks['Settings']['HansTask']['Tasks']:
            HansOutputLength += len(HansTaskEntry)
            if HansOutputLength >= 1994:
                await ctx.send(f"```{HansOutputString}```")
                HansOutputString = ""
                HansOutputLength = 0
            HansOutputString += HansTaskEntry + "\n"
            HansOutputLength = HansOutputLength + len(HansTaskEntry)
        await ctx.send(f"```{HansOutputString}```")

    @_hansworks.command(name="num", aliases=["Number", "count", "Count"], brief="Zeigt, wie beschäftigt Hans ist")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _count_hansworks(self, ctx):
        HansTasks = _read_json('Settings.json')
        HansTaskCount = len(HansTasks['Settings']['HansTask']['Tasks'])
        await ctx.send(f"Hans hat {HansTaskCount} Aufgaben vor sich! So ein vielbeschäftiger Mann!")
        logging.info(f"{ctx.author} wanted to know how busy hans is.")

    @commands.command(name="Schnabi", aliases=["schnabi", "Hirnfresser", "Schnabeltier", "schnabeltier"], brief=r"Weebs out for Schnabi \o/")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _schnabiuwu(self, ctx):
        AnimeElement = requests.get('https://api.waifu.pics/sfw/waifu')
        if AnimeElement.status_code == 200:
            AnimeJSON = json.loads(AnimeElement.content)
            AnimeURL = AnimeJSON['url']
            await ctx.send(f"{AnimeURL}")
        else:
            await ctx.send("API ist gerade nicht erreichbar TwT")

    @commands.command(name="Zucker", aliases=["zucker", "Zuggi", "zuggi"], brief="Zuckersüß")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _zuggishow(self, ctx):
        RandomIndex = random.randrange(0, 990, 30)
        RecipURL = requests.get(
            f"https://www.chefkoch.de/rs/s{RandomIndex}/kartoffel/Rezepte.html")
        if RecipURL.status_code == 200:
            RecipHTML = BeautifulSoup(RecipURL.text, "html.parser")
            RecipJSON = json.loads("".join(RecipHTML.find_all(
                "script", {"type": "application/ld+json"})[1]))
            RandomRecipIndex = random.randint(0, 30)
            RecipElementName = RecipJSON['itemListElement'][RandomRecipIndex]['name']
            RecipElementURL = RecipJSON['itemListElement'][RandomRecipIndex]['url']
            await ctx.send(f"{RecipElementName}\n{RecipElementURL}")
        else:
            await ctx.send("Kartoffel API ist leider down T_T")

    @commands.command(name="Josch", aliases=["josch", "fullstack"], brief="Entwickler...")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _blamedevs(self, ctx):
        await ctx.send(file=discord.File('memes/josch700#3680/josch.png'))

    @commands.command(name="Feiertag", aliases=["feiertag", "holiday", "Holiday"], brief="Zeigt den nächsten Feiertag an")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _nextholiday(self, ctx):
        NextHolidayElement = requests.get(
            f'https://date.nager.at/api/v3/nextpublicholidays/DE')
        if NextHolidayElement.status_code == 200:
            NextHolidayJSON = json.loads(NextHolidayElement.content)
            NextHoliday = NextHolidayJSON[0]
            GermanDate = parser.parse(NextHoliday['date'])
            await ctx.send(
                f"Der nächste Feiertag ist der {NextHoliday['localName']}, dieser findet am {GermanDate.day}.{GermanDate.month}.{GermanDate.year} statt.")
        else:
            await ctx.send("Die API für den nächsten Feiertag ist nicht erreichbar :(")

    @commands.group(name="Doto", invoke_without_command=True, aliases=["doto", "DotoJokes", "dotojokes", "dotoJokes"], brief="Gute Witze, schlechte Witze")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _dotojokes(self, ctx):
        if len(DotoJokes) == 0:
            RefreshJokes()
        DotoJoke = random.choice(DotoJokes)
        await ctx.send(f"{DotoJoke}")
        DotoJokes.remove(DotoJoke)

    @_dotojokes.command(name="add", aliases=['+', 'Add'], brief="Fügt einen Doto-Joke hinzu")
    @commands.has_role("Admin")
    async def _add_dotojoke(self, ctx, joke):
        DotoJokesJSON = _read_json('Settings.json')
        DotoJokesJSON['Settings']['DotoJokes']['Jokes'].append(joke)
        _write_json('Settings.json', DotoJokesJSON)
        await ctx.send(f"Der Schenkelklopfer '{joke}' wurde hinzugefügt.")
        RefreshJokes()

    @_dotojokes.command(name="show", aliases=['sh', '-s'], brief="Zeigt alle Doto-Jokes")
    async def _show_dotojokes(self, ctx):
        DotoJokesJSON = _read_json('Settings.json')
        DotoOutputString = ""
        DotoOutputLength = 0
        await ctx.send(f"Doto hat folgende Gagfeuerwerke gezündet:\n")
        for DotoTaskEntry in DotoJokesJSON['Settings']['DotoJokes']['Jokes']:
            DotoOutputLength += len(DotoTaskEntry)
            if DotoOutputLength >= 1994:
                await ctx.send(f"```{DotoOutputString}```")
                DotoOutputString = ""
                DotoOutputLength = 0
            DotoOutputString += DotoTaskEntry + "\n\n"
            DotoOutputLength = DotoOutputLength + len(DotoTaskEntry)
        await ctx.send(f"```{DotoOutputString}```")

    @_dotojokes.command(name="count", aliases=["num", "Number", "Count"], brief="Wie viele Gags hat Doto nochmal gerissen?")
    async def _count_dotojokes(self, ctx):
        DotoJokesJSON = _read_json('Settings.json')
        DotoJokesCount = len(DotoJokesJSON['Settings']['DotoJokes']['Jokes'])
        await ctx.send(f"Doto hat bereits {DotoJokesCount} Knaller im Discord gezündet!")

    @commands.command(name="TVoed", aliases=["tvoed", "Tvoed", "TVoeD"], brief="Zeigt die Gehaltsgruppe im TVöD an")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _calctvoed(self, ctx, eggroup: str, step):
        CurrentYear = datetime.now().year
        TVSiteHTML = requests.get(
            f"https://oeffentlicher-dienst.info/c/t/rechner/tvoed/vka?id=tvoed-vka-{CurrentYear}&matrix=1")
        TVSiteText = TVSiteHTML.text.replace("100%", "100")
        TVTableData = pd.read_html(TVSiteText)
        TVTable = TVTableData[1]
        TVTableCleaned = TVTable.drop(index=[19, 20]).iloc[:, 0:7]
        TVTableCleaned = TVTableCleaned.rename(columns={"€": "EG"})
        TVTableCleaned = TVTableCleaned.sort_index(ascending=False)
        TVTableCleaned = TVTableCleaned[f"Entgelttabelle TVÖD VKA {CurrentYear}"]
        TVTableCleaned["EG"] = TVTableCleaned["EG"].str.replace(u'\xa0', u' ')
        try:
            TVEGRow = TVTableCleaned[TVTableCleaned["EG"]
                                     == f"{eggroup}"][f"{step}"]
            if TVEGRow.empty == False and pd.isna(TVEGRow.values[0]) == False:
                await ctx.send(f"Dies entspricht: {TVEGRow.values[0]}€ Brutto laut Entgeldtabelle des TVöD.")
                logging.info(f"{ctx.author} calculated a TVoeD group.")
            else:
                await ctx.send("Diese Kombination aus EG Gruppe und Stufe gibt es im TVöD nicht.")
                logging.info(
                    f"{ctx.author} tried to calculate a combination of TVoeD group and step that does not exist.")
        except KeyError:
            await ctx.send("Diese Entgeldgruppe oder Stufe gibt es im TVöD nicht.")
            logging.info(
                f"{ctx.author} tried to calculate a TVoeD group that does not exist.")

    @_calctvoed.error
    async def _calctvoed_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Dieser Befehl ist noch im Cooldown.")
            logging.warning(f"{ctx.author} wanted to spam the TVoeD-command!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Es fehlt ein Parameter. Bitte !tvoed 'E X'[Leerzeichen] Stufe eingeben.")

    @_memearchiv.error
    async def _memearchiv_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Dieser Befehl ist noch im Cooldown.")
            logging.warning(f"{ctx.author} wanted to spam random memes!")

    @_uwuthis.error
    async def _uwuthis_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Dieser Befehl ist noch im Cooldown.")
            logging.warning(f"{ctx.author} wanted to spam the UwUcommand!")

    @_hansworks.error
    async def _hanstasks_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Dieser Befehl ist noch im Cooldown.")
            logging.warning(f"{ctx.author} wanted to spam the hanscommand!")

    @_dotojokes.error
    async def _dotojoke_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Dieser Befehl ist noch im Cooldown.")
            logging.warning(f"{ctx.author} wanted to spam Doto-Jokes!")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("Nur Doto darf so schlechte Witze machen und hinzufügen.")
            logging.warning(f"{ctx.author} wanted to add Doto-Jokes!")

    @_zuggishow.error
    async def _zuggishow_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Dieser Befehl ist noch im Cooldown.")
            logging.warning(f"{ctx.author} wanted to spam the zuggicommand!")

    @_schnabiuwu.error
    async def _schnabiuwu_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Dieser Befehl ist noch im Cooldown.")
            logging.warning(f"{ctx.author} wanted to spam the schnabicommand!")


class Corona(commands.Cog, name="Corona"):
    """
    Eine Klasse für Corona Funktionen, aktuell werden hier nur aktuelle Zahlen abgerufen.
    """

    async def cog_check(self, ctx):
        return _is_banned(ctx, BannedUsers)

    @commands.command(name="Corona", aliases=["corona", "covid", "COVID", "Covid"], brief="Gibt aktuelle Coronazahlen aus")
    async def _coronazahlen(self, ctx):
        CovURL = "https://www.corona-in-zahlen.de/weltweit/deutschland/"
        CovHTML = requests.get(CovURL)
        CovResult = BeautifulSoup(CovHTML.content, "html.parser")
        CovRate = CovResult.find_all("p", class_="card-title")
        WeeklyInz = CovRate[3].text.strip()
        NewCovCases = CovRate[9].text.strip()
        NewAvgWeek = CovRate[10].text.strip()
        HospRate = CovRate[12].text.strip()
        HospNum = CovRate[13].text.strip()
        HospPerc = CovRate[14].text.strip()

        await ctx.send(f"Seit gestern gab es {NewCovCases} neue COVID-19 Fälle, in den letzten 7 Tagen waren es im Schnitt {NewAvgWeek} Fälle pro Tag. Die Inzidenz liegt bei {WeeklyInz}.\n\n"
                       f"Die Hospitalisierungsrate liegt bei {HospRate}, dies entspricht {HospNum} Menschen und {HospPerc} der Intensivbetten\U0001F637")
        logging.info(
            f"User {ctx.author} has requested the COVID numbers.")


class Meetings(commands.Cog, name="Meetings"):
    """
    Diese Klasse handelt alle Verabredungen, sowie deren Funktionen, wie zum Beispiel Beitritt ab.

    !Game [Uhrzeit]:        Erstellt eine Verabredung zur Uhrzeit im Format HH:mm
    !Join                   Tritt der Verabredung bei
    !RemGame                Löscht die Verabredung
    !LeaveGame              Verlässt die Verabredung, ist man Owner, wird diese gelöscht
    !UpdateGame [Uhrzeit]   Aktualisiert die Verabredung auf die angegebene Uhrzeit
    !ShowGame               Zeigt die Verabredung in diesem Channel
    """

    async def cog_check(self, ctx):
        return _is_banned(ctx, BannedUsers)

    @commands.command(name="game", aliases=["Game"], brief="Startet eine Verabredung")
    @commands.check(_is_gamechannel)
    async def _playgame(self, ctx, timearg):
        try:
            CurrentDate = datetime.now()
            GameTime = datetime.strptime(timearg, "%H:%M").time()
            GameDateTime = datetime.combine(CurrentDate, GameTime)
            GameDateTimeTimestamp = GameDateTime.timestamp()
        except ValueError:
            await ctx.send("Na na, das ist keine Uhrzeit!")
            logging.warning(
                f"{ctx.author} entered a wrong time for the gamecommand!")
            return

        group = {
            f"{ctx.message.channel.name}": {
                "id": ctx.message.channel.id,
                "owner": ctx.message.author.mention,
                "time": GameDateTimeTimestamp,
                "members": [f"{ctx.message.author.mention}"]
            }
        }

        try:
            groups = _read_json('Settings.json')

            if not groups:
                groups["Settings"]["Groups"].update(group)
                _write_json('Settings.json', groups)
                await ctx.send("Die Spielrunde wurde eröffnet!")
                logging.info(
                    f"Meeting started in {ctx.message.channel.name}.")
            else:
                if ctx.message.channel.name in groups["Settings"]["Groups"].keys():
                    await ctx.send(f"{ctx.author.name}, hier ist schon eine Spielrunde geplant. Joine einfach mit !join")
                else:
                    groups["Settings"]["Groups"].update(group)
                    _write_json('Settings.json', groups)
                    await ctx.send("Die Spielrunde wurde eröffnet!")
                    logging.info(
                        f"Meeting started in {ctx.message.channel.name}.")
        except json.decoder.JSONDecodeError:
            groups = {}
            groups["Settings"]["Groups"].update(group)
            _write_json('Settings.json', groups)
            await ctx.send("Die Spielrunde wurde eröffnet!")
            logging.warning(
                f"The settingsfile is corrupted, overwrote the file and started meeting in {ctx.message.channel.name}!")

    @commands.command(name="ShowGame", aliases=["showgame", "Showgame"], brief="Zeigt die Mitglieder der Verabredung")
    @commands.check(_is_gamechannel)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def _showgame(self, ctx):
        CurrentChannel = ctx.message.channel.name
        GameSettings = _read_json('Settings.json')
        if ctx.message.channel.name in GameSettings["Settings"]["Groups"].keys():
            GameMembersString = "\n".join(
                GameSettings["Settings"]["Groups"][f"{CurrentChannel}"]["members"])
            await ctx.send(f"Folgende Personen sind verabredet:\n{GameMembersString}")
        else:
            await ctx.send("Hier gibt es noch keine Verabredung.")

    @commands.command(name="join", aliases=["Join"], brief="Tritt einer Verabredung bei")
    @commands.check(_is_gamechannel)
    async def _joingame(self, ctx):
        CurrentChannel = ctx.message.channel.name
        groups = _read_json('Settings.json')

        if ctx.message.channel.name in groups["Settings"]["Groups"].keys() and ctx.message.author.mention in groups["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
            await ctx.send(f"{ctx.message.author.name}, du bist bereits als Teilnehmer im geplanten Spiel.")
        elif ctx.message.channel.name in groups["Settings"]["Groups"].keys() and f"{ctx.message.author.mention}" not in groups["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
            groups["Settings"]["Groups"][f"{CurrentChannel}"]["members"].append(
                f"{ctx.message.author.mention}")
            await ctx.send(f"{ctx.author.mention}, du wurdest dem Spiel hinzugefügt.")
            logging.info(
                f"{ctx.author} joined the meeting in {ctx.message.channel.name}.")
            _write_json('Settings.json', groups)
        else:
            await ctx.send("In diesem Channel wurde noch kein Spiel geplant.")

    @commands.command(name="UpdateGame", aliases=["updategame", "Updategame", "updateGame"], brief="Verschiebt das Spiel auf die gewünschte Zeit")
    @commands.check(_is_gamechannel)
    async def _movegame(self, ctx, timearg):
        CurrentChannel = ctx.message.channel.name
        groups = _read_json('Settings.json')

        if ctx.message.channel.name in groups["Settings"]["Groups"].keys() and ctx.message.author.mention == groups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            try:
                CurrentDate = datetime.now()
                GameTime = datetime.strptime(timearg, "%H:%M").time()
                GameDateTime = datetime.combine(CurrentDate, GameTime)
                GameDateTimeTimestamp = GameDateTime.timestamp()
            except ValueError:
                await ctx.send("Na na, das ist keine Uhrzeit!")
                logging.warning(
                    f"{ctx.author} entered a wrong time for the updategamecommand!")
                return

            groups["Settings"]["Groups"][f"{CurrentChannel}"]["time"] = GameDateTimeTimestamp
            _write_json('Settings.json', groups)
            await ctx.send(f"Die Uhrzeit der Verabredung wurde auf {timearg} geändert.")
            logging.info(
                f"{ctx.author} moved the meeting in {CurrentChannel} to {timearg}.")
        elif ctx.message.channel.name in groups["Settings"]["Groups"].keys() and ctx.message.author.mention != groups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            await ctx.send("Na na, du bist nicht der Besitzer dieser Verabredung! Frag bitte den Besitzer, ob er es verschiebt!")
            logging.warning(
                f"{ctx.author} tried to move the meeting in {CurrentChannel} but is not the owner!")
        elif ctx.message.channel.name not in groups["Settings"]["Groups"].keys():
            await ctx.send("Hier gibt es noch keine Verabredung. Starte doch eine!")

    @commands.command(name="RemGame", aliases=["remgame"], brief="Löscht die Verabredung")
    @commands.check(_is_gamechannel)
    async def _gameremover(self, ctx):
        CurrentChannel = ctx.message.channel.name
        groups = _read_json('Settings.json')
        if ctx.message.channel.name in groups["Settings"]["Groups"].keys() and ctx.message.author.mention == groups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            groups["Settings"]["Groups"].pop(CurrentChannel)
            _write_json('Settings.json', groups)
            await ctx.send("Die Verabredung in diesem Channel wurde gelöscht.")
            logging.info(
                f"{ctx.author} deleted the meeting in {CurrentChannel}.")
        elif ctx.message.channel.name in groups["Settings"]["Groups"].keys() and ctx.message.author.mention != groups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            await ctx.send("Na na, du bist nicht der Besitzer dieser Verabredung! Frag bitte den Besitzer, ob er diese löscht!")
            logging.warning(
                f"{ctx.author} tried to delete a meeting in {CurrentChannel} but is not the owner!")
        elif ctx.message.channel.name not in groups["Settings"]["Groups"].keys():
            await ctx.send("Hier gibt es noch keine Verabredung. Starte doch eine!")

    @commands.command(name="LeaveGame", aliases=["leavegame", "lvgame", "qGame", "QuitGame", "leave", "Leave"], brief="Verlässt die aktuelle Verabredung")
    @commands.check(_is_gamechannel)
    async def _leavegame(self, ctx):
        CurrentChannel = ctx.message.channel.name
        StartedGroups = _read_json('Settings.json')
        if ctx.message.channel.name in StartedGroups["Settings"]["Groups"].keys() and ctx.message.author.mention == StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            StartedGroups["Settings"]["Groups"].pop(CurrentChannel)
            _write_json('Settings.json', StartedGroups)
            await ctx.send(f"{ctx.author.mention}, die Verabredung in diesem Channel wurde gelöscht, da du der Besitzer warst.")
            logging.info(
                f"{ctx.author} left the meeting in {CurrentChannel} and was the owner. Meeting deleted.")
        elif ctx.message.channel.name in StartedGroups["Settings"]["Groups"].keys() and ctx.message.author.mention in StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
            StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["members"].remove(
                ctx.message.author.mention)
            await ctx.send(f"{ctx.author.mention}, du wurdest aus der Verabredung entfernt.")
            logging.info(
                f"{ctx.author} removed from meeting in {CurrentChannel}")
            _write_json('Settings.json', StartedGroups)
        elif ctx.message.channel.name in StartedGroups["Settings"]["Groups"].keys() and ctx.message.author.mention not in StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
            await ctx.send(f"{ctx.author.mention}, du bist der Verabredung nicht beigetreten und wurdest daher auch nicht entfernt.")
            logging.info(
                f"{ctx.author} wanted to leave the meeting in {CurrentChannel}, but was not a member.")
        else:
            await ctx.send(f"{ctx.author.mention}, hier gibt es keine Verabredung, die du verlassen könntest.")
            logging.info(
                f"{ctx.author} wanted to leave a meeting in {CurrentChannel}, but there was none.")

    ## Error Handling for Meetings Cog ###

    @_playgame.error
    async def _playgame_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Bitte gib eine Uhrzeit an!")
            logging.warning(f"{ctx.author} hat keine Uhrzeit angegeben!")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("Das hier ist kein Unterhaltungschannel, hier kann man sich nicht verabreden.")
            logging.warning(
                f"{ctx.author} wanted to meet outside of an entertainment channel!")

    @_joingame.error
    async def _joingame_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Das hier ist kein Unterhaltungschannel, hier kann man sich nicht verabreden.")
            logging.warning(
                f"{ctx.author} wanted to meet outside of an entertainment channel!")

    @_leavegame.error
    async def _leavegame_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Das hier ist kein Unterhaltungschannel, hier gibt es keine Verabredungen.")
            logging.warning(
                f"{ctx.author} wanted to leave a meeting outside of an entertainment channel!")

    @_showgame.error
    async def _showgame_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Der Befehl ist noch im Cooldown.")
            logging.warning(
                f"{ctx.author} wanted to spam the members of a game in {ctx.message.channel.name}!")


class Games(commands.Cog, name="Games"):
    """
    Klasse für Videospielinhalte (eigentlich nicht mehr notwendig/vollständig).

    ESAGame:        Zeigt das aktuelle ESA Game auf Twitch an.
    OWHeld:         Generiert einen OW Helden, supported Rollen und Anzahl.
    """

    async def cog_check(self, ctx):
        return _is_banned(ctx, BannedUsers)

    @commands.command(name="ESAGame", aliases=["esagame"], brief="Gibt das aktuelle ESA Game aus")
    async def _esagame(self, ctx):
        try:
            USER = "esamarathon"
            r = requests.get(f'https://api.twitch.tv/helix/search/channels?query={USER}',
                             headers={'Authorization': f'Bearer {TWITCH_TOKEN}', 'Client-Id': f'{TWITCH_CLIENT_ID}'})
            data = json.loads(r.content)['data']
            data = list(
                filter(lambda x: x["broadcaster_login"] == f"{USER}", data))[0]

            if data['game_id'] is not None:
                gamerequest = requests.get(f'https://api.twitch.tv/helix/games?id={data["game_id"]}',
                                           headers={'Authorization': f'Bearer {TWITCH_TOKEN}', 'Client-Id': f'{TWITCH_CLIENT_ID}'})
                game = json.loads(gamerequest.content)['data'][0]
            else:
                game = {"name": "Irgendwas"}

            await ctx.send(f"Bei ESA wird gerade {game['name']} gespielt!")
            logging.info(f"{ctx.author} invoked the ESA command")
        except IndexError:
            # Username does not exist or Username is wrong, greetings to Schnabeltier
            logging.error("ESA Channel not found. Was it deleted or banned?!")
        except json.decoder.JSONDecodeError:
            logging.error("Twitch API not available.")
        except KeyError:
            logging.error("Twitch API not available.")

    @commands.command(name="OwHeld", aliases=["owhero", "owheld", "OWHeld", "RndHeld", "rndheld", "ow", "OW", "Ow"], brief="Weißt einen zufälligen Helden zu")
    @commands.check(_is_owchannel)
    async def _randomowhero(self, ctx, *args):
        """
        Lässt einen zufälligen Helden aus Overwatch generieren.
        Unterstützt sowohl Rolle, als auch Anzahl der Helden.
        """

        OWPage = requests.get('https://playoverwatch.com/en-us/heroes/#all')
        OWContent = BeautifulSoup(OWPage.content, "html.parser")
        OW_Heros = OWContent.find_all(
            'div', class_='hero-portrait-detailed-container')
        ListOfSupports = []
        ListOfTanks = []
        ListOfDPS = []
        SelectedHeros = []
        role = args[0]
        number = int(args[1])
        for hero in OW_Heros:
            if hero.attrs["data-groups"][2:-2] == "SUPPORT":
                ListOfSupports.append(hero.text)
            elif hero.attrs["data-groups"][2:-2] == "TANK":
                ListOfTanks.append(hero.text)
            elif hero.attrs["data-groups"][2:-2] == "DAMAGE":
                ListOfDPS.append(hero.text)
        ListOfAllHeros = ListOfTanks + ListOfDPS + ListOfSupports
        if role in ["SUPPORT", "support", "Support", "healer", "Healer"] and number < len(ListOfSupports):
            for _ in range(0, number):
                SelectedHero = random.choice(ListOfSupports)
                ListOfSupports.remove(f"{SelectedHero}")
                SelectedHeros.append(SelectedHero)
                SelectedHerosString = ", ".join(SelectedHeros)
            await ctx.send(f"Folgende Helden wurden ausgewählt: {SelectedHerosString}")
            logging.info(
                f"User {ctx.author} raffled a support hero from Overwatch.")
        elif role in ["DAMAGE", "DPS", "DMG", "Damage", "dmg", "dps", "Dps"] and number < len(ListOfDPS):
            for _ in range(0, number):
                SelectedHero = random.choice(ListOfDPS)
                ListOfDPS.remove(f"{SelectedHero}")
                SelectedHeros.append(SelectedHero)
                SelectedHerosString = ", ".join(SelectedHeros)
            await ctx.send(f"Folgende Helden wurden ausgewählt: {SelectedHerosString}")
            logging.info(
                f"User {ctx.author} raffled a dps hero from Overwatch.")
        elif role in ["TANK", "tank", "Tank"] and number < len(ListOfTanks):
            for _ in range(0, number):
                SelectedHero = random.choice(ListOfTanks)
                ListOfTanks.remove(f"{SelectedHero}")
                SelectedHeros.append(SelectedHero)
                SelectedHerosString = ", ".join(SelectedHeros)
            await ctx.send(f"Folgende Helden wurden ausgewählt: {SelectedHerosString}")
            logging.info(
                f"User {ctx.author} raffled a tank hero from Overwatch.")
        elif role in ["all", "All", "ALL", "alle", "Alle"] and number < len(ListOfAllHeros):
            for _ in range(0, number):
                SelectedHero = random.choice(ListOfAllHeros)
                ListOfAllHeros.remove(f"{SelectedHero}")
                SelectedHeros.append(SelectedHero)
                SelectedHerosString = ", ".join(SelectedHeros)
            await ctx.send(f"Folgende Helden wurden ausgewählt: {SelectedHerosString}")
            logging.info(
                f"User {ctx.author} raffled a general hero from Overwatch.")


class Administration(commands.Cog, name="Administration"):
    """
    Die Administrator Klasse, hier werden Teile des Bots verwaltet:

    Cogs:                      Können geladen oder entladen werden.
    Twitch:                    User hinzufügen oder löschen.
    Log:                       Zeigt die neusten 10 Zeilen des Log.
    MC Reboot:                 Startet den MC Server neu.
    """

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return _is_banned(ctx, BannedUsers)

    @commands.command(name="mcreboot", aliases=["MCReboot"], brief="Rebootet den MC Server")
    @commands.cooldown(1, 7200, commands.BucketType.user)
    @commands.has_any_role("Der Stack", "Admin")
    async def _mcreboot(self, ctx):
        """
        Rebootet den Minecraft Server per SSH.
        """

        try:

            MCDATA = _read_json('MC_DATA.json')
            host = MCDATA['MC_HOST']
            username = MCDATA['MC_USER']
            password = MCDATA['MC_PW']
            port = MCDATA['SSH_PORT']
            KillScreenCommand = "screen -S minecraft -X quit"
            RebootCommand = "sudo reboot"

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port, username, password)

            ssh.exec_command(KillScreenCommand)
            time.sleep(10)
            ssh.exec_command(RebootCommand)
            ssh.close()

            await ctx.send(f"{ctx.author.name} hat den Minecraft Server neugestartet.")
            logging.info(f"User {ctx.author} rebooted the minecraftserver.")

        except json.JSONDecodeError:
            logging.error("Could not load JSON File!", exc_info=True)
        except:
            logging.error(
                "Something went wrong, is the Pi reachable?", exc_info=True)

    @commands.group(name="tw", invoke_without_command=False, aliases=["twitch", "Twitch", "TW"], brief="Verwaltet das Twitch File")
    @commands.has_role("Admin")
    @commands.cooldown(3, 900, commands.BucketType.user)
    async def _twitchmanagement(self, ctx):
        """
        Verwaltet die Twitch Benachrichtigungen.

        Add: Fügt den User hinzu
        Del: Entfernt den User
        """
        pass

    @_twitchmanagement.command(name="show", aliases=["sh", "-s", "Show"], brief="Zeigt die Twitchmember")
    async def _showtwitchmembers(self, ctx):
        TwitchSettings = _read_json('Settings.json')
        TwitchUserString = "\n".join(
            TwitchSettings["Settings"]["TwitchUser"].keys())
        await ctx.send(f"Folgende User sind hinterlegt:\n```{TwitchUserString}```")
        logging.info(f"Twitchlist was posted.")

    @_twitchmanagement.command(name="add", aliases=["+"], brief="Fügt den Twitchuser der Liste hinzu")
    async def _addtwitchmembers(self, ctx, Member: str):
        try:
            TwitchUser = _read_json('Settings.json')
            TwitchMember = {f"{Member.lower()}": False}
            TwitchUser['Settings']['TwitchUser'].update(TwitchMember)
            _write_json('Settings.json', TwitchUser)
            await ctx.send(f"{Member} zur Twitchliste hinzugefügt!")
            logging.info(f"User {Member} was added to twitchlist.")
        except:
            await ctx.send("Konnte User nicht hinzufügen.")
            logging.error(
                f"User {Member} could not be added.", exc_info=True)

    @_twitchmanagement.command(name="del", aliases=["-"], brief="Löscht den Twitchuser aus der Liste")
    async def _deltwitchmember(self, ctx, Member: str):
        try:
            TwitchUser = _read_json('Settings.json')
            TwitchUser['Settings']['TwitchUser'].pop(f"{Member.lower()}")
            _write_json('Settings.json', TwitchUser)
            await ctx.send(f"{Member} wurde aus der Twitchliste entfernt.")
            logging.info(f"User {Member} was removed from twitchlist.")
        except:
            await ctx.send("Konnte User nicht entfernen.")
            logging.error(
                f"User {Member} could not be removed from twitchlist.", exc_info=True)

    @commands.command(name="ext", aliases=["Ext", "Extension", "extension"], brief="Verwaltet Extensions")
    @commands.has_role("Admin")
    async def _extensions(self, ctx, ChangeArg, extension):
        """
        Verwaltet die externen Cogs.

        Load:   Lädt die Cog in den Bot.
        Unload: Entfernt die Cog aus dem Bot.
        """

        if ChangeArg == "load":
            bot.load_extension(f"cogs.{extension}")
            await ctx.send(f"Extension {extension} wurde geladen und ist jetzt einsatzbereit.")
            logging.info(f"Extension {extension} was loaded.")
        elif ChangeArg == "unload":
            bot.unload_extension(f"cogs.{extension}")
            await ctx.send(f"Extension {extension} wurde entfernt und ist nicht mehr einsatzfähig.")
            logging.info(f"Extension {extension} was unloaded.")

    @commands.command(name="log", aliases=["Log", "LOG"], brief="Zeigt die neusten Logeinträge des Bots")
    @commands.has_role("Admin")
    async def _showlog(self, ctx):
        """
        Zeigt die letzten 10 Einträge des Logs.
        """

        AllLogFiles = next(os.walk("logs/"))[2]
        SortedLogFiles = sorted(AllLogFiles)
        LatestLogFile = SortedLogFiles[-1]
        with open(f'logs/{LatestLogFile}', 'r') as LogFileRead:
            LogContent = LogFileRead.readlines()
            LatestLogLines = LogContent[-10:]
            LogOutputInString = "".join(LatestLogLines)
            await ctx.send(f"```{LogOutputInString}```")
        logging.info(f"{ctx.author} has called for the log.")

    @commands.command(name="Ban", aliases=["ban", "bann", "Bann"], brief="Hindert den User am verwenden von Commands")
    @commands.has_any_role("Admin", "Moderatoren")
    async def _banuser(self, ctx, user: commands.MemberConverter):
        UserString = str(user)
        BannedUserJSON = _read_json('Settings.json')
        BannedUsers = BannedUserJSON['Settings']['BannedUsers']
        if UserString not in BannedUsers:
            BannedUsers.append(UserString)
            _write_json('Settings.json', BannedUserJSON)
            await ctx.send(f"User {UserString} wurde für 24 Stunden für Befehle gebannt.")
            logging.info(f"User {UserString} was banned from using commands.")
            _get_banned_users()
        else:
            await ctx.send("Dieser User ist bereits gebannt.")

    @commands.command(name="Unban", aliases=["unban", "entbannen", "UnBan"], brief="Gibt den User für Commands frei")
    @commands.has_any_role("Admin", "Moderatoren")
    async def _unbanuser(self, ctx, user: commands.MemberConverter):
        UserString = str(user)
        BannedUserJSON = _read_json('Settings.json')
        BannedUsers = BannedUserJSON['Settings']['BannedUsers']
        if UserString in BannedUsers:
            BannedUsers.remove(UserString)
            _write_json('Settings.json', BannedUserJSON)
            await ctx.send(f"Der User {UserString} wurde entbannt.")
            logging.info(f"User {UserString} was unbanned.")
            _get_banned_users()
        else:
            ctx.send(f"Der Benutzer {UserString} ist nicht gebannt.")

    @commands.command(name="ip", aliases=["IP", "Ip", "vpnip", "VPNip", "VPNIP"], brief="Gibt die aktuelle public IP aus")
    @commands.has_any_role("Admin", "Moderatoren")
    async def _returnpubip(self, ctx):
        MyIP = requests.get('https://api.ipify.org').content.decode('UTF-8')
        await ctx.send(f"Die aktuelle IP lautet: {MyIP}")
        logging.info(f"{ctx.author} requested the public ip.")

    ### Error Handling for Administrator Cog ###

    @_mcreboot.error
    async def _mcreboot_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            AdminGroup = _read_json('Settings.json')
            AdminToNotify = AdminGroup['Settings']['ManagementGroups']['Admins']
            await ctx.send(f"Na na, das darfst du nicht! <@{AdminToNotify}> guck dir diesen Schelm an!")
            logging.warning(
                f"{ctx.author} wanted to reboot the minecraftserver but is not allowed!")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Der Befehl ist aktuell noch im Cooldown.")
            logging.warning(
                f"{ctx.author} wanted to reboot the minecraftserver multiple times in three hours!")

    @_twitchmanagement.error
    async def _twitchmanagement_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            AdminGroup = _read_json('Settings.json')
            AdminToNotify = AdminGroup['Settings']['ManagementGroups']['Admins']
            await ctx.send(f"Na na, das darf nur der Admin! <@{AdminToNotify}>, hier möchte jemand in die Twitchliste oder aus der Twitchliste entfernt werden!")
            logging.warning(f"{ctx.author} wanted to edit the twitchlist!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Hier fehlte der User oder der Parameter!")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Der Befehl ist aktuell noch im Cooldown.")


### Tasks Section ###


@tasks.loop(seconds=60)
async def TwitchLiveCheck():
    """
    Erneuert den Twitch Token, sofern abgelaufen.
    Prüft jede Minute ob jemand bei Twitch live gegangen ist,
    das Ganze wird in ein JSON File gespeichert, sofern der Livestatus sich geändert hat.
    Zuletzt wird eine Benachrichtigung in meinen oder den Kumpels Channel gepostet.
    """

    if datetime.timestamp(datetime.now()) > TWITCH_TOKEN_EXPIRES:
        RequestTwitchToken()

    TWITCHUSERNAMES = _read_json('Settings.json')

    for USER, LASTSTATE in TWITCHUSERNAMES['Settings']['TwitchUser'].items():

        try:
            rUserData = requests.get(f'https://api.twitch.tv/helix/search/channels?query={USER}',
                                     headers={'Authorization': f'Bearer {TWITCH_TOKEN}', 'Client-Id': f'{TWITCH_CLIENT_ID}'})
            data = json.loads(rUserData.content)['data']
            data = list(
                filter(lambda x: x["broadcaster_login"] == f"{USER}", data))[0]
        except IndexError:
            # Username does not exist or Username is wrong, greetings to Schnabeltier
            continue
        except json.decoder.JSONDecodeError:
            logging.error("Twitch API not available.")
            break
        except KeyError:
            logging.error("Twitch API not available.")
            break

        if LASTSTATE is False and data['is_live'] and USER == data['broadcaster_login']:
            # User went live
            if data['game_id'] is not None:
                gamerequest = requests.get(f'https://api.twitch.tv/helix/games?id={data["game_id"]}',
                                           headers={'Authorization': f'Bearer {TWITCH_TOKEN}', 'Client-Id': f'{TWITCH_CLIENT_ID}'})
                game = json.loads(gamerequest.content)['data'][0]
            else:
                game = {"name": "Irgendwas"}

            try:
                rDisplayName = requests.get(f'https://api.twitch.tv/helix/users?id={data["id"]}',
                                            headers={'Authorization': f'Bearer {TWITCH_TOKEN}', 'Client-Id': f'{TWITCH_CLIENT_ID}'})
                Displayname = json.loads(rDisplayName.content)[
                    'data'][0]['display_name']
            except:
                Displayname = USER.title()
            CurrentTime = int(datetime.timestamp(datetime.now()))
            embed = discord.Embed(title=f"{data['title']}", colour=discord.Colour(
                0x772ce8), url=f"https://twitch.tv/{USER}", timestamp=datetime.utcnow())
            embed.set_image(
                url=f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{USER}-1920x1080.jpg?v={CurrentTime}")
            embed.set_author(
                name=f"{Displayname} ist jetzt live!", icon_url=f"{data['thumbnail_url']}")
            embed.set_footer(text="Bizeps_Bot")

            if USER == 'dota_joker':
                await bot.get_channel(539547495567720492).send(content=f"**{Displayname}** ist live! Gestreamt wird {game['name']}!", embed=embed)
                logging.info(
                    f"{Displayname} went live on Twitch! Twitch Notification sent!")
            else:
                channel = bot.get_channel(703530328836407327)
                NotificationTime = datetime.utcnow() - timedelta(minutes=60)
                LastMessages = await channel.history(after=NotificationTime).flatten()
                if LastMessages:
                    LastMessages.reverse()
                    for message in LastMessages:
                        if message.content.startswith(f"**{Displayname}**") is True:
                            break
                    else:
                        await bot.get_channel(703530328836407327).send(content=f"**{Displayname}** ist live! Gestreamt wird {game['name']}!", embed=embed)
                        logging.info(
                            f"{Displayname} went live on Twitch! Twitch Twitch Notification sent, because the last Notification is older than 60min!")
                else:
                    await bot.get_channel(703530328836407327).send(content=f"**{Displayname}** ist live! Gestreamt wird {game['name']}!", embed=embed)
                    logging.info(
                        f"{Displayname} went live on Twitch! Twitch Notification sent!")

        if LASTSTATE is not data['is_live']:
            TWITCHUSERNAMES['Settings']['TwitchUser'][USER] = data['is_live']
            _write_json('Settings.json', TWITCHUSERNAMES)


@tasks.loop(seconds=60)
async def GameReminder():
    """
    Prüft jede Minute ob eine Verabredung eingerichtet ist,
    wenn ja wird in den Channel ein Reminder zur Uhrzeit gepostet.
    """

    CurrentTime = datetime.timestamp(datetime.now())
    groups = _read_json('Settings.json')
    FoundList = []
    for reminder in groups["Settings"]["Groups"].keys():
        if CurrentTime > groups["Settings"]["Groups"][f"{reminder}"]["time"]:
            Remindchannel = bot.get_channel(
                groups["Settings"]["Groups"][f"{reminder}"]["id"])
            ReminderMembers = ", ".join(
                groups["Settings"]["Groups"][f"{reminder}"]["members"])
            await Remindchannel.send(f" Das Spiel geht los! Mit dabei sind: {ReminderMembers}")
            logging.info(f"Meeting in {reminder} started!")
            FoundList.append(reminder)
    if FoundList:
        for reminder in FoundList:
            groups["Settings"]["Groups"].pop(f'{reminder}')
        _write_json('Settings.json', groups)


@tasks.loop(minutes=30)
async def TrashReminder():
    """
    Prüft alle 30min ob morgen Müll ist und sendet eine Nachricht an mich per Discord DM,
    dabei wird eine CSV Datei eingelesen und durchiteriert.
    """
    TodayAtFivePM = datetime.now().replace(
        hour=17, minute=00, second=00, microsecond=00)
    TodayAtFiveAndAHalfPM = datetime.now().replace(
        hour=17, minute=32, second=00, microsecond=00)
    if datetime.now() >= TodayAtFivePM and datetime.now() <= TodayAtFiveAndAHalfPM:
        AdminToNotify = 248181624485838849
        MyDiscordUser = await bot.fetch_user(AdminToNotify)
        tomorrowNow = datetime.today() + timedelta(days=1)
        tomorrowClean = tomorrowNow.replace(
            hour=00, minute=00, second=00, microsecond=00)
        MuellListe = pd.read_csv('Muell.csv', sep=";")
        for entry in MuellListe["Schwarze Tonne"].dropna():
            EntryDate = pd.to_datetime(entry[3:], dayfirst=True)
            if tomorrowClean == EntryDate:
                await MyDiscordUser.send(f"Die nächste schwarze Tonne ist morgen am: {entry}")
                logging.info(
                    f"Reminder for black garbage can which is collected on {entry} sent!")
        for entry in MuellListe["Blaue Tonne"].dropna():
            EntryDate = pd.to_datetime(entry[3:], dayfirst=True)
            if tomorrowClean == EntryDate:
                await MyDiscordUser.send(f"Die nächste blaue Tonne ist morgen am: {entry}")
                logging.info(
                    f"Reminder for blue garbage can which is collected on {entry} sent!")
        for entry in MuellListe["Gelbe Saecke"].dropna():
            EntryDate = pd.to_datetime(entry[3:], dayfirst=True)
            if tomorrowClean == EntryDate:
                await MyDiscordUser.send(f"Die nächsten gelben Säcke sind morgen am: {entry}")
                logging.info(
                    f"Reminder for yellow trashbag which is collected on {entry} sent!")


@tasks.loop(minutes=5)
async def GetFreeEpicGames():

    AllEpicFiles = next(os.walk("epic/"))[2]
    NumberOfEpicFiles = len(AllEpicFiles)

    FreeGamesList = _read_json('Settings.json')
    CurrentTime = datetime.now(timezone.utc)
    EndedOffers = []

    for FreeGameEntry in FreeGamesList['Settings']['FreeEpicGames'].keys():

        GameEndDate = parser.parse(
            FreeGamesList['Settings']['FreeEpicGames'][f"{FreeGameEntry}"]["endDate"])
        if CurrentTime > GameEndDate:
            EndedOffers.append(FreeGameEntry)

    if EndedOffers:
        for EndedOffer in EndedOffers:
            FreeGamesList['Settings']['FreeEpicGames'].pop(EndedOffer)
            logging.info(
                f"{EndedOffer} removed from free Epic Games, since it expired!")
        _write_json('Settings.json', FreeGamesList)

    EpicStoreURL = 'https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=de&country=DE&allowCountries=DE'

    RequestFromEpic = requests.get(EpicStoreURL)
    if RequestFromEpic.status_code == 200:
        JSONFromEpicStore = RequestFromEpic.json()
        if JSONFromEpicStore:
            for FreeGame in JSONFromEpicStore['data']['Catalog']['searchStore']['elements']:
                if FreeGame['promotions'] is not None and FreeGame['promotions']['promotionalOffers'] != []:
                    PromotionalStartDate = parser.parse(
                        FreeGame['promotions']['promotionalOffers'][0]['promotionalOffers'][0]['startDate'])
                    LaunchingToday = parser.parse(FreeGame['effectiveDate'])

                    if FreeGame['price']['totalPrice']['discountPrice'] == 0 and (LaunchingToday.date() <= datetime.now().date() or PromotionalStartDate.date() <= datetime.now().date()):
                        offers = FreeGame['promotions']['promotionalOffers']
                        for offer in offers:

                            FreeGameObject = {
                                f"{FreeGame['title']}": {
                                    "startDate": offer['promotionalOffers'][0]['startDate'],
                                    "endDate": offer['promotionalOffers'][0]['endDate'],
                                }
                            }

                            try:

                                if FreeGame['title'] in FreeGamesList['Settings']['FreeEpicGames'].keys():
                                    pass
                                else:
                                    FreeGamesList['Settings']['FreeEpicGames'].update(
                                        FreeGameObject)
                                    _write_json(
                                        'Settings.json', FreeGamesList)
                                    EndOfOffer = offer['promotionalOffers'][0]['endDate']
                                    EndDateOfOffer = parser.parse(
                                        EndOfOffer).date()

                                    for index in range(len(FreeGame['keyImages'])):
                                        if FreeGame['keyImages'][index]['type'] == "Thumbnail":
                                            EpicImageURL = FreeGame['keyImages'][index]['url']
                                            EpicImage = requests.get(
                                                EpicImageURL)
                                            break
                                        elif FreeGame['keyImages'][index]['type'] == "DieselStoreFrontWide":
                                            EpicImageURL = FreeGame['keyImages'][index]['url']
                                            EpicImage = requests.get(
                                                EpicImageURL)
                                            break
                                        else:
                                            EpicImage = ""

                                    ### Build Embed with chosen vars ###
                                    EpicEmbed = discord.Embed(title=f"Neues Gratis Epic Game: {FreeGame['title']}!\r\n\nNoch einlösbar bis zum {EndDateOfOffer.day}.{EndDateOfOffer.month}.{EndDateOfOffer.year}!\r\n\n", colour=discord.Colour(
                                        0x1), timestamp=datetime.utcnow())
                                    EpicEmbed.set_thumbnail(
                                        url=r'https://cdn2.unrealengine.com/Epic+Games+Node%2Fxlarge_whitetext_blackback_epiclogo_504x512_1529964470588-503x512-ac795e81c54b27aaa2e196456dd307bfe4ca3ca4.jpg')
                                    EpicEmbed.set_author(
                                        name="Bizeps_Bot", icon_url="https://cdn.discordapp.com/app-icons/794273832508588062/06ac0fd02fdf7623a38d9a6d72061fa6.png")
                                    if "collection" or "bundle" or "trilogy" in FreeGame['productSlug']:
                                        EpicEmbed.add_field(
                                            name="Besuch mich im EGS", value=f"[Epic Games Store](https://store.epicgames.com/de/bundles/{FreeGame['productSlug']})", inline=True)
                                        EpicEmbed.add_field(
                                            name="Hol mich im Launcher", value=f"<com.epicgames.launcher://store/bundles/{FreeGame['productSlug']}>", inline=True)
                                    else:
                                        EpicEmbed.add_field(
                                            name="Besuch mich im EGS", value=f"[Epic Games Store](https://store.epicgames.com/de/p/{FreeGame['productSlug']})", inline=True)
                                        EpicEmbed.add_field(
                                            name="Hol mich im Launcher", value=f"<com.epicgames.launcher://store/p/{FreeGame['productSlug']}>", inline=True)
                                    if EpicImageURL:
                                        EpicImageURL = quote(
                                            EpicImageURL, safe=':/')
                                        EpicEmbed.set_image(
                                            url=f"{EpicImageURL}")
                                    EpicEmbed.set_footer(text="Bizeps_Bot")

                                    if EpicImage != "" and EpicImage.status_code == 200:
                                        EpicImagePath = f"{NumberOfEpicFiles +1}_epic.jpg"
                                        with open(f'epic/{EpicImagePath}', 'wb') as write_file:
                                            write_file.write(
                                                EpicImage.content)
                                    await bot.get_channel(539553203570606090).send(embed=EpicEmbed)
                                    logging.info(
                                        f"{FreeGame['title']} was added to free Epic Games!")

                            except json.decoder.JSONDecodeError:
                                FreeGamesList['Settings']['FreeEpicGames'] = {}
                                FreeGamesList['Settings']['FreeEpicGames'].update(
                                    FreeGameObject)
                                _write_json('Settings.json', FreeGamesList)
    else:
        logging.error("Epic Store is not available!")


@tasks.loop(minutes=30)
async def _get_free_steamgames():
    FreeGameTitleList = []
    FreeSteamList = _read_json('Settings.json')
    SteamURL = "https://store.steampowered.com/search/?maxprice=free&specials=1"
    SteamReq = requests.get(SteamURL)
    if SteamReq.status_code == 200:
        SteamHTML = BeautifulSoup(SteamReq.content, "html.parser")
        SteamResult = SteamHTML.find_all(
            "a", class_="search_result_row ds_collapse_flag")
        if SteamResult:
            for Result in SteamResult:
                SteamGameTitle = Result.find(class_="title").text
                if SteamGameTitle:
                    FreeGameTitleList.append(SteamGameTitle)
                    if SteamGameTitle not in FreeSteamList['Settings']['FreeSteamGames']:
                        SteamGameURL = Result['href']
                        ProdID = Result['data-ds-appid']
                        ImageSrc = f"https://cdn.akamai.steamstatic.com/steam/apps/{ProdID}/header.jpg"

                        SteamEmbed = discord.Embed(title=f"Neues Gratis Steam Game: {SteamGameTitle}!\r\n\n", colour=discord.Colour(
                            0x6c6c6c), timestamp=datetime.utcnow())
                        SteamEmbed.set_thumbnail(
                            url=r'https://store.cloudflare.steamstatic.com/public/images/v6/logo_steam_footer.png')
                        SteamEmbed.set_author(
                            name="Bizeps_Bot", icon_url="https://cdn.discordapp.com/app-icons/794273832508588062/06ac0fd02fdf7623a38d9a6d72061fa6.png")
                        SteamEmbed.add_field(
                            name="Besuch mich auf Steam", value=f"{SteamGameURL}", inline=True)
                        SteamEmbed.add_field(
                            name="Hol mich im Launcher", value=f"<Steam://Store/{ProdID}>", inline=True)
                        SteamImageURL = quote(ImageSrc, safe=':/')
                        SteamEmbed.set_image(url=f"{SteamImageURL}")
                        SteamEmbed.set_footer(text="Bizeps_Bot")
                        await bot.get_channel(539553203570606090).send(embed=SteamEmbed)
                        FreeSteamList['Settings']['FreeSteamGames'].append(
                            SteamGameTitle)
                        _write_json('Settings.json', FreeSteamList)
                        logging.info(
                            f"{SteamGameTitle} was added to the free steam game list.")

                    ExpiredGames = set(FreeSteamList['Settings']['FreeSteamGames']).difference(
                        FreeGameTitleList)
                    for ExpiredGame in ExpiredGames:
                        FreeSteamList['Settings']['FreeSteamGames'].remove(
                            ExpiredGame)
                        logging.info(
                            f"Removed {ExpiredGame} from free steam game list since it expired.")
                        _write_json('Settings.json', FreeSteamList)

### Bot Events ###


@bot.event
async def on_ready():
    """
    Startet den Bot und lädt alle notwendigen Cogs,
    dazu werden die Loops gestartet, sollten sie nicht schon laufen.
    """

    logging.info(f"Logged in as {bot.user}!")
    logging.info("Bot started up!")
    for File in os.listdir('./cogs'):
        if File.endswith('.py') and f"cogs.{File[:-3]}" not in bot.extensions.keys():
            bot.load_extension(f"cogs.{File[:-3]}")
            logging.info(f"Extension {File[:-3]} loaded.")
    if not TwitchLiveCheck.is_running():
        TwitchLiveCheck.start()
    if not GameReminder.is_running():
        GameReminder.start()
    if not TrashReminder.is_running():
        TrashReminder.start()
    if not GetFreeEpicGames.is_running():
        GetFreeEpicGames.start()
    if not _get_free_steamgames.is_running():
        _get_free_steamgames.start()
    RefreshMemes()
    RefreshJokes()
    _get_banned_users()


@bot.event
async def on_message(message):
    """
    Was bei einer Nachricht passieren soll.
    """
    if message.author == bot.user:
        return

    if(_is_banned(message, BannedUsers)):
        # This line needs to be added so the commands are actually processed
        await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    """
    Fehlerbehandlung falls Fehler bei einem Befehl auftreten.
    Aktuell werden dort nur fehlende Befehle behandelt.
    """

    if isinstance(error, commands.CommandNotFound):
        logging.warning(
            f"{error}, {ctx.author} wants a new command.")

if __name__ == '__main__':

    ### General Settings ###

    with open("TOKEN.json", "r") as TOKENFILE:
        TOKENDATA = json.load(TOKENFILE)
        TOKEN = TOKENDATA['DISCORD_TOKEN']
        TWITCH_CLIENT_ID = TOKENDATA['TWITCH_CLIENT_ID']
        TWITCH_CLIENT_SECRET = TOKENDATA['TWITCH_CLIENT_SECRET']
        STREAMLABS_TOKEN = TOKENDATA['STREAMLABS_TOKEN']
        if 'TWITCH_TOKEN' in TOKENDATA.keys() and 'TWITCH_TOKEN_EXPIRES' in TOKENDATA.keys() and datetime.timestamp(datetime.now()) < TOKENDATA['TWITCH_TOKEN_EXPIRES']:
            TWITCH_TOKEN = TOKENDATA['TWITCH_TOKEN']
            TWITCH_TOKEN_EXPIRES = TOKENDATA['TWITCH_TOKEN_EXPIRES']
        else:
            RequestTwitchToken()
        logging.info("Token successfully loaded.")

    ### Add Cogs in bot file ###

    bot.add_cog(Counter(bot))
    logging.info(f"Extension {Counter.__name__} loaded.")
    bot.add_cog(Fun(bot))
    logging.info(f"Extension {Fun.__name__} loaded.")
    bot.add_cog(Corona(bot))
    logging.info(f"Extension {Corona.__name__} loaded.")
    bot.add_cog(Meetings(bot))
    logging.info(f"Extension {Meetings.__name__} loaded.")
    bot.add_cog(Games(bot))
    logging.info(f"Extension {Games.__name__} loaded.")
    bot.add_cog(Administration(bot))
    logging.info(f"Extension {Administration.__name__} loaded.")

    ### Run Bot ###

    bot.run(TOKEN)
