import time
from datetime import datetime, timedelta
import json
import os
import random
import discord
from discord.ext import commands, tasks
from discord.ext.commands import context
import requests
from bs4 import BeautifulSoup
import paramiko
import uwuify


# To show the whole table, currently unused
# pd.set_option('display.max_rows', None)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=('!'), intents=intents)

### Functions ###


def RequestTwitchToken():
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


def _is_mcsu(ctx: context.Context):
    return ctx.author.id in [247117682875432960, 232561052573892608, 257249704872509441, 248181624485838849]

def _is_owchannel(ctx):
    return ctx.message.channel.id == 554390037811167363


def _is_nouwuchannel(ctx):
    return ctx.message.channel.category_id != 539547423782207488 and ctx.message.channel.id != 539549544585756693 and ctx.message.channel.id != 539546796939149334


def _is_gamechannel(ctx):
    if isinstance(ctx.channel, discord.channel.DMChannel):
        return False
    else:
        return ctx.message.channel.category_id == 539553136222666792


def _is_admin(ctx):
    return ctx.author.id == 248181624485838849


def _read_json(FileName):
    with open(f'{FileName}', 'r') as JsonRead:
        return json.load(JsonRead)


def _write_json(FileName, Content):
    with open(f'{FileName}', 'w') as JsonWrite:
        json.dump(Content, JsonWrite)

### General Settings ###


with open("TOKEN.json", "r") as TOKENFILE:
    TOKENDATA = json.load(TOKENFILE)
    TOKEN = TOKENDATA['DISCORD_TOKEN']
    TWITCH_CLIENT_ID = TOKENDATA['TWITCH_CLIENT_ID']
    TWITCH_CLIENT_SECRET = TOKENDATA['TWITCH_CLIENT_SECRET']
    if 'TWITCH_TOKEN' in TOKENDATA.keys() and 'TWITCH_TOKEN_EXPIRES' in TOKENDATA.keys():
        TWITCH_TOKEN = TOKENDATA['TWITCH_TOKEN']
        TWITCH_TOKEN_EXPIRES = TOKENDATA['TWITCH_TOKEN_EXPIRES']
    else:
        RequestTwitchToken()

### Commands and Cogs Section ###


class Counter(commands.Cog, name="Counter"):

    @commands.group(name="pun",  aliases=["Pun"], invoke_without_command=True, brief="Erhöht den Pun Counter")
    async def _puncounter(self, ctx):
        data = _read_json('Botcount.json')
        data['Puns'] = data['Puns'] + 1
        PunNumber = data['Puns']
        _write_json('Botcount.json', data)
        await ctx.send(f"Es wurde bereits {PunNumber} Mal ein Gagfeuerwerk gezündet!")

    @_puncounter.command(name="show", aliases=["sh", "-s"], brief="Zeigt den aktuellen Puncount")
    async def _show_puncounter(self, ctx):
        data = _read_json('Botcount.json')
        await ctx.send(f"Bereits {data['Puns']} Gagfeuerwerke wurden gezündet!")

    @commands.group(name="mobbing",  aliases=["Mobbing", "Hasssprech", "hasssprech"], invoke_without_command=True, brief="Erhöht Hasssprech Counter")
    async def _mobbingcounter(self, ctx):
        data = _read_json('Botcount.json')
        data['Mobbing'] = int(data['Mobbing']) + 1
        _write_json('Botcount.json', data)
        MobbingNumber = data['Mobbing']
        await ctx.send(f"Das ist Hasssprech! {MobbingNumber} Mal wurde schon Hasssprech betrieben! Pfui!")

    @_mobbingcounter.command(name="show", aliases=["sh", "-s"], brief="Zeigt den aktuellen Hasssprech Counter")
    async def _show_mobbingcounter(self, ctx):
        data = _read_json('Botcount.json')
        await ctx.send(f"Auf dem Discord wurde bereits {data['Mobbing']} Mal Hasssprech betrieben! Pfui!")

    @commands.group(name="leak", aliases=["Leak"], invoke_without_command=True, brief="Erhöht den Leak Counter")
    async def _leakcounter(self, ctx):
        data = _read_json('Botcount.json')
        data['Leak'] = int(data['Leak']) + 1
        _write_json('Botcount.json', data)
        LeakNumber = data['Leak']
        await ctx.send(f"Da hat wohl jemand nicht aufgepasst... Es wurde bereits {LeakNumber} Mal geleakt! Obacht!")

    @_leakcounter.command(name="show", aliases=["sh", "-s"], brief="Zeigt den aktuellen Leak Counter")
    async def _show_leakcounter(self, ctx):
        data = _read_json('Botcount.json')
        await ctx.send(f"Bisher wurden {data['Leak']} Mal kritische Informationen geleakt.<:eyes:825006453936750612>")

    @commands.group(name="salz", aliases=["Salz"], invoke_without_command=True, brief="Erhöht den Salz Counter")
    async def _salzcounter(self, ctx):
        data = _read_json('Botcount.json')
        data['Salz'] = int(data['Salz']) + 1
        _write_json('Botcount.json', data)
        SalzNumber = data['Salz']
        await ctx.send(f"Man konnte sich schon {SalzNumber} Mal nicht beherrschen! Böse Salzstreuer hier!<:salt:826091230156161045>")

    @_salzcounter.command(name="show", aliases=["sh", "-s"], brief="Zeigt den aktuellen Salz Counter")
    async def _show_salzcounter(self, ctx):
        data = _read_json('Botcount.json')
        await ctx.send(f"Bisher war es schon {data['Salz']} Mal salzig auf dem Discord!<:salt:826091230156161045>")


