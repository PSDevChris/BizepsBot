import time
from datetime import datetime, timedelta, timezone
import json
import os
import random
import logging
import discord
from discord.ext import commands, tasks
from discord.ext.commands import context
from dateutil import parser
import requests
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
    logging.info("Neues Twitch Token wurde erfolgreich angefordert.")


def _read_json(FileName):
    with open(f'{FileName}', 'r', encoding='utf-8') as JsonRead:
        return json.load(JsonRead)


def _write_json(FileName, Content):
    with open(f'{FileName}', 'w', encoding='utf-8') as JsonWrite:
        json.dump(Content, JsonWrite, indent=4)


def RefreshMemes():
    global AllFiles
    AllFiles = next(os.walk("memes/"))[2]
    return AllFiles

### Permission Checks ###

### Prüft ob der Minecraft Superuser ist laut Settings.json Datei ###


def _is_mcsu(ctx: context.Context):
    MCSUs = _read_json('Settings.json')
    return ctx.author.id in MCSUs['Settings']['ManagementGroups']['MCSUs']


def _is_owchannel(ctx):
    return ctx.message.channel.id == 554390037811167363


def _is_nouwuchannel(ctx):
    return ctx.message.channel.category_id != 539547423782207488 and ctx.message.channel.id not in [539549544585756693, 539546796939149334]


def _is_gamechannel(ctx):
    if isinstance(ctx.channel, discord.channel.DMChannel):
        return False
    else:
        return ctx.message.channel.category_id == 539553136222666792

### Prüft ob der User ein Admin ist laut Settings.json Datei ###


def _is_admin(ctx):
    AdminGroup = _read_json('Settings.json')
    return ctx.author.id == AdminGroup['Settings']['ManagementGroups']['Admins']

### General Settings ###


with open("TOKEN.json", "r") as TOKENFILE:
    TOKENDATA = json.load(TOKENFILE)
    TOKEN = TOKENDATA['DISCORD_TOKEN']
    TWITCH_CLIENT_ID = TOKENDATA['TWITCH_CLIENT_ID']
    TWITCH_CLIENT_SECRET = TOKENDATA['TWITCH_CLIENT_SECRET']
    if 'TWITCH_TOKEN' in TOKENDATA.keys() and 'TWITCH_TOKEN_EXPIRES' in TOKENDATA.keys() and datetime.timestamp(datetime.now()) < TOKENDATA['TWITCH_TOKEN_EXPIRES']:
        TWITCH_TOKEN = TOKENDATA['TWITCH_TOKEN']
        TWITCH_TOKEN_EXPIRES = TOKENDATA['TWITCH_TOKEN_EXPIRES']
    else:
        RequestTwitchToken()
    logging.info("Token successfully loaded.")

### Commands and Cogs Section ###


