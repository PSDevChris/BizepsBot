import time
from datetime import datetime, timedelta
import json
import os
import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import pandas as pd
from dateutil.parser import parse
import paramiko


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


def _isgeneral(channelid):
    """
    docstring
    """
    return channelid == 539546796939149334


def _is_mcsu(ctx):
    return ctx.author.id in [247117682875432960, 232561052573892608, 257249704872509441, 248181624485838849]


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

### Commands Section ###


@bot.command(name="pun", aliases=["Pun"])
async def _puncounter(ctx, ChangeArg=""):
    if ChangeArg in ["add", "+"]:
        data = _read_json('Botcount.json')
        data['Puns'] = data['Puns'] + 1
        PunNumber = data['Puns']
        _write_json('Botcount.json', data)
        await ctx.send(f"Es wurde bereits {PunNumber} Mal ein Gagfeuerwerk gezündet!")
    else:
        data = _read_json('Botcount.json')
        await ctx.send(f"Bereits {data['Puns']} Gagfeuerwerke wurden gezündet!")


@bot.command(name="mobbing", aliases=["Mobbing", "Hasssprech", "hasssprech"])
async def _mobbingcounter(ctx, ChangeArg=""):
    if ChangeArg in ["add", "+"]:
        data = _read_json('Botcount.json')
        data['Mobbing'] = int(data['Mobbing']) + 1
        _write_json('Botcount.json', data)
        MobbingNumber = data['Mobbing']
        await ctx.send(f"Das ist Hasssprech! {MobbingNumber} Mal wurde schon Hasssprech betrieben! Pfui!")
    else:
        data = _read_json('Botcount.json')
        await ctx.send(f"Auf dem Discord wurde bereits {data['Mobbing']} Mal Hasssprech betrieben! Pfui!")


@bot.command(name="Leak", aliases=["leak"])
async def _leakcounter(ctx, ChangeArg=""):
    if ChangeArg in ["add", "+"]:
        data = _read_json('Botcount.json')
        data['Leak'] = int(data['Leak']) + 1
        _write_json('Botcount.json', data)
        LeakNumber = data['Leak']
        await ctx.send(f"Da hat wohl jemand nicht aufgepasst... Es wurde bereits {LeakNumber} Mal geleakt! Obacht!")
    else:
        data = _read_json('Botcount.json')
        await ctx.send(f"Bisher wurden {data['Leak']} Mal kritische Informationen geleakt.<:eyes:825006453936750612>")


@bot.command(name="Salz", aliases=["salz"])
async def _salzcounter(ctx, ChangeArg=""):
    if ChangeArg in ["add", "+"]:
        data = _read_json('Botcount.json')
        data['Salz'] = int(data['Salz']) + 1
        _write_json('Botcount.json', data)
        SalzNumber = data['Salz']
        await ctx.send(f"Man konnte sich schon {SalzNumber} Mal nicht beherrschen! Böse Salzstreuer hier!<:salt:826091230156161045>")
    else:
        data = _read_json('Botcount.json')
        await ctx.send(f"Bisher war es schon {data['Salz']} Mal salzig auf dem Discord!<:salt:826091230156161045>")


@bot.command(name="Pub", aliases=["pub"])
async def _pubtypo(ctx):
    await ctx.send(f"Das Discord Pub ist geschlossen, {ctx.author.name}! Du meintest wohl !pun?")


@bot.command(name="Ehrenmann", aliases=["ehrenmann"])
async def _ehrenmann(ctx):
    await ctx.send(f"{ctx.message.mentions[0].mention}, du bist ein gottverdammter Ehrenmann!<:Ehrenmann:762764389384192000>")


@bot.command(name="testgeheim", aliases=["latestmsgtest"])
async def _latestmsgtest(ctx):
    channel = bot.get_channel(ctx.message.channel.id)
    LastMessages = await channel.history(limit=2).flatten()
    LastMessages.reverse()
    await ctx.send(f"{ctx.author.mention}, die letzte Nachricht hier war {LastMessages[0].content}.")