class Fun(commands.Cog, name="Schabernack"):

    @commands.command(name="Pub", aliases=["pub"], brief="Typos...")
    async def _pubtypo(self, ctx):
        await ctx.send(f"Das Discord Pub ist geschlossen, {ctx.author.name}! Du meintest wohl !pun?")

    @commands.command(name="Ehrenmann", aliases=["ehrenmann"], brief="Der erwähnte User ist ein Ehrenmann!")
    async def _ehrenmann(self, ctx, user: commands.MemberConverter):
        await ctx.send(f"{user.mention}, du bist ein gottverdammter Ehrenmann!<:Ehrenmann:762764389384192000>")

    @commands.command(name="testgeheim", aliases=["latestmsgtest"], brief="Super geheim")
    async def _latestmsgtest(self, ctx):
        LastMessages = await ctx.message.channel.history(limit=2).flatten()
        LastMessages.reverse()
        await ctx.send(f"{ctx.author.mention}, die letzte Nachricht hier war {LastMessages[0].content}.")

    @commands.group(name="meme", aliases=["Meme"], invoke_without_command=True, brief="Gibt ein Zufallsmeme aus, kann auch Memes adden")
    @commands.has_permissions(attach_files=True)
    async def _memearchiv(self, ctx):
        RandomMeme = random.choice(next(os.walk("memes/"))[2])
        await ctx.send("Zufalls-Meme!", file=discord.File(f"memes/{RandomMeme}"))

    @_memearchiv.command(name="add", aliases=["+"], brief="Fügt das Meme der oberen Nachricht hinzu")
    async def _addmeme(self, ctx):
        AllFiles = next(os.walk("memes/"))[2]
        NumberOfFiles = len(AllFiles)
        LastMessages = await ctx.message.channel.history(limit=2).flatten()
        LastMessages.reverse()
        for index, meme in enumerate(LastMessages[0].attachments):
            if meme.filename.lower().endswith(('gif', 'jpg', 'png', 'jpeg')):
                await meme.save(f"memes/{NumberOfFiles + index}_{meme.filename}")
            else:
                pass
            await ctx.send("Memes hinzugefügt.")

    @_memearchiv.command(name="collect", aliases=["coll", "Collect", "Coll"], brief="Sammelt das Meme per ID ein")
    async def _collmeme(self, ctx, Message: commands.MessageConverter):
        AllFiles = next(os.walk("memes/"))[2]
        NumberOfFiles = len(AllFiles)
        for index, meme in enumerate(Message.attachments):
            if meme.filename.lower().endswith(('gif', 'jpg', 'png', 'jpeg')):
                await meme.save(f"memes/{NumberOfFiles + index}_{meme.filename}")
            else:
                pass
            await ctx.send("Dieses spicy Meme wurde eingesammelt.", file=await meme.to_file())

    @commands.Cog.listener("on_message")
    @commands.check(_is_nouwuchannel)
    async def _uwumsg(self, message):
        if message.author == bot.user:
            return
        if random.randint(0, 50) == 1:
            LastMessageContent = message.content
            flags = uwuify.SMILEY | uwuify.YU
            await message.channel.send(f"{uwuify.uwu(LastMessageContent, flags=flags)} UwU")

    @commands.command(name="uwu", aliases=["UwU", "Uwu", "uWu", "uWU"], brief="Weebt die Message UwU")
    @commands.check(_is_nouwuchannel)
    async def _uwuthis(self, ctx):
        if ctx.message.author == bot.user:
            return
        LastMessages = await ctx.message.channel.history(limit=2).flatten()
        LastMessages.reverse()
        flags = uwuify.SMILEY | uwuify.YU
        await ctx.send(uwuify.uwu(LastMessages[0].content, flags=flags))