class Counter(commands.Cog, name="Counter"):
    """
    Die Klasse die alle Counter enthält und diese erhöht oder anzeigt,
    die Counter werden in einem JSON File abgelegt und gespeichert.
    """

    @commands.group(name="pun",  aliases=["Pun"], invoke_without_command=True, brief="Erhöht den Pun Counter")
    async def _puncounter(self, ctx):
        data = _read_json('Settings.json')
        data['Settings']['Counter']['Puns'] = data['Settings']['Counter']['Puns'] + 1
        PunNumber = data['Settings']['Counter']['Puns']
        _write_json('Settings.json', data)
        await ctx.send(f"Es wurde bereits {PunNumber} Mal ein Gagfeuerwerk gezündet!")

    @_puncounter.command(name="show", aliases=["sh", "-s", "Show"], brief="Zeigt den aktuellen Puncount")
    async def _show_puncounter(self, ctx):
        data = _read_json('Settings.json')
        await ctx.send(f"Bereits {data['Settings']['Counter']['Puns']} Gagfeuerwerke wurden gezündet!")

    @commands.group(name="mobbing",  aliases=["Mobbing", "Hasssprech", "hasssprech"], invoke_without_command=True, brief="Erhöht Hasssprech Counter")
    async def _mobbingcounter(self, ctx):
        data = _read_json('Settings.json')
        data['Settings']['Counter']['Mobbing'] = int(
            data['Settings']['Counter']['Mobbing']) + 1
        _write_json('Settings.json', data)
        MobbingNumber = data['Settings']['Counter']['Mobbing']
        await ctx.send(f"Das ist Hasssprech! {MobbingNumber} Mal wurde schon Hasssprech betrieben! Pfui!")

    @_mobbingcounter.command(name="show", aliases=["sh", "-s", "Show"], brief="Zeigt den aktuellen Hasssprech Counter")
    async def _show_mobbingcounter(self, ctx):
        data = _read_json('Settings.json')
        await ctx.send(f"Auf dem Discord wurde bereits {data['Settings']['Counter']['Mobbing']} Mal Hasssprech betrieben! Pfui!")

    @commands.group(name="leak", aliases=["Leak"], invoke_without_command=True, brief="Erhöht den Leak Counter")
    async def _leakcounter(self, ctx):
        data = _read_json('Settings.json')
        data['Settings']['Counter']['Leak'] = int(
            data['Settings']['Counter']['Leak']) + 1
        _write_json('Settings.json', data)
        LeakNumber = data['Settings']['Counter']['Leak']
        await ctx.send(f"Da hat wohl jemand nicht aufgepasst... Es wurde bereits {LeakNumber} Mal geleakt! Obacht!")

    @_leakcounter.command(name="show", aliases=["sh", "-s", "Show"], brief="Zeigt den aktuellen Leak Counter")
    async def _show_leakcounter(self, ctx):
        data = _read_json('Settings.json')
        await ctx.send(f"Bisher wurden {data['Settings']['Counter']['Leak']} Mal kritische Informationen geleakt.<:eyes:825006453936750612>")

    @commands.group(name="salz", aliases=["Salz"], invoke_without_command=True, brief="Erhöht den Salz Counter")
    async def _salzcounter(self, ctx):
        data = _read_json('Settings.json')
        data['Settings']['Counter']['Salz'] = int(
            data['Settings']['Counter']['Salz']) + 1
        _write_json('Settings.json', data)
        SalzNumber = data['Settings']['Counter']['Salz']
        await ctx.send(f"Man konnte sich schon {SalzNumber} Mal nicht beherrschen! Böse Salzstreuer hier!<:salt:826091230156161045>")

    @_salzcounter.command(name="show", aliases=["sh", "-s", "Show"], brief="Zeigt den aktuellen Salz Counter")
    async def _show_salzcounter(self, ctx):
        data = _read_json('Settings.json')
        await ctx.send(f"Bisher war es schon {data['Settings']['Counter']['Salz']} Mal salzig auf dem Discord!<:salt:826091230156161045>")

    @commands.group(name="Schnenko", aliases=["schnenko", "Schnenk", "schnenk"], invoke_without_command=True, brief="Wirtschaft dankt!")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _schnenkorder(self, ctx):
        data = _read_json('Settings.json')
        data['Settings']['Counter']['Lieferando'] = int(
            data['Settings']['Counter']['Lieferando']) + 20
        _write_json('Settings.json', data)
        LieferandoNumber = data['Settings']['Counter']['Lieferando']
        await ctx.send(f"Schnenko hat dieses Jahr bereits für {LieferandoNumber}€ bei Lieferando bestellt. Ein starkes Zeichen für die Wirtschaft!")

    @_schnenkorder.command(name="show", aliases=["sh", "-s", "Show"], brief="Zeigt Schnenkos Bestellfreudigkeit in Euro")
    async def _show_schnenkcounter(self, ctx):
        data = _read_json('Settings.json')
        await ctx.send(f"Schnenko hat dieses Jahr bereits {data['Settings']['Counter']['Lieferando']}€ in Lieferando investiert. Ist das der neue Bitcoin?!")

    @commands.group(name="Pipi", aliases=["pipi"], invoke_without_command=True, brief="Erhöht den Pipi Counter")
    async def _pipicounter(self, ctx):
        data = _read_json('Settings.json')
        data['Settings']['Counter']['Pipi'] = int(
            data['Settings']['Counter']['Pipi']) + 1
        _write_json('Settings.json', data)
        PipiNumber = data['Settings']['Counter']['Pipi']
        await ctx.send(f"Dotas Babyblase hat ihn schon {PipiNumber} auf das stille Örtchen getrieben!")

    @_pipicounter.command(name="show", aliases=["sh", "-s", "Show"], brief="Zeigt den aktuellen Pipi Counter")
    async def _show_pipicounter(self, ctx):
        data = _read_json('Settings.json')
        await ctx.send(f"Bisher war Dota schon {data['Settings']['Counter']['Pipi']} Mal auf dem stillen Örtchen!")

    @_schnenkorder.error
    async def _schnenkorder_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Dieser Befehl ist noch im Cooldown.")
            logging.warning(
                f"{ctx.author} wollte den Schnenkcounter stark nach oben drücken!")