@bot.command(name="Corona", aliases=["corona", "covid", "COVID", "Covid"])
async def _coronazahlen(ctx):
    CORONA_URL = "https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Fallzahlen.html"
    CORONA_PAGE = requests.get(CORONA_URL)
    CORONA_RESULT = BeautifulSoup(CORONA_PAGE.content, "html.parser")
    CORONA_TABLE = CORONA_RESULT.find("table")
    CORONA_ROWS = CORONA_TABLE.find_all("strong")
    CORONA_CASES_YESTERDAY = CORONA_ROWS[2].text
    CORONA_CASES_WEEK = CORONA_ROWS[3].text
    await ctx.send(f"Seit gestern gab es {CORONA_CASES_YESTERDAY} neue COVID-19 Fälle, in den letzten 7 Tagen waren es {CORONA_CASES_WEEK} Fälle\U0001F637")


@bot.command(name="game", aliases=["Game"])
@commands.check(_is_gamechannel)
async def _playgame(ctx, timearg):

    CurrentDate = datetime.now()
    try:
        GameTime = datetime.strptime(timearg, "%H:%M").time()
        GameDateTime = datetime.combine(CurrentDate, GameTime)
        GameDateTimeTimestamp = GameDateTime.timestamp()
    except ValueError:
        await ctx.send("Na na, das ist keine Uhrzeit!")
        return

    group = {
        "channel": ctx.message.channel.id,
        "time": GameDateTimeTimestamp,
        "members": [f"{ctx.message.author.mention}"]
    }

    try:
        with open('GROUPS.json', 'r') as read_file:
            groups = json.load(read_file)

        if not groups:
            groups.append(group)
            with open('GROUPS.json', 'w') as write_file:
                json.dump(groups, write_file)
            await ctx.send("Die Spielrunde wurde eröffnet!")
        else:
            for team in groups:
                if ctx.message.channel.id == team["channel"]:
                    await ctx.send(f"{ctx.author.name}, hier ist schon eine Spielrunde geplant. Joine einfach mit !join")
                else:
                    if team == groups[-1]:
                        groups.append(group)
                        with open('GROUPS.json', 'w') as write_file:
                            json.dump(groups, write_file)
                        await ctx.send("Die Spielrunde wurde eröffnet!")
                    else:
                        continue
    except json.decoder.JSONDecodeError:
        groups = []
        groups.append(group)
        with open('GROUPS.json', 'w') as write_file:
            json.dump(groups, write_file)
        await ctx.send("Die Spielrunde wurde eröffnet!")


@bot.command(name="join", aliases=["Join"])
@commands.check(_is_gamechannel)
async def _joingame(ctx):
    with open('GROUPS.json', 'r') as read_file:
        groups = json.load(read_file)

    for group in groups:
        if ctx.message.channel.id == group["channel"] and ctx.message.author.mention in group["members"]:
            await ctx.send(f"{ctx.message.author.name}, du bist bereits als Teilnehmer im geplanten Spiel.")
        elif ctx.message.channel.id == group["channel"] and f"{ctx.message.author.mention}" not in group["members"]:
            FoundIndex = groups.index(group)
            groups[FoundIndex]["members"].append(
                f"{ctx.message.author.mention}")
            await ctx.send(f"{ctx.author.mention}, du wurdest dem Spiel hinzugefügt.")
        else:
            if group == groups[-1]:
                await ctx.send("In diesem Channel wurde noch kein Spiel geplant.")
            else:
                continue
    with open('GROUPS.json', 'w') as write_file:
        json.dump(groups, write_file)


@bot.command(name="ESAGame", aliases=["esagame"])
async def _esagame(ctx):
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


@bot.command(name="mcreboot", aliases=["MCReboot"])
@commands.check(_is_mcsu)
async def _mcreboot(ctx):
    try:
        with open("MC_DATA.json", "r") as MCFILE:
            MCDATA = json.load(MCFILE)
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


@bot.command(name="tw", aliases=["twitch", "Twitch", "TW"])
@commands.check(_is_admin)
async def _twitchmanagement(ctx, ChangeArg, Member):
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
            with open('TWITCHUSER.json', 'r') as TwitchFile:
                TwitchUser = json.load(TwitchFile)
                TwitchUser.pop(f"{Member}")
            with open("TWITCHUSER.json", "w") as write_file:
                json.dump(TwitchUser, write_file)
            await ctx.send(f"{Member} wurde aus der Twitchliste entfernt.")
        except:
            await ctx.send("Konnte User nicht entfernen.")