class Corona(commands.Cog, name="Corona"):

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


class Meetings(commands.Cog, name="Meetings"):

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
            groups = _read_json('GROUPS.json')

            if not groups:
                groups.update(group)
                _write_json('GROUPS.json', groups)
                await ctx.send("Die Spielrunde wurde eröffnet!")
            else:
                if ctx.message.channel.name in groups.keys():
                    await ctx.send(f"{ctx.author.name}, hier ist schon eine Spielrunde geplant. Joine einfach mit !join")
                else:
                    groups.update(group)
                    _write_json('GROUPS.json', groups)
                    await ctx.send("Die Spielrunde wurde eröffnet!")
        except json.decoder.JSONDecodeError:
            groups = {}
            groups.update(group)
            _write_json('GROUPS.json', groups)
            await ctx.send("Die Spielrunde wurde eröffnet!")

    @commands.command(name="join", aliases=["Join"], brief="Tritt einer Verabredung bei")
    @commands.check(_is_gamechannel)
    async def _joingame(self, ctx):
        CurrentChannel = ctx.message.channel.name
        groups = _read_json('GROUPS.json')

        if ctx.message.channel.name in groups.keys() and ctx.message.author.mention in groups[f"{CurrentChannel}"]["members"]:
            await ctx.send(f"{ctx.message.author.name}, du bist bereits als Teilnehmer im geplanten Spiel.")
        elif ctx.message.channel.name in groups.keys() and f"{ctx.message.author.mention}" not in groups[f"{CurrentChannel}"]["members"]:
            groups[f"{CurrentChannel}"]["members"].append(
                f"{ctx.message.author.mention}")
            await ctx.send(f"{ctx.author.mention}, du wurdest dem Spiel hinzugefügt.")
            _write_json('GROUPS.json', groups)
        else:
            await ctx.send("In diesem Channel wurde noch kein Spiel geplant.")

    @commands.command(name="UpdateGame", aliases=["updategame", "Updategame", "updateGame"], brief="Verschiebt das Spiel auf die gewünschte Zeit")
    @commands.check(_is_gamechannel)
    async def _movegame(self, ctx, timearg):
        CurrentChannel = ctx.message.channel.name
        groups = _read_json('GROUPS.json')

        if ctx.message.channel.name in groups.keys() and ctx.message.author.mention == groups[f"{CurrentChannel}"]["owner"]:
            try:
                CurrentDate = datetime.now()
                GameTime = datetime.strptime(timearg, "%H:%M").time()
                GameDateTime = datetime.combine(CurrentDate, GameTime)
                GameDateTimeTimestamp = GameDateTime.timestamp()
            except ValueError:
                await ctx.send("Na na, das ist keine Uhrzeit!")
                return

            groups[f"{CurrentChannel}"]["time"] = GameDateTimeTimestamp
            _write_json('GROUPS.json', groups)
            await ctx.send(f"Die Uhrzeit der Verabredung wurde auf {timearg} geändert.")
        elif ctx.message.channel.name in groups.keys() and ctx.message.author.mention != groups[f"{CurrentChannel}"]["owner"]:
            await ctx.send("Na na, du bist nicht der Besitzer dieser Verabredung! Frag bitte den Besitzer, ob er es verschiebt!")
        elif ctx.message.channel.name not in groups.keys():
            await ctx.send("Hier gibt es noch keine Verabredung. Starte doch eine!")

    @commands.command(name="RemGame", aliases=["remgame"], brief="Löscht die Verabredung")
    @commands.check(_is_gamechannel)
    async def _gameremover(self, ctx):
        CurrentChannel = ctx.message.channel.name
        groups = _read_json('GROUPS.json')
        if ctx.message.channel.name in groups.keys() and ctx.message.author.mention == groups[f"{CurrentChannel}"]["owner"]:
            groups.pop(CurrentChannel)
            _write_json('GROUPS.json', groups)
            await ctx.send("Die Verabredung in diesem Channel wurde gelöscht.")
        elif ctx.message.channel.name in groups.keys() and ctx.message.author.mention != groups[f"{CurrentChannel}"]["owner"]:
            await ctx.send("Na na, du bist nicht der Besitzer dieser Verabredung! Frag bitte den Besitzer, ob er diese löscht!")
        elif ctx.message.channel.name not in groups.keys():
            await ctx.send("Hier gibt es noch keine Verabredung. Starte doch eine!")

    ## Error Handling for Meetings Cog ###

    @_playgame.error
    async def _playgame_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Bitte gib eine Uhrzeit an!")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("Das hier ist kein Unterhaltungschannel, hier kann man sich nicht verabreden.")

    @_joingame.error
    async def _joingame_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Das hier ist kein Unterhaltungschannel, hier kann man sich nicht verabreden.")


