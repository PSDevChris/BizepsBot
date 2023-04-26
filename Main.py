import datetime
import io
import json
import logging
import os
import zoneinfo
from datetime import timedelta, timezone

import aiohttp
import discord
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from discord.ext import commands, tasks
from requests.utils import quote

logging.getLogger("discord").setLevel(logging.WARNING)
logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO, handlers=[logging.FileHandler(f'./logs/{datetime.datetime.now().date()}_bot.log'),
                                                                                      logging.StreamHandler()], encoding="UTF-8")

# To show the whole table, currently unused
# pd.set_option('display.max_rows', None)

intents = discord.Intents.default()
intents.message_content = True
# Remember to remove the debug guild if you want to use it on your server
bot = commands.Bot(debug_guilds=[539546796473712650],
                   command_prefix=('!'), intents=intents)

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
    }, timeout=30)

    TWITCHTOKENDATA = json.loads(rTwitchTokenData.content)
    TWITCH_TOKEN = TWITCHTOKENDATA['access_token']
    TWITCH_TOKEN_EXPIRES = datetime.datetime.timestamp(
        datetime.datetime.now()) + TWITCHTOKENDATA['expires_in']

    with open('TOKEN.json', encoding="UTF-8") as TokenJsonRead:
        data = json.load(TokenJsonRead)
        data['TWITCH_TOKEN'] = TWITCH_TOKEN
        data['TWITCH_TOKEN_EXPIRES'] = TWITCH_TOKEN_EXPIRES
    with open('TOKEN.json', 'w', encoding="UTF-8") as write_file:
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


def _load_settings_file():
    bot.Settings = _read_json('Settings.json')
    return bot.Settings

### Permission Checks ###


def _get_banned_users():
    bot.BannedUsers = _read_json('Settings.json')['Settings']['BannedUsers']
    return bot.BannedUsers

# Needs to be async for cog checks, command checks etc. work without async