class Fun(commands.Cog, name="Schabernack"):
    """
    Die Klasse für Spaßfunktionen, diverse Textausgaben, eine Funktion um Bilder in die Memegallery zu speichern,
    sie anzuzeigen und eine Textreplace Funktion um Texte zu UwUen wird alles hier abgehandelt.
    """

    @commands.command(name="Pub", aliases=["pub"], brief="Typos...")
    async def _pubtypo(self, ctx):
        await ctx.send(f"Das Discord Pub ist geschlossen, {ctx.author.name}! Du meintest wohl !pun?")

    @commands.command(name="Ehrenmann", aliases=["ehrenmann"], brief="Der erwähnte User ist ein Ehrenmann!")
    async def _ehrenmann(self, ctx, user: commands.MemberConverter):
        await ctx.send(f"{user.mention}, du bist ein gottverdammter Ehrenmann!<:Ehrenmann:762764389384192000>")

    @commands.group(name="meme", aliases=["Meme"], invoke_without_command=True, brief="Gibt ein Zufallsmeme aus, kann auch Memes adden")
    @commands.cooldown(3, 30, commands.BucketType.user)
    @commands.has_permissions(attach_files=True)
    async def _memearchiv(self, ctx):
        if len(AllFiles) == 0:
            RefreshMemes()
        RandomMeme = random.choice(AllFiles)
        await ctx.send("Zufalls-Meme!", file=discord.File(f"memes/{RandomMeme}"))
        AllFiles.remove(RandomMeme)
        logging.info(f"{ctx.author} hat ein Zufallsmeme angefordert.")

    @_memearchiv.command(name="add", aliases=["+"], brief="Fügt das Meme der oberen Nachricht hinzu")
    async def _addmeme(self, ctx):
        AllFiles = next(os.walk("memes/"))[2]
        NumberOfFiles = len(AllFiles)
        LastMessages = await ctx.message.channel.history(limit=2).flatten()
        LastMessages.reverse()
        for index, meme in enumerate(LastMessages[0].attachments):
            if meme.filename.lower().endswith(('gif', 'jpg', 'png', 'jpeg')):
                await meme.save(f"memes/{NumberOfFiles + index}_{meme.filename}")
                await ctx.send("Memes hinzugefügt.")
                logging.info(
                    f"{ctx.author} hat ein Meme erfolgreich hinzugefügt.")
                RefreshMemes()
            else:
                pass

    @_memearchiv.command(name="collect", aliases=["coll", "Collect", "Coll"], brief="Sammelt das Meme per ID ein")
    async def _collmeme(self, ctx, Message: commands.MessageConverter):
        AllFiles = next(os.walk("memes/"))[2]
        NumberOfFiles = len(AllFiles)
        for index, meme in enumerate(Message.attachments):
            if meme.filename.lower().endswith(('gif', 'jpg', 'png', 'jpeg')):
                await meme.save(f"memes/{NumberOfFiles + index}_{meme.filename}")
                await ctx.send("Dieses spicy Meme wurde eingesammelt.", file=await meme.to_file())
                logging.info(
                    f"{ctx.author} hat ein Meme erfolgreich eingesammelt.")
                RefreshMemes()
            else:
                pass

    @commands.Cog.listener("on_message")
    @commands.check(_is_nouwuchannel)
    async def _uwumsg(self, message):
        if isinstance(message.channel, discord.channel.DMChannel):
            pass
        else:
            if message.channel.category_id != 539547423782207488 and message.channel.id not in [539549544585756693, 539546796939149334]:
                if message.author == bot.user:
                    return
                if random.randint(0, 75) == 1:
                    LastMessageContent = message.content
                    flags = uwuify.SMILEY | uwuify.YU
                    await message.channel.send(f"{uwuify.uwu(LastMessageContent, flags=flags)} <:UwU:870283726704242698>")
                    logging.info(
                        f"Die Nachricht [{LastMessageContent}] wurde UwUt.")

    @commands.command(name="uwu", aliases=["UwU", "Uwu", "uWu", "uWU"], brief="Weebt die Message UwU")
    @commands.cooldown(1, 30, commands.BucketType.user)
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
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _hansworks(self, ctx):
        HansTasks = _read_json('Settings.json')
        HansTask = random.choice(HansTasks['Settings']['HansTask']['Tasks'])
        await ctx.send(f"Hans muss {HansTask}...")

    @_hansworks.command(name="add", aliases=['+', 'Add'], brief="Fügt Hans einen Task hinzu")
    async def _add_hansworks(self, ctx, task):
        HansTasks = _read_json('Settings.json')
        HansTasks['Settings']['HansTask']['Tasks'].append(task)
        _write_json('Settings.json', HansTasks)
        await ctx.send(f"Der Task {task} wurde Hans hinzugefügt.")

    @_hansworks.command(name="show", aliases=['sh', '-s'], brief="Zeigt Hans Aufgaben an")
    async def _show_hansworks(self, ctx):
        HansTasks = _read_json('Settings.json')
        HansTasksString = "\n".join(HansTasks['Settings']['HansTask']['Tasks'])
        await ctx.send(f"Hans hat folgende Tasks:\n```{HansTasksString}```")

    @commands.command(name="Schnabi", aliases=["schnabi", "Hirnfresser", "Schnabeltier", "schnabeltier"], brief=r"Weebs out for Schnabi \o/")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _schnabiuwu(self, ctx):
        await ctx.send("""
⡆⣐⢕⢕⢕⢕⢕⢕⢕⢕⠅⢗⢕⢕⢕⢕⢕⢕⢕⠕⠕⢕⢕⢕⢕⢕⢕⢕⢕⢕
⢐⢕⢕⢕⢕⢕⣕⢕⢕⠕⠁⢕⢕⢕⢕⢕⢕⢕⢕⠅⡄⢕⢕⢕⢕⢕⢕⢕⢕⢕
⢕⢕⢕⢕⢕⠅⢗⢕⠕⣠⠄⣗⢕⢕⠕⢕⢕⢕⠕⢠⣿⠐⢕⢕⢕⠑⢕⢕⠵⢕
⢕⢕⢕⢕⠁⢜⠕⢁⣴⣿⡇⢓⢕⢵⢐⢕⢕⠕⢁⣾⢿⣧⠑⢕⢕⠄⢑⢕⠅⢕
⢕⢕⠵⢁⠔⢁⣤⣤⣶⣶⣶⡐⣕⢽⠐⢕⠕⣡⣾⣶⣶⣶⣤⡁⢓⢕⠄⢑⢅⢑
⠍⣧⠄⣶⣾⣿⣿⣿⣿⣿⣿⣷⣔⢕⢄⢡⣾⣿⣿⣿⣿⣿⣿⣿⣦⡑⢕⢤⠱⢐
⢠⢕⠅⣾⣿⠋⢿⣿⣿⣿⠉⣿⣿⣷⣦⣶⣽⣿⣿⠈⣿⣿⣿⣿⠏⢹⣷⣷⡅⢐
⣔⢕⢥⢻⣿⡀⠈⠛⠛⠁⢠⣿⣿⣿⣿⣿⣿⣿⣿⡀⠈⠛⠛⠁⠄⣼⣿⣿⡇⢔
⢕⢕⢽⢸⢟⢟⢖⢖⢤⣶⡟⢻⣿⡿⠻⣿⣿⡟⢀⣿⣦⢤⢤⢔⢞⢿⢿⣿⠁⢕
⢕⢕⠅⣐⢕⢕⢕⢕⢕⣿⣿⡄⠛⢀⣦⠈⠛⢁⣼⣿⢗⢕⢕⢕⢕⢕⢕⡏⣘⢕
⢕⢕⠅⢓⣕⣕⣕⣕⣵⣿⣿⣿⣾⣿⣿⣿⣿⣿⣿⣿⣷⣕⢕⢕⢕⢕⡵⢀⢕⢕
⢑⢕⠃⡈⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢃⢕⢕⢕
⣆⢕⠄⢱⣄⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⢁⢕⢕⠕⢁
⣿⣦⡀⣿⣿⣷⣶⣬⣍⣛⣛⣛⡛⠿⠿⠿⠛⠛⢛⣛⣉⣭⣤⣂⢜⠕⢑⣡⣴⣿""")

    @commands.command(name="Zucker", aliases=["zucker", "Zuggi", "zuggi"], brief="Zuckersüß")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _zuggishow(self, ctx):
        await ctx.send("(◕‿◕✿)")

    @_memearchiv.error
    async def _memearchiv_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Dieser Befehl ist noch im Cooldown.")
            logging.warning(f"{ctx.author} wollte Random Memes spammen!")

    @_uwuthis.error
    async def _uwuthis_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Dieser Befehl ist noch im Cooldown.")
            logging.warning(f"{ctx.author} wollte den Uwubefehl spammen!")

    @_hansworks.error
    async def _zuggishow_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Dieser Befehl ist noch im Cooldown.")
            logging.warning(f"{ctx.author} wollte den Hansbefehl spammen!")

    @_zuggishow.error
    async def _zuggishow_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Dieser Befehl ist noch im Cooldown.")
            logging.warning(f"{ctx.author} wollte den Zuggibefehl spammen!")

    @_schnabiuwu.error
    async def _schnabiuwu_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Dieser Befehl ist noch im Cooldown.")
            logging.warning(f"{ctx.author} wollte den Schnabibefehl spammen!")