class Games(commands.Cog, name="Games"):

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
        except IndexError:
            # Username does not exist or Username is wrong, greetings to Schnabeltier
            print("Der ESA Kanal ist weg. Gelöscht?!")
        except json.decoder.JSONDecodeError:
            print("Twitch API scheint nicht erreichbar.")

    @commands.command(name="OwHeld", aliases=["owhero", "owheld", "OWHeld", "RndHeld", "RndOwHeld", "RndOWHeld", "rndowheld"], brief="Weißt einen zufälligen Helden zu")
    @commands.check(_is_owchannel)
    async def _randomowhero(self, ctx, *args):
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
        elif role in ["DAMAGE", "DPS", "DMG", "Damage", "dmg", "dps", "Dps"] and number < len(ListOfDPS):
            for _ in range(0, number):
                SelectedHero = random.choice(ListOfDPS)
                ListOfDPS.remove(f"{SelectedHero}")
                SelectedHeros.append(SelectedHero)
                SelectedHerosString = ", ".join(SelectedHeros)
            await ctx.send(f"Folgende Helden wurden ausgewählt: {SelectedHerosString}")
        elif role in ["TANK", "tank", "Tank"] and number < len(ListOfTanks):
            for _ in range(0, number):
                SelectedHero = random.choice(ListOfTanks)
                ListOfTanks.remove(f"{SelectedHero}")
                SelectedHeros.append(SelectedHero)
                SelectedHerosString = ", ".join(SelectedHeros)
            await ctx.send(f"Folgende Helden wurden ausgewählt: {SelectedHerosString}")
        elif role in ["all", "All", "ALL", "alle", "Alle"] and number < len(ListOfAllHeros):
            for _ in range(0, number):
                SelectedHero = random.choice(ListOfAllHeros)
                ListOfAllHeros.remove(f"{SelectedHero}")
                SelectedHeros.append(SelectedHero)
                SelectedHerosString = ", ".join(SelectedHeros)
            await ctx.send(f"Folgende Helden wurden ausgewählt: {SelectedHerosString}")


class Administration(commands.Cog, name="Administration"):
    global bot

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="mcreboot", aliases=["MCReboot"], brief="Rebootet den MC Server")
    @commands.check(_is_mcsu)
    async def _mcreboot(self, ctx):
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
            print(f"{ctx.author.name} hat den Minecraft Server neugestartet.")
            ssh.close()

            await ctx.send(f"{ctx.author.name} hat den Minecraft Server neugestartet.")

        except json.JSONDecodeError:
            print("Konnte das Minecraft JSON File nicht laden...")
        except:
            print("Etwas anderes ist schief gelaufen... Ist der Minecraft Pi erreichbar?")

    @commands.command(name="tw", aliases=["twitch", "Twitch", "TW"], brief="Verwaltet das Twitch File")
    @commands.check(_is_admin)
    async def _twitchmanagement(self, ctx, ChangeArg, Member):
        if ChangeArg in ["add", "+"]:
            try:
                with open('TWITCHUSER.json', 'r+') as TwitchFile:
                    TwitchUser = json.load(TwitchFile)
                    TwitchMember = {f"{Member}": False}
                    TwitchUser.update(TwitchMember)
                    # Seek is enough since the new String is longer otherwise TwitchFile.truncate() would be needed
                    TwitchFile.seek(0)
                    json.dump(TwitchUser, TwitchFile)
                await ctx.send(f"{Member} zur Twitchliste hinzugefügt!")
            except:
                await ctx.send("Konnte User nicht hinzufügen.")
        elif ChangeArg in ["del", "-"]:
            try:
                TwitchUser = _read_json('TWITCHUSER.json')
                TwitchUser.pop(f"{Member}")
                _write_json('TWITCHUSER.json', TwitchUser)
                await ctx.send(f"{Member} wurde aus der Twitchliste entfernt.")
            except:
                await ctx.send("Konnte User nicht entfernen.")

    @commands.command(name="ext", aliases=["Ext", "Extension", "extension"], brief="Verwaltet Extensions")
    @commands.check(_is_admin)
    async def _extensions(self, ctx, ChangeArg, extension):
        if ChangeArg == "load":
            bot.load_extension(f"cogs.{extension}")
            await ctx.send(f"Extension {extension} wurde geladen und ist jetzt einsatzbereit.")
        elif ChangeArg == "unload":
            bot.unload_extension(f"cogs.{extension}")
            await ctx.send(f"Extension {extension} wurde entfernt und ist nicht mehr einsatzfähig.")

    ### Error Handling for Administrator Cog ###

    @_mcreboot.error
    async def _mcreboot_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Na na, das darfst du nicht! <@248181624485838849> guck dir diesen Schelm an!")

    @_twitchmanagement.error
    async def _twitchmanagement_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Na na, das darf nur der Admin! <@248181624485838849>, hier möchte jemand in die Twitchliste oder aus der Twitchliste entfernt werden!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Hier fehlte der User oder der Parameter!")