async def _is_banned(ctx: commands.context.Context):
    if str(ctx.author) in bot.BannedUsers:
        logging.info(
            f"User {ctx.author} wanted to use a command but is banned.")
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

    TwitchJSON = _read_json('Settings.json')
    API_Call = io.StringIO()
    for index, USER in enumerate(TwitchJSON['Settings']['TwitchUser'].keys()):
        if index == 0:
            API_Call.write(f"user_login={USER}")
        else:
            API_Call.write(f"&user_login={USER}")

    try:
        # YOU NEED TO CHANGE THIS IF YOU WANT TO USE YOUR SERVER
        guild = bot.get_guild(539546796473712650)
        async with aiohttp.ClientSession(headers={'Authorization': f'Bearer {TWITCH_TOKEN}', 'Client-Id': f'{TWITCH_CLIENT_ID}'}) as TwitchSession:
            async with TwitchSession.get(f'https://api.twitch.tv/helix/streams?{API_Call.getvalue()}') as rUserData:
                API_Call.close()
                if rUserData.status == 200:
                    AllTwitchdata = await rUserData.json()
                    AllTwitchdata = AllTwitchdata["data"]

        # No one is live
        if AllTwitchdata == [] and rUserData.status == 200:
            for USER in TwitchJSON['Settings']['TwitchUser'].keys():
                if TwitchJSON['Settings']['TwitchUser'][USER]['live']:
                    TwitchJSON['Settings']['TwitchUser'][USER]['live'] = False
                    _write_json('Settings.json', TwitchJSON)
                    bot.Settings = TwitchJSON

        elif AllTwitchdata is None and rUserData.status != 200:
            pass

        # Someone is live
        else:
            for USER in TwitchJSON['Settings']['TwitchUser'].keys():

                # Create Alertgroups if missing
                twitchuserrole = discord.utils.get(
                    guild.roles, name=f"{USER} Alert")
                if twitchuserrole is None:
                    await guild.create_role(name=f"{USER} Alert")
                    logging.info(
                        f"Created Twitch Alertgroup for {USER} since there was none.")
                    twitchuserrole = discord.utils.get(
                        guild.roles, name=f"{USER} Alert")

                livestate = TwitchJSON['Settings']['TwitchUser'][f'{USER}']['live']

                data = list(
                    filter(lambda x: x["user_login"] == f"{USER}", AllTwitchdata))
                if data == []:
                    if livestate:
                        TwitchJSON['Settings']['TwitchUser'][USER]['live'] = False
                        _write_json('Settings.json', TwitchJSON)
                        bot.Settings = TwitchJSON
                    continue
                else:
                    data = data[0]
                    custommsg = TwitchJSON['Settings'][
                        'TwitchUser'][f'{USER}']['custom_msg']
                    if livestate is False and data['user_login']:
                        # User went live
                        if data['game_name']:
                            game = data['game_name']
                        else:
                            game = "Irgendwas"

                        if data['user_name']:
                            Displayname = data['user_name']
                        else:
                            Displayname = USER.title()
                        CurrentTime = int(datetime.datetime.timestamp(
                            datetime.datetime.now()))
                        embed = discord.Embed(title=f"{data['title']}", colour=discord.Colour(
                            0x772ce8), url=f"https://twitch.tv/{USER}", timestamp=datetime.datetime.now())
                        embed.set_image(
                            url=f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{USER}-1920x1080.jpg?v={CurrentTime}")
                        async with aiohttp.ClientSession(headers={'Authorization': f'Bearer {TWITCH_TOKEN}', 'Client-Id': f'{TWITCH_CLIENT_ID}'}) as TwitchSession:
                            async with TwitchSession.get(f'https://api.twitch.tv/helix/users?login={data["user_login"]}') as ProfileData:
                                if ProfileData.status == 200:
                                    UserProfile = await ProfileData.json()
                                    ProfilePicData = UserProfile["data"][0]["profile_image_url"]
                                else:
                                    ProfilePicData = ""
                        embed.set_author(
                            name=f"{Displayname} ist jetzt live!", icon_url=f"{ProfilePicData}")
                        embed.set_footer(text="Bizeps_Bot")
                        NotificationTime = datetime.datetime.now() - timedelta(minutes=60)
                        if USER == 'dota_joker':
                            DotoChannel = bot.get_channel(
                                539547495567720492)
                            LastMessages = await DotoChannel.history(after=NotificationTime).flatten()
                            if LastMessages:
                                for message in LastMessages:
                                    if message.content.startswith(f"**{Displayname}**"):
                                        logging.info(
                                            f"{Displayname} went live on Twitch! Twitch Twitch Notification NOT sent, because the last Notification is under 60min old!")
                                        break
                                    else:
                                        await bot.get_channel(539547495567720492).send(content=f"**{Displayname}** ist live mit {game}! {custommsg} {twitchuserrole.mention}", embed=embed)
                                        logging.info(
                                            f"{Displayname} went live on Twitch! Twitch Notification sent!")
                                        # DM when I go live, requested by Kernie
                                        KernieDM = await bot.fetch_user(628940079913500703)
                                        await KernieDM.send(content="Doto ist live, Kernovic!", embed=embed)
                                        logging.info(
                                            f"{Displayname} went live on Twitch! Twitch Notification sent to Kernie!")
                                        break
                            else:
                                await bot.get_channel(539547495567720492).send(content=f"**{Displayname}** ist live mit {game}! {custommsg} {twitchuserrole.mention}", embed=embed)
                                logging.info(
                                    f"{Displayname} went live on Twitch! Twitch Notification sent!")
                                # DM when I go live, requested by Kernie
                                KernieDM = await bot.fetch_user(628940079913500703)
                                await KernieDM.send(content="Doto ist live, Kernovic!", embed=embed)
                                logging.info(
                                    f"{Displayname} went live on Twitch! Twitch Notification sent to Kernie!")
                        else:
                            channel = bot.get_channel(
                                703530328836407327)
                            LastMessages = await channel.history(after=NotificationTime).flatten()
                            if LastMessages:
                                for message in LastMessages:
                                    if message.content.startswith(f"**{Displayname}**"):
                                        logging.info(
                                            f"{Displayname} went live on Twitch! Twitch Twitch Notification NOT sent, because the last Notification is under 60min old!")
                                        break
                                else:
                                    await channel.send(content=f"**{Displayname}** ist live mit {game}! {custommsg} {twitchuserrole.mention}", embed=embed)
                                    logging.info(
                                        f"{Displayname} went live on Twitch! Twitch Twitch Notification sent, because the last Notification is older than 60min!")
                            else:
                                await channel.send(content=f"**{Displayname}** ist live mit {game}! {custommsg} {twitchuserrole.mention}", embed=embed)
                                logging.info(
                                    f"{Displayname} went live on Twitch! Twitch Notification sent!")

                        TwitchJSON['Settings']['TwitchUser'][USER]['live'] = True
                        _write_json(
                            'Settings.json', TwitchJSON)
                        bot.Settings = TwitchJSON
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
    groups = bot.Settings
    FoundList = []
    for reminder in groups["Settings"]["Groups"].keys():
        if CurrentTime > groups["Settings"]["Groups"][f"{reminder}"]["time"]:
            Remindchannel = bot.get_channel(
                groups["Settings"]["Groups"][f"{reminder}"]["id"])
            ReminderMembers = ", ".join(
                groups["Settings"]["Groups"][f"{reminder}"]["members"])
            ReminderTheme = groups["Settings"]["Groups"][f"{reminder}"]["theme"]
            await Remindchannel.send(f" Es geht los mit {ReminderTheme}! Mit dabei sind: {ReminderMembers}")
            logging.info(f"Meeting in {reminder} started!")
            FoundList.append(reminder)
    if FoundList:
        for reminder in FoundList:
            groups["Settings"]["Groups"].pop(f'{reminder}')
        _write_json('Settings.json', groups)
        bot.Settings = groups

# this needs a fix discussed in https://github.com/Pycord-Development/pycord/issues/1990


@tasks.loop(time=datetime.time(hour=17, minute=0, second=0, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")))
async def TrashReminder():
    """
    Prüft einmal um 17 Uhr ob morgen Müll ist und sendet eine Nachricht an mich per Discord DM,
    dabei wird eine CSV Datei eingelesen und durchiteriert.
    """
    AdminToNotify = 248181624485838849
    MyDiscordUser = await bot.fetch_user(AdminToNotify)
    tomorrowNow = datetime.datetime.today() + timedelta(days=1)
    tomorrowClean = tomorrowNow.replace(
        hour=00, minute=00, second=00, microsecond=00)
    # categorial DFs reduce memory usage
    MuellListe = pd.read_csv('Muell.csv', sep=";", dtype='category')
    for entry in MuellListe["Schwarze Tonne"].dropna():
        EntryDate = pd.to_datetime(entry[3:], dayfirst=True)
        if tomorrowClean == EntryDate:
            await MyDiscordUser.send(f"Die nächste schwarze Tonne ist morgen am: {entry}")
            logging.info(
                f"Reminder for black garbage can which is collected on {entry} sent!")
            break

    for entry in MuellListe["Blaue Tonne"].dropna():
        EntryDate = pd.to_datetime(entry[3:], dayfirst=True)
        if tomorrowClean == EntryDate:
            await MyDiscordUser.send(f"Die nächste blaue Tonne ist morgen am: {entry}")
            logging.info(
                f"Reminder for blue garbage can which is collected on {entry} sent!")
            break

    for entry in MuellListe["Gelbe Saecke"].dropna():
        EntryDate = pd.to_datetime(entry[3:], dayfirst=True)
        if tomorrowClean == EntryDate:
            await MyDiscordUser.send(f"Die nächsten gelben Säcke sind morgen am: {entry}")
            logging.info(
                f"Reminder for yellow trashbag which is collected on {entry} sent!")
            break


# this needs a fix discussed in https://github.com/Pycord-Development/pycord/issues/1990
@tasks.loop(time=datetime.time(hour=17, minute=5, second=0, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")))
async def GetFreeEpicGames():

    AllEpicFiles = next(os.walk("epic/"))[2]
    NumberOfEpicFiles = len(AllEpicFiles)

    FreeGamesList = _read_json('Settings.json')
    CurrentTime = datetime.datetime.now(timezone.utc)
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
        bot.Settings = FreeGamesList

    EpicStoreURL = 'https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=de&country=DE&allowCountries=DE'

    async with aiohttp.ClientSession() as EpicSession:
        async with EpicSession.get(EpicStoreURL) as RequestFromEpic:

            if RequestFromEpic.status == 200:
                JSONFromEpicStore = await RequestFromEpic.json()
            else:
                logging.error("Epic Store is not available!")
            if JSONFromEpicStore['data']['Catalog']['searchStore']['elements']:
                for FreeGame in JSONFromEpicStore['data']['Catalog']['searchStore']['elements']:
                    if FreeGame['promotions'] is not None and FreeGame['promotions']['promotionalOffers'] != []:
                        PromotionalStartDate = parser.parse(
                            FreeGame['promotions']['promotionalOffers'][0]['promotionalOffers'][0]['startDate'])
                        LaunchingToday = parser.parse(
                            FreeGame['effectiveDate'])

                        if FreeGame['price']['totalPrice']['discountPrice'] == 0 and (LaunchingToday.date() <= datetime.datetime.now().date() or PromotionalStartDate.date() <= datetime.datetime.now().date()):
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
                                        bot.Settings = FreeGamesList
                                        EndOfOffer = offer['promotionalOffers'][0]['endDate']
                                        EndDateOfOffer = parser.parse(
                                            EndOfOffer).date()

                                        for index in range(len(FreeGame['keyImages'])):
                                            if FreeGame['keyImages'][index]['type'] == "Thumbnail":
                                                EpicImageURL = FreeGame['keyImages'][index]['url']
                                                async with EpicSession.get(EpicImageURL) as EpicImageReq:
                                                    EpicImage = await EpicImageReq.read()
                                                    break
                                            elif FreeGame['keyImages'][index]['type'] == "DieselStoreFrontWide":
                                                EpicImageURL = FreeGame['keyImages'][index]['url']
                                                async with EpicSession.get(EpicImageURL) as EpicImageReq:
                                                    EpicImage = await EpicImageReq.read()
                                                    break
                                            elif FreeGame['keyImages'][index]['type'] == "OfferImageWide":
                                                EpicImageURL = FreeGame['keyImages'][index]['url']
                                                async with EpicSession.get(EpicImageURL) as EpicImageReq:
                                                    EpicImage = await EpicImageReq.read()
                                                    break
                                        else:
                                            EpicImageURL = ""
                                            EpicImage = ""

                                        ### Build Embed with chosen vars ###
                                        EpicEmbed = discord.Embed(title=f"Neues Gratis Epic Game: {FreeGame['title']}!\r\n\nNoch einlösbar bis zum {EndDateOfOffer.day}.{EndDateOfOffer.month}.{EndDateOfOffer.year}!\r\n\n", colour=discord.Colour(
                                            0x1), timestamp=datetime.datetime.now())
                                        EpicEmbed.set_thumbnail(
                                            url=r'https://cdn2.unrealengine.com/Epic+Games+Node%2Fxlarge_whitetext_blackback_epiclogo_504x512_1529964470588-503x512-ac795e81c54b27aaa2e196456dd307bfe4ca3ca4.jpg')
                                        EpicEmbed.set_author(
                                            name="Bizeps_Bot", icon_url="https://cdn.discordapp.com/avatars/794273832508588062/9267c06d60098704f652d980caa5a43c.png")
                                        if FreeGame['productSlug']:
                                            if "collection" in FreeGame['productSlug'] or "bundle" in FreeGame['productSlug'] or "trilogy" in FreeGame['productSlug']:
                                                EpicEmbed.add_field(
                                                    name="Besuch mich im EGS", value=f"[Epic Games Store](https://store.epicgames.com/de/bundles/{FreeGame['productSlug']})", inline=True)
                                                EpicEmbed.add_field(
                                                    name="Hol mich im Launcher", value=f"<com.epicgames.launcher://store/bundles/{FreeGame['productSlug']}>", inline=True)
                                            else:
                                                EpicEmbed.add_field(
                                                    name="Besuch mich im EGS", value=f"[Epic Games Store](https://store.epicgames.com/de/p/{FreeGame['productSlug']})", inline=True)
                                                EpicEmbed.add_field(
                                                    name="Hol mich im Launcher", value=f"<com.epicgames.launcher://store/p/{FreeGame['productSlug']}>", inline=True)
                                        elif FreeGame['catalogNs']['mappings'][0]['pageSlug']:
                                            if "collection" in FreeGame['catalogNs']['mappings'][0]['pageSlug'] or "bundle" in FreeGame['catalogNs']['mappings'][0]['pageSlug'] or "trilogy" in FreeGame['catalogNs']['mappings'][0]['pageSlug']:
                                                EpicEmbed.add_field(
                                                    name="Besuch mich im EGS", value=f"[Epic Games Store](https://store.epicgames.com/de/bundles/{FreeGame['catalogNs']['mappings'][0]['pageSlug']})", inline=True)
                                                EpicEmbed.add_field(
                                                    name="Hol mich im Launcher", value=f"<com.epicgames.launcher://store/bundles/{FreeGame['catalogNs']['mappings'][0]['pageSlug']}>", inline=True)
                                            else:
                                                EpicEmbed.add_field(
                                                    name="Besuch mich im EGS", value=f"[Epic Games Store](https://store.epicgames.com/de/p/{FreeGame['catalogNs']['mappings'][0]['pageSlug']})", inline=True)
                                                EpicEmbed.add_field(
                                                    name="Hol mich im Launcher", value=f"<com.epicgames.launcher://store/p/{FreeGame['catalogNs']['mappings'][0]['pageSlug']}>", inline=True)
                                        if EpicImageURL != "":
                                            EpicImageURL = quote(
                                                EpicImageURL, safe=':/')
                                            EpicEmbed.set_image(
                                                url=f"{EpicImageURL}")
                                        EpicEmbed.set_footer(
                                            text="Bizeps_Bot")

                                        if EpicImage != "" and EpicImage:
                                            NumberOfEpicFiles = NumberOfEpicFiles + 1
                                            EpicImagePath = f"{NumberOfEpicFiles}_epic.jpg"
                                            with open(f'epic/{EpicImagePath}', 'wb') as write_file:
                                                write_file.write(
                                                    EpicImage)
                                        await bot.get_channel(539553203570606090).send(embed=EpicEmbed)
                                        logging.info(
                                            f"{FreeGame['title']} was added to free Epic Games!")
                                        # Send Games to Schnenk
                                        SchnenkDM = await bot.fetch_user(257249704872509441)
                                        await SchnenkDM.send(embed=EpicEmbed)
                                        logging.info(
                                            "Free Epic Games were sent to Schnenk.")

                                except json.decoder.JSONDecodeError:
                                    logging.error(
                                        "ERROR: Something bad happend with the json decoding! The Free EpicGames list was created again!", exc_info=True)
                                    FreeGamesList['Settings']['FreeEpicGames'] = {
                                    }
                                    FreeGamesList['Settings']['FreeEpicGames'].update(
                                        FreeGameObject)
                                    _write_json(
                                        'Settings.json', FreeGamesList)
                                    bot.Settings = FreeGamesList


@tasks.loop(minutes=15)
async def _get_free_steamgames():
    FreeGameTitleList = []
    FreeSteamList = _read_json('Settings.json')
    SteamURL = "https://store.steampowered.com/search/?maxprice=free&specials=1"
    async with aiohttp.ClientSession() as SteamSession:
        async with SteamSession.get(SteamURL) as SteamReq:
            if SteamReq.status == 200:
                SteamPage = await SteamReq.read()
                if SteamPage:
                    SteamHTML = BeautifulSoup(SteamPage, "html.parser")
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
                                        0x6c6c6c), timestamp=datetime.datetime.now())
                                    SteamEmbed.set_thumbnail(
                                        url=r'https://store.cloudflare.steamstatic.com/public/images/v6/logo_steam_footer.png')
                                    SteamEmbed.set_author(
                                        name="Bizeps_Bot", icon_url="https://cdn.discordapp.com/avatars/794273832508588062/9267c06d60098704f652d980caa5a43c.png")
                                    SteamEmbed.add_field(
                                        name="Besuch mich auf Steam", value=f"{SteamGameURL}", inline=True)
                                    SteamEmbed.add_field(
                                        name="Hol mich im Launcher", value=f"<Steam://Store/{ProdID}>", inline=True)
                                    SteamImageURL = quote(ImageSrc, safe=':/')
                                    SteamEmbed.set_image(
                                        url=f"{SteamImageURL}")
                                    SteamEmbed.set_footer(text="Bizeps_Bot")
                                    await bot.get_channel(539553203570606090).send(embed=SteamEmbed)
                                    FreeSteamList['Settings']['FreeSteamGames'].append(
                                        SteamGameTitle)
                                    _write_json('Settings.json', FreeSteamList)
                                    bot.Settings = FreeSteamList
                                    # Hack for missing char mapping in logging module
                                    SteamGameTitle = SteamGameTitle.replace(
                                        "\uFF1A", ": ")
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
                            bot.Settings = FreeSteamList


@tasks.loop(minutes=20)
async def _get_free_goggames():
    FreeGOGList = _read_json('Settings.json')

    GOGURL = "https://www.gog.com/"
    async with aiohttp.ClientSession() as GOGSession:
        async with GOGSession.get(GOGURL) as GOGReq:
            if GOGReq.status == 200:
                GOGHTML = await GOGReq.read()
                if GOGHTML:
                    GOGResult = BeautifulSoup(GOGHTML, "html.parser")
                    GOGPage = GOGResult.find_all(
                        "a", class_="container giveaway-banner giveaway-banner--with-consent is-loading")
                    if GOGPage != []:
                        GOGGameURL = f"http://www.gog.com{GOGPage[0]['ng-href']}"
                        GOGGameTitleBanner = GOGPage[0].find_all(
                            'span', 'giveaway-banner__title')
                        GOGGameTitle = " ".join(
                            GOGGameTitleBanner[-1].text.split()[1:])
                        if GOGGameTitle not in FreeGOGList['Settings']['FreeGOGGames']:
                            GOGImageURL = GOGPage[0].find_all(
                                'source', attrs={'srcset': True})
                            GOGImageURL = f"http:{GOGImageURL[-1]['srcset'].split(',')[-1].split()[0]}"

                            GOGEmbed = discord.Embed(title=f"Neues Gratis GOG Game: {GOGGameTitle}!\r\n\n", colour=discord.Colour(
                                0xffffff), timestamp=datetime.datetime.now())
                            GOGEmbed.set_thumbnail(
                                url=r'https://www.gog.com/blog/wp-content/uploads/2022/01/gogcomlogo-1.jpeg')
                            GOGEmbed.set_author(
                                name="Bizeps_Bot", icon_url="https://cdn.discordapp.com/avatars/794273832508588062/9267c06d60098704f652d980caa5a43c.png")
                            GOGEmbed.add_field(
                                name="Besuch mich auf GOG", value=f"{GOGGameURL}", inline=True)
                            GOGEmbed.set_image(
                                url=f"{GOGImageURL}")
                            GOGEmbed.set_footer(text="Bizeps_Bot")
                            await bot.get_channel(539553203570606090).send(embed=GOGEmbed)
                            FreeGOGList['Settings']['FreeGOGGames'].append(
                                GOGGameTitle)
                            _write_json('Settings.json', FreeGOGList)
                            bot.Settings = FreeGOGList
                            logging.info(
                                f"Added GOG Game: {GOGGameTitle} to Free GOG List.")
                    else:
                        for FreeGameEntry in FreeGOGList['Settings']['FreeGOGGames']:
                            FreeGOGList['Settings']['FreeGOGGames'].remove(
                                FreeGameEntry)
                            logging.info(
                                f"{FreeGameEntry} removed from free GOG Games, since it expired!")
                            _write_json('Settings.json', FreeGOGList)
                            bot.Settings = FreeGOGList


### Bot Events ###


@bot.event
async def on_ready():
    """
    Startet den Bot und die Loops werden gestartet, sollten sie nicht schon laufen.
    """

    logging.info(f"Logged in as {bot.user}!")
    logging.info("Bot started up!")
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
    if not _get_free_goggames.is_running():
        _get_free_goggames.start()
    RefreshMemes()


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
        logging.warning(
            f"{error}, {ctx.author} wants a new command.")

if __name__ == '__main__':

    ### General Settings ###
    _load_settings_file()

    with open("TOKEN.json", "r", encoding="UTF-8") as TOKENFILE:
        TOKENDATA = json.load(TOKENFILE)
        TOKEN = TOKENDATA['DISCORD_TOKEN']
        TWITCH_CLIENT_ID = TOKENDATA['TWITCH_CLIENT_ID']
        TWITCH_CLIENT_SECRET = TOKENDATA['TWITCH_CLIENT_SECRET']
        STREAMLABS_TOKEN = TOKENDATA['STREAMLABS_TOKEN']
        if 'TWITCH_TOKEN' in TOKENDATA.keys() and 'TWITCH_TOKEN_EXPIRES' in TOKENDATA.keys() and datetime.datetime.timestamp(datetime.datetime.now()) < TOKENDATA['TWITCH_TOKEN_EXPIRES']:
            TWITCH_TOKEN = TOKENDATA['TWITCH_TOKEN']
            TWITCH_TOKEN_EXPIRES = TOKENDATA['TWITCH_TOKEN_EXPIRES']
        else:
            RequestTwitchToken()
        logging.info("Token successfully loaded.")

    # Reading Banned Users before Startup for Cogs
    _get_banned_users()

    ### Add Cogs in bot file ###

    for File in os.listdir('./cogs'):
        if File.endswith('.py') and f"cogs.{File[:-3]}" not in bot.extensions.keys() and not File.startswith("management") and not File.startswith("old"):
            bot.load_extension(f"cogs.{File[:-3]}")
            logging.info(f"Extension {File[:-3]} loaded.")
    if "cogs.management" not in bot.extensions.keys():
        bot.load_extension("cogs.management")
        logging.info("Extension management loaded.")

    ### Run Bot ###

    bot.run(TOKEN)