class Corona(commands.Cog, name="Corona"):
    """
    Eine Klasse für Corona Funktionen, aktuell werden hier nur aktuelle Zahlen abgerufen.
    """

    @commands.command(name="Corona", aliases=["corona", "covid", "COVID", "Covid"], brief="Gibt aktuelle Coronazahlen aus")
    async def _coronazahlen(self, ctx):
        CORONA_URL = "https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Fallzahlen.html"
        CORONA_PAGE = requests.get(CORONA_URL)
        CORONA_RESULT = BeautifulSoup(CORONA_PAGE.content, "html.parser")
        CORONA_TABLE = CORONA_RESULT.find("table")
        CORONA_ROWS = CORONA_TABLE.find_all("strong")
        CORONA_CASES_YESTERDAY = CORONA_ROWS[2].text
        CORONA_CASES_WEEK = CORONA_ROWS[3].text
        await ctx.send(f"Seit gestern gab es {CORONA_CASES_YESTERDAY} neue COVID-19 Fälle, in den letzten 7 Tagen waren es {CORONA_CASES_WEEK} Fälle\U0001F637")
        logging.info(
            f"User {ctx.author} hat die heutigen Coronazahlen abgefragt.")


class Meetings(commands.Cog, name="Meetings"):
    """
    Diese Klasse handelt alle Verabredungen, sowie deren Funktionen, wie zum Beispiel Beitritt ab.

    !Game [Uhrzeit]:        Erstellt eine Verabredung zur Uhrzeit im Format HH:mm
    !Join                   Tritt der Verabredung bei
    !RemGame                Löscht die Verabredung
    !LeaveGame              Verlässt die Verabredung, ist man Owner, wird diese gelöscht
    !UpdateGame [Uhrzeit]   Aktualisiert die Verabredung auf die angegebene Uhrzeit
    """

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
                f"{ctx.author} hat eine falsche Uhrzeit angegeben!")
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
                    f"Verabredung in {ctx.message.channel.name} eröffnet.")
            else:
                if ctx.message.channel.name in groups["Settings"]["Groups"].keys():
                    await ctx.send(f"{ctx.author.name}, hier ist schon eine Spielrunde geplant. Joine einfach mit !join")
                else:
                    groups["Settings"]["Groups"].update(group)
                    _write_json('Settings.json', groups)
                    await ctx.send("Die Spielrunde wurde eröffnet!")
                    logging.info(
                        f"Verabredung in {ctx.message.channel.name} eröffnet.")
        except json.decoder.JSONDecodeError:
            groups = {}
            groups["Settings"]["Groups"].update(group)
            _write_json('Settings.json', groups)
            await ctx.send("Die Spielrunde wurde eröffnet!")
            logging.warning(
                f"Das Settings.json File war nicht lesbar, Verabredung in {ctx.message.channel.name} trotzdem eröffnet!")

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
                f"{ctx.author} wurde der Verabredung in {ctx.message.channel.name} hinzugefügt.")
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
                    f"{ctx.author} hat eine falsche Uhrzeit angegeben!")
                return

            groups["Settings"]["Groups"][f"{CurrentChannel}"]["time"] = GameDateTimeTimestamp
            _write_json('Settings.json', groups)
            await ctx.send(f"Die Uhrzeit der Verabredung wurde auf {timearg} geändert.")
            logging.info(
                f"{ctx.author} hat seine Verabredung verschoben auf {timearg}.")
        elif ctx.message.channel.name in groups["Settings"]["Groups"].keys() and ctx.message.author.mention != groups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            await ctx.send("Na na, du bist nicht der Besitzer dieser Verabredung! Frag bitte den Besitzer, ob er es verschiebt!")
            logging.warning(
                f"{ctx.author} wollte eine Verabredung verschieben, die nicht Ihm gehört!")
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
            logging.info(f"{ctx.author} hat seine Verabredung gelöscht.")
        elif ctx.message.channel.name in groups["Settings"]["Groups"].keys() and ctx.message.author.mention != groups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            await ctx.send("Na na, du bist nicht der Besitzer dieser Verabredung! Frag bitte den Besitzer, ob er diese löscht!")
            logging.warning(
                f"{ctx.author} wollte eine Verabredung löschen, die nicht Ihm gehört!")
        elif ctx.message.channel.name not in groups["Settings"]["Groups"].keys():
            await ctx.send("Hier gibt es noch keine Verabredung. Starte doch eine!")

    @commands.command(name="LeaveGame", aliases=["leavegame", "lvgame", "qGame", "QuitGame"], brief="Verlässt die aktuelle Verabredung")
    @commands.check(_is_gamechannel)
    async def _leavegame(self, ctx):
        CurrentChannel = ctx.message.channel.name
        StartedGroups = _read_json('Settings.json')
        if ctx.message.channel.name in StartedGroups["Settings"]["Groups"].keys() and ctx.message.author.mention == StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["owner"]:
            StartedGroups["Settings"]["Groups"].pop(CurrentChannel)
            _write_json('Settings.json', StartedGroups)
            await ctx.send(f"{ctx.author.mention}, die Verabredung in diesem Channel wurde gelöscht, da du der Besitzer warst.")
            logging.info(
                f"{ctx.author} hat seine Verabredung verlassen, daher wurde sie gelöscht.")
        elif ctx.message.channel.name in StartedGroups["Settings"]["Groups"].keys() and ctx.message.author.mention in StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
            StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["members"].remove(
                ctx.message.author.mention)
            await ctx.send(f"{ctx.author.mention}, du wurdest aus der Verabredung entfernt.")
            logging.info(
                f"{ctx.author} wurde aus der Verabredung in {ctx.message.channel.name} entfernt.")
            _write_json('Settings.json', StartedGroups)
        elif ctx.message.channel.name in StartedGroups["Settings"]["Groups"].keys() and ctx.message.author.mention not in StartedGroups["Settings"]["Groups"][f"{CurrentChannel}"]["members"]:
            await ctx.send(f"{ctx.author.mention}, du bist der Verabredung nicht beigetreten und wurdest daher auch nicht entfernt.")
            logging.info(
                f"{ctx.author} wollte die Verabredung in {ctx.message.channel.name} verlassen, war aber kein Mitglied.")
        else:
            await ctx.send(f"{ctx.author.mention}, hier gibt es keine Verabredung, die du verlassen könntest.")
            logging.info(
                f"{ctx.author} wollte eine Verabredung in {ctx.message.channel.name} verlassen, aber es gab keine.")

    ## Error Handling for Meetings Cog ###

    @_playgame.error
    async def _playgame_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Bitte gib eine Uhrzeit an!")
            logging.warning(f"{ctx.author} hat keine Uhrzeit angegeben!")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("Das hier ist kein Unterhaltungschannel, hier kann man sich nicht verabreden.")
            logging.warning(
                f"{ctx.author} wollte sich in keinem Unterhaltungschannel verabreden!")

    @_joingame.error
    async def _joingame_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Das hier ist kein Unterhaltungschannel, hier kann man sich nicht verabreden.")
            logging.warning(
                f"{ctx.author} wollte sich in keinem Unterhaltungschannel verabreden!")

    @_leavegame.error
    async def _leavegame_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Das hier ist kein Unterhaltungschannel, hier gibt es keine Verabredungen.")
            logging.warning(
                f"{ctx.author} wollte eine Verabredung abseits eines Unterhaltungschannels verlassen!")