### Add Cogs in bot file ###

bot.add_cog(Counter(bot))
bot.add_cog(Fun(bot))
bot.add_cog(Corona(bot))
bot.add_cog(Meetings(bot))
bot.add_cog(Games(bot))
bot.add_cog(Administration(bot))

### Tasks Section ###


@tasks.loop(seconds=60)
async def TwitchLiveCheck():
    if datetime.timestamp(datetime.now()) > TWITCH_TOKEN_EXPIRES:
        RequestTwitchToken()

    TWITCHUSERNAMES = _read_json('TWITCHUSER.json')

    for USER, LASTSTATE in TWITCHUSERNAMES.items():

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
            print("Twitch API scheint nicht erreichbar.")
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
            else:
                channel = bot.get_channel(703530328836407327)
                NotificationTime = datetime.utcnow() - timedelta(minutes=60)
                LastMessages = await channel.history(after=NotificationTime).flatten()
                if LastMessages:
                    LastMessages.reverse()
                    for message in LastMessages:
                        if message.content.startswith(f"**{Displayname}**") is True:
                            break
                        elif message.content.startswith(f"**{Displayname}**") is not False and message == LastMessages[-1]:
                            await bot.get_channel(703530328836407327).send(content=f"**{Displayname}** ist live! Gestreamt wird {game['name']}!", embed=embed)
                        else:
                            pass
                else:
                    await bot.get_channel(703530328836407327).send(content=f"**{Displayname}** ist live! Gestreamt wird {game['name']}!", embed=embed)

        if LASTSTATE is not data['is_live']:
            TWITCHUSERNAMES[USER] = data['is_live']
            _write_json('TWITCHUSER.json', TWITCHUSERNAMES)


@tasks.loop(seconds=60)
async def GameReminder():
    CurrentTime = datetime.timestamp(datetime.now())
    groups = _read_json('GROUPS.json')
    FoundList = []
    for reminder in groups.keys():
        if CurrentTime > groups[f"{reminder}"]["time"]:
            Remindchannel = bot.get_channel(groups[f"{reminder}"]["id"])
            ReminderMembers = ", ".join(groups[f"{reminder}"]["members"])
            await Remindchannel.send(f" Das Spiel geht los! Mit dabei sind: {ReminderMembers}")
            FoundList.append(reminder)
    if FoundList:
        for reminder in FoundList:
            groups.pop(f'{reminder}')
        _write_json('GROUPS.json', groups)

### Bot Events ###


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    print(f"Bot Startup Time: {datetime.now()}")
    for File in os.listdir('./cogs'):
        if File.endswith('.py') and f"cogs.{File[:-3]}" not in bot.extensions.keys():
            bot.load_extension(f"cogs.{File[:-3]}")
            print(f"Extension {File[:-3]} geladen.")
    if not TwitchLiveCheck.is_running():
        TwitchLiveCheck.start()
    if not GameReminder.is_running():
        GameReminder.start()


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    # This line needs to be added so the commands are actually processed
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        print(f"{error}, {ctx.author} möchte wohl einen neuen Befehl.")

bot.run(TOKEN)
