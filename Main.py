import csv
import datetime
import io
import json
import logging
import os
import zoneinfo
from datetime import timedelta, timezone

import aiohttp
import discord
import requests
from dateutil import parser
from discord.ext import commands, tasks

logging.getLogger(name="discord").setLevel(level=logging.WARNING)
logging.basicConfig(
    format="[%(asctime)s] %(message)s", level=logging.INFO, handlers=[logging.FileHandler(filename=f"./logs/{datetime.datetime.now().date()}_bot.log"), logging.StreamHandler()], encoding="UTF-8"
)


with open("TOKEN.json", mode="r", encoding="UTF8") as Tokenfile:
    Tokenvalues = json.load(Tokenfile)
    SERVER = Tokenvalues["SERVER"]
    TWITCH_TOKEN = Tokenvalues["TWITCH_TOKEN"]
    TWITCH_TOKEN_EXPIRES = Tokenvalues["TWITCH_TOKEN_EXPIRES"]
    TWITCH_CLIENT_ID = Tokenvalues["TWITCH_CLIENT_ID"]
    TWITCH_CLIENT_SECRET = Tokenvalues["TWITCH_CLIENT_SECRET"]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Needed for DM function on alerts

# Remember to remove the debug guild if you want to use it on your server
bot = commands.Bot(debug_guilds=[SERVER], command_prefix=("!"), intents=intents)

bot.Server = SERVER
bot.Twitch_Token = TWITCH_TOKEN
bot.Twitch_Token_Expires = TWITCH_TOKEN_EXPIRES
bot.Twitch_Client_ID = TWITCH_CLIENT_ID
bot.Twitch_Client_Secret = TWITCH_CLIENT_SECRET

### Functions ###


def RequestTwitchToken():
    """
    Beantragt ein neues Twitch Token zur Authentifizierung.
    """
    global TWITCH_TOKEN, TWITCH_TOKEN_EXPIRES

    rTwitchTokenData = requests.post("https://id.twitch.tv/oauth2/token", data={"client_id": TWITCH_CLIENT_ID, "client_secret": TWITCH_CLIENT_SECRET, "grant_type": "client_credentials"}, timeout=30)

    TWITCHTOKENDATA = json.loads(rTwitchTokenData.content)
    TWITCH_TOKEN = TWITCHTOKENDATA["access_token"]
    TWITCH_TOKEN_EXPIRES = datetime.datetime.timestamp(datetime.datetime.now()) + TWITCHTOKENDATA["expires_in"]

    with open("TOKEN.json", encoding="UTF-8") as TokenJsonRead:
        data = json.load(TokenJsonRead)
        data["TWITCH_TOKEN"] = TWITCH_TOKEN
        data["TWITCH_TOKEN_EXPIRES"] = TWITCH_TOKEN_EXPIRES
    with open("TOKEN.json", "w", encoding="UTF-8") as write_file:
        json.dump(data, write_file)
    logging.info("New Twitch Token requested.")


def _read_json(FileName):
    with open(f"{FileName}", "r", encoding="utf-8") as JsonRead:
        return json.load(JsonRead)


def _write_json(FileName, Content):
    with open(f"{FileName}", "w", encoding="utf-8") as JsonWrite:
        json.dump(Content, JsonWrite, indent=4)


def _load_settings_file():
    global bot
    bot.Settings = _read_json("Settings.json")
    logging.info("Settings have been loaded.")
    return bot.Settings


### Permission Checks ###


def _get_banned_users():
    bot.BannedUsers = _read_json("Settings.json")["Settings"]["BannedUsers"]
    return bot.BannedUsers


# Needs to be async for cog checks, command checks etc. work without async


async def _is_banned(ctx: commands.context.Context):
    if str(ctx.author) in bot.BannedUsers:
        logging.info(f"User {ctx.author} wanted to use a command but is banned.")
    return str(ctx.author) not in bot.BannedUsers


### Tasks Section ###