class Games(commands.Cog, name="Games"):
    """
    Klasse für Videospielinhalte (eigentlich nicht mehr notwendig/vollständig).

    ESAGame:        Zeigt das aktuelle ESA Game auf Twitch an.
    OWHeld:         Generiert einen OW Helden, supported Rollen und Anzahl.
    """

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
            logging.info(f"{ctx.author} hat das ESA Game abgefragt.")
        except IndexError:
            # Username does not exist or Username is wrong, greetings to Schnabeltier
            logging.error("ESA Channel nicht gefunden. Wurde er gelöscht?!")
        except json.decoder.JSONDecodeError:
            logging.error("Die Twitch API ist nicht erreichbar.")

    @commands.command(name="OwHeld", aliases=["owhero", "owheld", "OWHeld", "RndHeld", "RndOwHeld", "RndOWHeld", "rndowheld"], brief="Weißt einen zufälligen Helden zu")
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
                f"User {ctx.author} hat sich einen Support aus OW zuweisen lassen.")
        elif role in ["DAMAGE", "DPS", "DMG", "Damage", "dmg", "dps", "Dps"] and number < len(ListOfDPS):
            for _ in range(0, number):
                SelectedHero = random.choice(ListOfDPS)
                ListOfDPS.remove(f"{SelectedHero}")
                SelectedHeros.append(SelectedHero)
                SelectedHerosString = ", ".join(SelectedHeros)
            await ctx.send(f"Folgende Helden wurden ausgewählt: {SelectedHerosString}")
            logging.info(
                f"User {ctx.author} hat sich einen DPS aus OW zuweisen lassen.")
        elif role in ["TANK", "tank", "Tank"] and number < len(ListOfTanks):
            for _ in range(0, number):
                SelectedHero = random.choice(ListOfTanks)
                ListOfTanks.remove(f"{SelectedHero}")
                SelectedHeros.append(SelectedHero)
                SelectedHerosString = ", ".join(SelectedHeros)
            await ctx.send(f"Folgende Helden wurden ausgewählt: {SelectedHerosString}")
            logging.info(
                f"User {ctx.author} hat sich einen Tank aus OW zuweisen lassen.")
        elif role in ["all", "All", "ALL", "alle", "Alle"] and number < len(ListOfAllHeros):
            for _ in range(0, number):
                SelectedHero = random.choice(ListOfAllHeros)
                ListOfAllHeros.remove(f"{SelectedHero}")
                SelectedHeros.append(SelectedHero)
                SelectedHerosString = ", ".join(SelectedHeros)
            await ctx.send(f"Folgende Helden wurden ausgewählt: {SelectedHerosString}")
            logging.info(
                f"User {ctx.author} hat sich einen Helden aus OW zuweisen lassen.")