@bot.command(name="RemGame", aliases=["remgame"])
@commands.check(_is_admin)
async def _gameremover(ctx):
    with open('GROUPS.json', 'r') as read_file:
        groups = json.load(read_file)
    CurrentChannel = ctx.message.channel.id
    groups[:] = [dict for dict in groups if dict.get(
        'channel') != CurrentChannel]
    with open("GROUPS.json", "w") as write_file:
        json.dump(groups, write_file)
    await ctx.send("Die Verabredung in diesem Channel wurde (sofern vorhanden) gelöscht.")

@bot.command(name="ext", aliases=["Ext", "Extension", "extension"])
@commands.check(_is_admin)
async def _extensions(ctx, ChangeArg, extension):
    if ChangeArg == "load":
        bot.load_extension(f"cogs.{extension}")
        await ctx.send(f"Extension {extension} wurde geladen und ist jetzt einsatzbereit.")
    elif ChangeArg == "unload":
        bot.unload_extension(f"cogs.{extension}")
        await ctx.send(f"Extension {extension} wurde entfernt und ist nicht mehr einsatzfähig.")

### Tasks Section ###


@tasks.loop(seconds=60)
async def TwitchLiveCheck():
    if datetime.timestamp(datetime.now()) > TWITCH_TOKEN_EXPIRES:
        RequestTwitchToken()

    with open("TWITCHUSER.json", "r") as TWITCHUSER:
        TWITCHUSERNAMES = json.load(TWITCHUSER)

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
                0x772ce8), url=f"https://twitch.tv/{USER}")
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
            with open("TWITCHUSER.json", "w") as write_file:
                json.dump(TWITCHUSERNAMES, write_file)


@tasks.loop(seconds=60)
async def GameReminder():
    FoundIndex = []
    CurrentTime = datetime.timestamp(datetime.now())
    with open('GROUPS.json', 'r') as read_file:
        groups = json.load(read_file)
    for reminder in groups:
        if CurrentTime > reminder["time"]:
            Remindchannel = bot.get_channel(reminder["channel"])
            ReminderMembers = ", ".join(reminder["members"])
            await Remindchannel.send(f" Das Spiel geht los! Mit dabei sind: {ReminderMembers}")
            FoundIndex.append(groups.index(reminder))
    if FoundIndex:
        for index in FoundIndex:
            groups.pop(index)
        with open("GROUPS.json", "w") as write_file:
            json.dump(groups, write_file)


### Bot Events ###

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    print(f"Bot Startup Time: {datetime.now()}")
    for File in os.listdir('./cogs'):
        if File.endswith('.py'):
            bot.load_extension(f"cogs.{File[:-3]}")
            print(f"Extension {File[:-3]} geladen.")
    TwitchLiveCheck.start()
    GameReminder.start()


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    if _isgeneral(message.channel.id) is False:
        # This line needs to be added so the commands are actually processed
        await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        print(f"{error}, {ctx.author} möchte wohl einen neuen Befehl.")


### Error Handling ###

@_playgame.error
async def _playgame_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Bitte gib eine Uhrzeit an!")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("Das hier ist kein Unterhaltungschannel, hier kann man sich nicht verabreden.")


@_joingame.error
async def _joingame_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Das hier ist kein Unterhaltungschannel, hier kann man sich nicht verabreden.")


@_mcreboot.error
async def _mcreboot_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Na na, das darfst du nicht! <@248181624485838849> guck dir diesen Schelm an!")


@_twitchmanagement.error
async def _twitchmanagement_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Na na, das darf nur der Admin! <@248181624485838849>, hier möchte jemand in die Twitchliste oder aus der Twitchliste entfernt werden!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Hier fehlte der User oder der Parameter!")


@_gameremover.error
async def _gameremover_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Na na, das darf nur der Admin! <@248181624485838849>, hier muss ein Reminder gelöscht werden!")

bot.run(TOKEN)