@tasks.loop(seconds=60)
async def TwitchLiveCheck():
    """
    Erneuert den Twitch Token, sofern abgelaufen.
    Prüft jede Minute ob jemand bei Twitch live gegangen ist,
    das Ganze wird in ein JSON File gespeichert, sofern der Livestatus sich geändert hat.
    Zuletzt wird eine Benachrichtigung in meinen oder den Kumpels Channel gepostet.
    """

    if datetime.datetime.timestamp(datetime.datetime.now()) > TWITCH_TOKEN_EXPIRES:
        RequestTwitchToken()

    API_Call = io.StringIO()
    for index, USER in enumerate(bot.Settings["Settings"]["TwitchUser"].keys()):
        if index == 0:
            API_Call.write(f"user_login={USER}")
        else:
            API_Call.write(f"&user_login={USER}")

    try:
        # YOU NEED TO CHANGE THIS IF YOU WANT TO USE YOUR SERVER
        guild = bot.get_guild(SERVER)
        async with (
            aiohttp.ClientSession(headers={"Authorization": f"Bearer {TWITCH_TOKEN}", "Client-Id": f"{TWITCH_CLIENT_ID}"}) as TwitchSession,
            TwitchSession.get(f"https://api.twitch.tv/helix/streams?{API_Call.getvalue()}") as rUserData,
        ):
            API_Call.close()
            if rUserData.status == 200:
                AllTwitchdata = await rUserData.json()
                AllTwitchdata = AllTwitchdata["data"]
            else:
                AllTwitchdata = None

        # No one is live
        if AllTwitchdata == [] and rUserData.status == 200:
            for USER in bot.Settings["Settings"]["TwitchUser"]:
                if bot.Settings["Settings"]["TwitchUser"][USER]["live"]:
                    bot.Settings["Settings"]["TwitchUser"][USER]["live"] = False
                    _write_json("Settings.json", bot.Settings)

        elif AllTwitchdata is None and rUserData.status != 200:
            pass

        # Someone is live
        else:
            for USER in bot.Settings["Settings"]["TwitchUser"]:
                # Create Alertgroups if missing
                twitchuserrole = discord.utils.get(guild.roles, name=f"{USER} Alert")
                if twitchuserrole is None:
                    await guild.create_role(name=f"{USER} Alert")
                    logging.info(f"Created Twitch Alertgroup for {USER} since there was none.")
                    twitchuserrole = discord.utils.get(guild.roles, name=f"{USER} Alert")

                livestate = bot.Settings["Settings"]["TwitchUser"][f"{USER}"]["live"]

                data = list(filter(lambda x: x["user_login"] == f"{USER}", AllTwitchdata))
                if data == []:
                    if livestate:
                        bot.Settings["Settings"]["TwitchUser"][USER]["live"] = False
                        _write_json("Settings.json", bot.Settings)
                    continue
                data = data[0]
                custommsg = bot.Settings["Settings"]["TwitchUser"][f"{USER}"]["custom_msg"]
                if livestate is False and data["user_login"]:
                    # User went live
                    game = data["game_name"] if data["game_name"] else "Irgendwas"

                    Displayname = data["user_name"] if data["user_name"] else USER.title()
                    CurrentTime = int(datetime.datetime.timestamp(datetime.datetime.now()))
                    embed = discord.Embed(title=f"{data['title']}", colour=discord.Colour(0x772CE8), url=f"https://twitch.tv/{USER}", timestamp=datetime.datetime.now())
                    embed.set_image(url=f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{USER}-1920x1080.jpg?v={CurrentTime}")
                    async with (
                        aiohttp.ClientSession(headers={"Authorization": f"Bearer {TWITCH_TOKEN}", "Client-Id": f"{TWITCH_CLIENT_ID}"}) as TwitchSession,
                        TwitchSession.get(f"https://api.twitch.tv/helix/users?login={data['user_login']}") as ProfileData,
                    ):
                        if ProfileData.status == 200:
                            UserProfile = await ProfileData.json()
                            ProfilePicData = UserProfile["data"][0]["profile_image_url"]
                        else:
                            ProfilePicData = ""
                    embed.set_author(name=f"{Displayname} ist jetzt live!", icon_url=f"{ProfilePicData}")
                    embed.set_footer(text="Bizeps_Bot")
                    NotificationTime = datetime.datetime.now() - timedelta(minutes=60)
                    if USER == "dota_joker":
                        DotoChannel = discord.utils.get(guild.text_channels, name="live")
                        LastMessages = await DotoChannel.history(after=NotificationTime).flatten()
                        if LastMessages:
                            for message in LastMessages:
                                if message.content.startswith(f"**{Displayname}**"):
                                    logging.info(f"{Displayname} went live on Twitch! Twitch Twitch Notification NOT sent, because the last Notification is under 60min old!")
                                    break
                                await DotoChannel.send(content=f"**{Displayname}** ist live mit {game}! {custommsg} {twitchuserrole.mention}", embed=embed)
                                logging.info(f"{Displayname} went live on Twitch! Twitch Notification sent!")
                                # DM when I go live, requested by Kernie
                                KernieDM = await bot.fetch_user(628940079913500703)
                                await KernieDM.send(content="Doto ist live, Kernovic!", embed=embed)
                                logging.info(f"{Displayname} went live on Twitch! Twitch Notification sent to Kernie!")
                                break
                        else:
                            await DotoChannel.send(content=f"**{Displayname}** ist live mit {game}! {custommsg} {twitchuserrole.mention}", embed=embed)
                            logging.info(f"{Displayname} went live on Twitch! Twitch Notification sent!")
                            # DM when I go live, requested by Kernie
                            KernieDM = await bot.fetch_user(628940079913500703)
                            await KernieDM.send(content="Doto ist live, Kernovic!", embed=embed)
                            logging.info(f"{Displayname} went live on Twitch! Twitch Notification sent to Kernie!")
                    else:
                        channel = discord.utils.get(guild.text_channels, name="kumpels-und-kumpelinen")
                        LastMessages = await channel.history(after=NotificationTime).flatten()
                        if LastMessages:
                            for message in LastMessages:
                                if message.content.startswith(f"**{Displayname}**"):
                                    logging.info(f"{Displayname} went live on Twitch! Twitch Twitch Notification NOT sent, because the last Notification is under 60min old!")
                                    break
                            else:
                                await channel.send(content=f"**{Displayname}** ist live mit {game}! {custommsg} {twitchuserrole.mention}", embed=embed)
                                logging.info(f"{Displayname} went live on Twitch! Twitch Twitch Notification sent, because the last Notification is older than 60min!")
                        else:
                            await channel.send(content=f"**{Displayname}** ist live mit {game}! {custommsg} {twitchuserrole.mention}", embed=embed)
                            logging.info(f"{Displayname} went live on Twitch! Twitch Notification sent!")

                    bot.Settings["Settings"]["TwitchUser"][USER]["live"] = True
                    _write_json("Settings.json", bot.Settings)
    except IndexError:
        # Username does not exist or Username is wrong, greetings to Schnabeltier
        logging.error("ERROR: ", exc_info=True)
    except json.decoder.JSONDecodeError:
        logging.error("ERROR: Twitch API not available.", exc_info=True)
    except KeyError:
        logging.error("ERROR: Twitch API not available.", exc_info=True)
    except Exception:
        logging.error("ERROR: ", exc_info=True)


@tasks.loop(seconds=60)
async def GameReminder():
    """
    Prüft jede Minute ob eine Verabredung eingerichtet ist,
    wenn ja wird in den Channel ein Reminder zur Uhrzeit gepostet.
    """

    CurrentTime = datetime.datetime.timestamp(datetime.datetime.now())
    FoundList = []
    for reminder in bot.Settings["Settings"]["Groups"]:
        if CurrentTime > bot.Settings["Settings"]["Groups"][f"{reminder}"]["time"]:
            Remindchannel = bot.get_channel(bot.Settings["Settings"]["Groups"][f"{reminder}"]["id"])
            ReminderMembers = ", ".join(bot.Settings["Settings"]["Groups"][f"{reminder}"]["members"])
            ReminderTheme = bot.Settings["Settings"]["Groups"][f"{reminder}"]["theme"]
            await Remindchannel.send(f" Es geht los mit {ReminderTheme}! Mit dabei sind: {ReminderMembers}")
            logging.info(f"Meeting in {reminder} started!")
            FoundList.append(reminder)
    if FoundList:
        for reminder in FoundList:
            bot.Settings["Settings"]["Groups"].pop(f"{reminder}")
        _write_json("Settings.json", bot.Settings)


@tasks.loop(time=datetime.time(hour=17, minute=0, second=0, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")))
async def TrashReminder():
    """
    Prüft einmal um 17 Uhr ob morgen Müll ist und sendet eine Nachricht an mich per Discord DM,
    dabei wird eine CSV Datei eingelesen und durchiteriert.
    """
    logging.info("Checking if there is garbage collection tomorrow...")
    AdminToNotify = 248181624485838849
    MyDiscordUser = await bot.fetch_user(AdminToNotify)
    TomorrowNow = datetime.datetime.today() + timedelta(days=1)
    TomorrowClean = TomorrowNow.replace(hour=00, minute=00, second=00, microsecond=00)

    with open(
        file="Muell.csv",
        mode="r",
        newline="",
    ) as TrashFile:
        CSVReader = csv.DictReader(TrashFile, delimiter=";")
        for Row in CSVReader:
            if Row["Schwarze Tonne"] != "":
                BlackTrashCan = parser.parse(Row["Schwarze Tonne"], fuzzy=True)
            if Row["Blaue Tonne"] != "":
                BlueTrashCan = parser.parse(Row["Blaue Tonne"], fuzzy=True)
            if Row["Gelbe Saecke"] != "":
                YellowTrashCan = parser.parse(Row["Gelbe Saecke"], fuzzy=True)

            if TomorrowClean == BlackTrashCan:
                await MyDiscordUser.send(f"Die nächste schwarze Tonne ist morgen am: {Row['Schwarze Tonne']}")
                logging.info(f"Reminder for black garbage can which is collected on {Row['Schwarze Tonne']} sent!")
            if TomorrowClean == BlueTrashCan:
                await MyDiscordUser.send(f"Die nächste blaue Tonne ist morgen am: {Row['Blaue Tonne']}")
                logging.info(f"Reminder for blue garbage can which is collected on {Row['Blaue Tonne']} sent!")
            if TomorrowClean == YellowTrashCan:
                await MyDiscordUser.send(f"Die nächste gelbe Tonne ist morgen am: {Row['Gelbe Saecke']}")
                logging.info(f"Reminder for yellow trashbag which is collected on {Row['Gelbe Saecke']} sent!")


### Bot Events ###


@bot.event
async def on_connect():
    pass


@bot.event
async def on_ready():
    """
    Startet den Bot und die Loops werden gestartet, sollten sie nicht schon laufen.
    """
    bot.reload_settings = _load_settings_file

    ### Add Cogs in bot file ###

    for File in os.listdir("./cogs"):
        if File.endswith(".py") and f"cogs.{File[:-3]}" not in bot.extensions and not File.startswith("management") and not File.startswith("old"):
            bot.load_extension(f"cogs.{File[:-3]}")
            logging.info(f"Extension {File[:-3]} loaded.")
    if "cogs.management" not in bot.extensions:
        bot.load_extension("cogs.management")
        logging.info("Extension management loaded.")

    logging.info(msg=f"Logged in as {bot.user}!")
    logging.info(msg="Bot started up!")

    if not TwitchLiveCheck.is_running():
        TwitchLiveCheck.start()
    if not GameReminder.is_running():
        GameReminder.start()
    if not TrashReminder.is_running():
        TrashReminder.start()
    await bot.sync_commands()


@bot.event
async def on_message(message):
    """
    Was bei einer Nachricht passieren soll.
    """
    if message.author == bot.user:
        return
    if await _is_banned(message):
        # This line needs to be added so the commands are actually processed
        await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    """
    Fehlerbehandlung falls Fehler bei einem Befehl auftreten.
    Aktuell werden dort nur fehlende Befehle behandelt.
    """

    if isinstance(error, commands.CommandNotFound):
        pass


if __name__ == "__main__":
    ### General Settings ###
    _load_settings_file()

    with open("TOKEN.json", "r", encoding="UTF-8") as TOKENFILE:
        TOKENDATA = json.load(TOKENFILE)
        TOKEN = TOKENDATA["DISCORD_TOKEN"]
        TWITCH_CLIENT_ID = TOKENDATA["TWITCH_CLIENT_ID"]
        TWITCH_CLIENT_SECRET = TOKENDATA["TWITCH_CLIENT_SECRET"]
        STREAMLABS_TOKEN = TOKENDATA["STREAMLABS_TOKEN"]
        if "TWITCH_TOKEN" in TOKENDATA and "TWITCH_TOKEN_EXPIRES" in TOKENDATA and datetime.datetime.timestamp(datetime.datetime.now()) < TOKENDATA["TWITCH_TOKEN_EXPIRES"]:
            TWITCH_TOKEN = TOKENDATA["TWITCH_TOKEN"]
            TWITCH_TOKEN_EXPIRES = TOKENDATA["TWITCH_TOKEN_EXPIRES"]
        else:
            RequestTwitchToken()
        logging.info("Token successfully loaded.")

    # Reading Banned Users before Startup for Cogs
    _get_banned_users()

    ### Run Bot ###

    bot.run(TOKEN)