class Administration(commands.Cog, name="Administration"):
    """
    Die Administrator Klasse, hier werden Teile des Bots verwaltet:

    Cogs:                      Können geladen oder entladen werden.
    Twitch:                    User hinzufügen oder löschen.
    Log:                       Zeigt die neusten 10 Zeilen des Log.
    MC Reboot:                 Startet den MC Server neu.
    """
    global bot

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="mcreboot", aliases=["MCReboot"], brief="Rebootet den MC Server")
    @commands.cooldown(1, 7200, commands.BucketType.user)
    @commands.check(_is_mcsu)
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
            logging.info(f"User {ctx.author} rebooted the Minecraftserver.")

        except json.JSONDecodeError:
            logging.error("Could not load JSON File!", exc_info=True)
        except:
            logging.error(
                "Something went wrong, is the Pi reachable?", exc_info=True)

    @commands.command(name="tw", aliases=["twitch", "Twitch", "TW"], brief="Verwaltet das Twitch File")
    @commands.check(_is_admin)
    async def _twitchmanagement(self, ctx, ChangeArg, Member):
        """
        Verwaltet die Twitch Benachrichtigungen.

        Add: Fügt den User hinzu
        Del: Entfernt den User
        """

        if ChangeArg in ["add", "+"]:
            try:
                TwitchUser = _read_json('Settings.json')
                TwitchMember = {f"{Member}": False}
                TwitchUser['Settings']['TwitchUser'].update(TwitchMember)
                _write_json('Settings.json', TwitchUser)
                await ctx.send(f"{Member} zur Twitchliste hinzugefügt!")
                logging.info(f"User {Member} was added to Twitchlist.")
            except:
                await ctx.send("Konnte User nicht hinzufügen.")
                logging.error(
                    f"User {Member} could not be added.", exc_info=True)
        elif ChangeArg in ["del", "-"]:
            try:
                TwitchUser = _read_json('Settings.json')
                TwitchUser['Settings']['TwitchUser'].pop(f"{Member}")
                _write_json('Settings.json', TwitchUser)
                await ctx.send(f"{Member} wurde aus der Twitchliste entfernt.")
                logging.info(f"User {Member} was removed from Twitchlist.")
            except:
                await ctx.send("Konnte User nicht entfernen.")
                logging.error(
                    f"User {Member} could not be removed.", exc_info=True)

    @commands.command(name="ext", aliases=["Ext", "Extension", "extension"], brief="Verwaltet Extensions")
    @commands.check(_is_admin)
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
    @commands.check(_is_admin)
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

    ### Error Handling for Administrator Cog ###

    @_mcreboot.error
    async def _mcreboot_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Na na, das darfst du nicht! <@248181624485838849> guck dir diesen Schelm an!")
            logging.warning(
                f"{ctx.author} wollte den Minecraftserver dabei darf er oder sie das nicht!")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send("Der Befehl ist aktuell noch im Cooldown.")
            logging.warning(
                f"{ctx.author} wollte den Minecraftserver in 3 Stunden mehrfach neustarten!")

    @_twitchmanagement.error
    async def _twitchmanagement_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Na na, das darf nur der Admin! <@248181624485838849>, hier möchte jemand in die Twitchliste oder aus der Twitchliste entfernt werden!")
            logging.warning(f"{ctx.author} wollte die Twitchliste bearbeiten!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Hier fehlte der User oder der Parameter!")

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
            logging.error("Die Twitch API ist nicht erreichbar.")
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
                    f"{Displayname} ging live auf Twitch! Twitch Benachrichtigung gesendet!")
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
                            f"{Displayname} ging live auf Twitch! Twitch Benachrichtigung gesendet, da älter als 60min oder nicht vorhanden!")
                else:
                    await bot.get_channel(703530328836407327).send(content=f"**{Displayname}** ist live! Gestreamt wird {game['name']}!", embed=embed)
                    logging.info(
                        f"{Displayname} ging live auf Twitch! Twitch Benachrichtigung gesendet!")

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
            logging.info(f"Treffen im Channel {reminder} gestartet!")
            FoundList.append(reminder)
    if FoundList:
        for reminder in FoundList:
            groups["Settings"]["Groups"].pop(f'{reminder}')
        _write_json('Settings.json', groups)


@tasks.loop(minutes=30)
async def MuellReminder():
    """
    Prüft alle 30min ob morgen Müll ist und sendet eine Nachricht an mich per Discord DM,
    dabei wird eine CSV Datei eingelesen und durchiteriert.
    """

    MyDiscordUser = await bot.fetch_user(248181624485838849)
    TodayAtFivePM = datetime.now().replace(
        hour=17, minute=00, second=00, microsecond=00)
    TodayAtFiveAndAHalfPM = datetime.now().replace(
        hour=17, minute=32, second=00, microsecond=00)
    if datetime.now() >= TodayAtFivePM and datetime.now() <= TodayAtFiveAndAHalfPM:
        tomorrowNow = datetime.today() + timedelta(days=1)
        tomorrowClean = tomorrowNow.replace(
            hour=00, minute=00, second=00, microsecond=00)
        MuellListe = pd.read_csv('Muell.csv', sep=";")
        for entry in MuellListe["Schwarze Tonne"].dropna():
            EntryDate = pd.to_datetime(entry[3:], dayfirst=True)
            if tomorrowClean == EntryDate:
                await MyDiscordUser.send(f"Die nächste schwarze Tonne ist morgen am: {entry}")
                logging.info(
                    f"Reminder für die schwarze Tonne am {entry} gesendet!")
        for entry in MuellListe["Blaue Tonne"].dropna():
            EntryDate = pd.to_datetime(entry[3:], dayfirst=True)
            if tomorrowClean == EntryDate:
                await MyDiscordUser.send(f"Die nächste blaue Tonne ist morgen am: {entry}")
                logging.info(
                    f"Reminder für die blaue Tonne am {entry} gesendet!")
        for entry in MuellListe["Gelbe Saecke"].dropna():
            EntryDate = pd.to_datetime(entry[3:], dayfirst=True)
            if tomorrowClean == EntryDate:
                await MyDiscordUser.send(f"Die nächsten gelben Säcke sind morgen am: {entry}")
                logging.info(
                    f"Reminder für den gelben Sack am {entry} gesendet!")


@tasks.loop(hours=3)
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
                f"{EndedOffer} aus den gratis Epic Games entfernt, da abgelaufen!")
        _write_json('Settings.json', FreeGamesList)

    EpicStoreURL = 'https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=de&country=DE&allowCountries=DE'

    RequestFromEpic = requests.get(EpicStoreURL)

    JSONFromEpicStore = RequestFromEpic.json()
    if JSONFromEpicStore:
        for FreeGame in JSONFromEpicStore['data']['Catalog']['searchStore']['elements']:
            if FreeGame['promotions'] is not None and FreeGame['promotions']['promotionalOffers'] != []:
                offers = FreeGame['promotions']['promotionalOffers']
                for offer in offers:

                    FreeGameObject = {
                        f"{FreeGame['title']}": {
                            "startDate": offer['promotionalOffers'][0]['startDate'],
                            "endDate": offer['promotionalOffers'][0]['endDate'],
                        }
                    }

                    try:

                        if not FreeGamesList:
                            FreeGamesList['Settings']['FreeEpicGames'].update(
                                FreeGameObject)
                            _write_json('Settings.json', FreeGameObject)
                            EndOfOffer = offer['promotionalOffers'][0]['endDate']
                            EndDateOfOffer = parser.parse(EndOfOffer).date()

                            for index in range(len(FreeGame['keyImages'])):
                                if FreeGame['keyImages'][index]['type'] == "Thumbnail":
                                    EpicImageURL = FreeGame['keyImages'][index]['url']
                                    break

                            EpicImage = requests.get(EpicImageURL)
                            if EpicImage.status_code == 200:
                                EpicImagePath = f"{NumberOfEpicFiles +1}_epic.jpg"
                                with open(f'epic/{EpicImagePath}', 'wb') as write_file:
                                    write_file.write(EpicImage.content)
                            if EpicImagePath:
                                await bot.get_channel(539553203570606090).send(f"Neues Gratis Epic Game: {FreeGame['title']}! Noch verfügbar bis {EndDateOfOffer.day}.{EndDateOfOffer.month}.{EndDateOfOffer.year}!", file=discord.File(f"epic/{EpicImagePath}"))
                            else:
                                await bot.get_channel(539553203570606090).send(f"Neues Gratis Epic Game: {FreeGame['title']}! Noch verfügbar bis {EndDateOfOffer.day}.{EndDateOfOffer.month}.{EndDateOfOffer.year}!")

                            logging.info(
                                f"{FreeGame['title']} wurde zu den gratis Epic Games hinzugefügt!")
                        else:
                            if FreeGame['title'] in FreeGamesList['Settings']['FreeEpicGames'].keys():
                                pass
                            else:
                                FreeGamesList['Settings']['FreeEpicGames'].update(
                                    FreeGameObject)
                                _write_json('Settings.json', FreeGamesList)
                                EndOfOffer = offer['promotionalOffers'][0]['endDate']
                                EndDateOfOffer = parser.parse(
                                    EndOfOffer, dayfirst=True).date()

                                for index in range(len(FreeGame['keyImages'])):
                                    if FreeGame['keyImages'][index]['type'] == "Thumbnail":
                                        EpicImageURL = FreeGame['keyImages'][index]['url']
                                        break

                                EpicImage = requests.get(EpicImageURL)
                                if EpicImage.status_code == 200:
                                    EpicImagePath = f"{NumberOfEpicFiles +1}_epic.jpg"
                                    with open(f'epic/{EpicImagePath}', 'wb') as write_file:
                                        write_file.write(EpicImage.content)

                                if EpicImagePath:
                                    await bot.get_channel(539553203570606090).send(f"Neues Gratis Epic Game: {FreeGame['title']}! Noch verfügbar bis {EndDateOfOffer.day}.{EndDateOfOffer.month}.{EndDateOfOffer.year}!", file=discord.File(f"epic/{EpicImagePath}"))
                                else:
                                    await bot.get_channel(539553203570606090).send(f"Neues Gratis Epic Game: {FreeGame['title']}! Noch verfügbar bis {EndDateOfOffer.day}.{EndDateOfOffer.month}.{EndDateOfOffer.year}!")
                                logging.info(
                                    f"{FreeGame['title']} wurde der Liste der gratis Epic Games hinzugefügt!")

                    except json.decoder.JSONDecodeError:
                        FreeGamesList['Settings']['FreeEpicGames'] = {}
                        FreeGamesList['Settings']['FreeEpicGames'].update(
                            FreeGameObject)
                        _write_json('Settings.json', FreeGamesList)

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
    if not MuellReminder.is_running():
        MuellReminder.start()
    if not GetFreeEpicGames.is_running():
        GetFreeEpicGames.start()
    RefreshMemes()


@bot.event
async def on_message(message):
    """
    Was bei einer Nachricht passieren soll.
    """
    if message.author == bot.user:
        return

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
            f"{error}, {ctx.author} möchte wohl einen neuen Befehl.")

bot.run(TOKEN)
