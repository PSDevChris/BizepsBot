import asyncio
import json
import os
import zoneinfo
from datetime import timedelta, timezone

import discord
from bs4 import BeautifulSoup
from dateutil import parser
from discord.ext import commands, tasks
from requests.utils import quote

from Main import _write_json, aiohttp, datetime, logging


class Gaming(commands.Cog):
    def __init__(self, bot):  # this is a special method that is called when the cog is loaded
        self.bot = bot
        self._get_free_goggames.start()
        self._get_free_steamgames.start()
        self._get_free_epicgames.start()

    # Loops
    @tasks.loop(time=datetime.time(hour=19, minute=5, second=0, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")))
    async def _get_free_goggames(self):
        logging.info("Check if there are new free GOG.com games...")
        GOGURL = "https://www.gog.com/"
        async with aiohttp.ClientSession() as GOGSession:
            for _ in range(10):  # ten tries to find the giveaway HTML, this is absolutely godless but otherwise the bot is too spammy
                async with GOGSession.get(GOGURL) as GOGReq:
                    if GOGReq.status == 200:
                        GOGHTML = await GOGReq.read()
                        if GOGHTML:
                            GOGResult = BeautifulSoup(GOGHTML, "html.parser")
                            GOGPage = GOGResult.find_all(class_="giveaway")
                            if GOGPage != []:
                                GOGGameURL = GOGPage[0].find_all(class_="giveaway__overlay-link")[0]["href"]
                                GOGGameTitle = GOGPage[0].find_all(class_="giveaway__image")[0].find_all("img", alt=True)[0]["alt"].replace(" giveaway", "")
                                if GOGGameTitle not in self.bot.Settings["Settings"]["FreeGOGGames"]:
                                    GOGImageURL = GOGPage[0].find_all(class_="giveaway__image")[0].find_all("source", srcset=True, type="image/jpeg")[0]["srcset"].split(",")[0]

                                    GOGEmbed = discord.Embed(title=f"Neues Gratis GOG Game: {GOGGameTitle}!\r\n\n", colour=discord.Colour(0xFFFFFF), timestamp=datetime.datetime.now())
                                    GOGEmbed.set_thumbnail(url=r"https://www.gog.com/blog/wp-content/uploads/2022/01/gogcomlogo-1.jpeg")
                                    GOGEmbed.set_author(name="Bizeps_Bot", icon_url="https://cdn.discordapp.com/avatars/794273832508588062/9267c06d60098704f652d980caa5a43c.png")
                                    GOGEmbed.add_field(name="Besuch mich auf GOG", value=f"{GOGGameURL}", inline=True)
                                    GOGEmbed.set_image(url=f"{GOGImageURL}")
                                    GOGEmbed.set_footer(text="Bizeps_Bot")
                                    guild = self.bot.get_guild(self.bot.SERVER)
                                    GOGRole = discord.utils.get(guild.roles, name="Free GOG Game Alert")
                                    GamingChannel = discord.utils.get(guild.text_channels, name="gaming")
                                    await GamingChannel.send(content=f"{GOGRole.mention}", embed=GOGEmbed)
                                    self.bot.Settings["Settings"]["FreeGOGGames"].append(GOGGameTitle)
                                    _write_json("Settings.json", self.bot.Settings)
                                    # Send GOG Games to Subscribers via DM
                                    DMRoleGOG = discord.utils.get(guild.roles, name="DM Alert GOG")
                                    for user in DMRoleGOG.members:
                                        UserDM = await self.bot.get_or_fetch_user(user.id)
                                        await UserDM.send(embed=GOGEmbed)
                                        await asyncio.sleep(2)  # for ratelimiting reasons
                                        logging.info(f"Free GOG Games were sent to subscriber [{user}].")
                                    logging.info(f"Added GOG Game: {GOGGameTitle} to Free GOG List.")
                                break
                            await asyncio.sleep(360)  # wait five minutes to search for that html again
            else:
                if self.bot.Settings["Settings"]["FreeGOGGames"]:
                    for FreeGameEntry in self.bot.Settings["Settings"]["FreeGOGGames"]:
                        self.bot.Settings["Settings"]["FreeGOGGames"].remove(FreeGameEntry)
                        logging.info(f"{FreeGameEntry} removed from free GOG Games, since it expired!")
                        _write_json("Settings.json", self.bot.Settings)

    @tasks.loop(minutes=15)
    async def _get_free_steamgames(self):
        FreeGameTitleList = []
        SteamURL = "https://store.steampowered.com/search/?maxprice=free&specials=1"
        async with aiohttp.ClientSession() as SteamSession, SteamSession.get(SteamURL) as SteamReq:
            if SteamReq.status == 200:
                SteamPage = await SteamReq.read()
                if SteamPage:
                    SteamHTML = BeautifulSoup(SteamPage, "html.parser")
                    SteamResult = SteamHTML.find_all("a", class_="search_result_row ds_collapse_flag")
                    if SteamResult:
                        NotifiedUsers = False  # Check if we already pinged the role
                        for Result in SteamResult:
                            SteamGameTitle = Result.find(class_="title").text
                            if SteamGameTitle:
                                FreeGameTitleList.append(SteamGameTitle)
                                if SteamGameTitle not in self.bot.Settings["Settings"]["FreeSteamGames"]:
                                    SteamGameURL = Result["href"]
                                    ProdID = Result["data-ds-appid"]
                                    ImageSrc = f"https://cdn.akamai.steamstatic.com/steam/apps/{ProdID}/header.jpg"
                                    SteamEmbed = discord.Embed(title=f"Neues Gratis Steam Game: {SteamGameTitle}!\r\n\n", colour=discord.Colour(0x6C6C6C), timestamp=datetime.datetime.now())
                                    SteamEmbed.set_thumbnail(url=r"https://store.cloudflare.steamstatic.com/public/images/v6/logo_steam_footer.png")
                                    SteamEmbed.set_author(name="Bizeps_Bot", icon_url="https://cdn.discordapp.com/avatars/794273832508588062/9267c06d60098704f652d980caa5a43c.png")
                                    SteamEmbed.add_field(name="Besuch mich auf Steam", value=f"{SteamGameURL}", inline=True)
                                    SteamEmbed.add_field(name="Hol mich im Launcher", value=f"<Steam://openurl/{SteamGameURL}>", inline=True)
                                    SteamImageURL = quote(ImageSrc, safe=":/")
                                    SteamEmbed.set_image(url=f"{SteamImageURL}")
                                    SteamEmbed.set_footer(text="Bizeps_Bot")
                                    guild = self.bot.get_guild(self.bot.Server)
                                    GamingChannel = discord.utils.get(guild.text_channels, name="gaming")
                                    if NotifiedUsers is False:
                                        SteamRole = discord.utils.get(guild.roles, name="Free Steam Game Alert")
                                        await GamingChannel.send(content=f"{SteamRole.mention}", embed=SteamEmbed)
                                        # Send Steam Games to Subscribers via DM
                                        DMRoleSteam = discord.utils.get(guild.roles, name="DM Alert Steam")
                                        for user in DMRoleSteam.members:
                                            UserDM = await self.bot.get_or_fetch_user(user.id)
                                            await UserDM.send(embed=SteamEmbed)
                                            await asyncio.sleep(2)  # for ratelimiting reasons
                                            logging.info(f"Free Steam Games were sent to subscriber [{user}].")
                                        NotifiedUsers = True
                                    else:
                                        await GamingChannel.send(embed=SteamEmbed)
                                        # Send Steam Games to Subscribers via DM
                                        DMRoleSteam = discord.utils.get(guild.roles, name="DM Alert Steam")
                                        for user in DMRoleSteam.members:
                                            UserDM = await self.bot.get_or_fetch_user(user.id)
                                            await UserDM.send(embed=SteamEmbed)
                                            await asyncio.sleep(2)  # for ratelimiting reasons
                                            logging.info(f"Free Steam Games were sent to subscriber [{user}].")
                                    self.bot.Settings["Settings"]["FreeSteamGames"].append(SteamGameTitle)
                                    _write_json("Settings.json", self.bot.Settings)
                                    # Hack for missing char mapping in logging module
                                    SteamGameTitle = SteamGameTitle.replace("\uff1a", ": ")
                                    logging.info(f"{SteamGameTitle} was added to the free steam game list.")

                        ExpiredGames = set(self.bot.Settings["Settings"]["FreeSteamGames"]).difference(FreeGameTitleList)
                        for ExpiredGame in ExpiredGames:
                            self.bot.Settings["Settings"]["FreeSteamGames"].remove(ExpiredGame)
                            logging.info(f"Removed {ExpiredGame} from free steam game list since it expired.")
                            _write_json("Settings.json", self.bot.Settings)

    # this needs a fix discussed in https://github.com/Pycord-Development/pycord/issues/1990
    @tasks.loop(time=datetime.time(hour=17, minute=5, second=0, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")))
    async def _get_free_epicgames(self):
        logging.info("Checking if there are new free epic games...")
        AllEpicFiles = next(os.walk("epic/"))[2]
        NumberOfEpicFiles = len(AllEpicFiles)
        CurrentTime = datetime.datetime.now(timezone.utc)
        EndedOffers = []

        for FreeGameEntry in self.bot.Settings["Settings"]["FreeEpicGames"]:
            GameEndDate = (
                parser.parse(self.bot.Settings["Settings"]["FreeEpicGames"][f"{FreeGameEntry}"]["endDate"])
                if self.bot.Settings["Settings"]["FreeEpicGames"][f"{FreeGameEntry}"]["endDate"]
                else (datetime.datetime.now() + timedelta(days=7)).replace(hour=12)  # to make the game expire in a week
            )
            if CurrentTime > GameEndDate:
                EndedOffers.append(FreeGameEntry)

        if EndedOffers:
            for EndedOffer in EndedOffers:
                self.bot.Settings["Settings"]["FreeEpicGames"].pop(EndedOffer)
                logging.info(f"{EndedOffer} removed from free Epic Games, since it expired!")
                _write_json("Settings.json", self.bot.Settings)

        EpicStoreURL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=de&country=DE&allowCountries=DE"

        async with aiohttp.ClientSession() as EpicSession, EpicSession.get(EpicStoreURL) as RequestFromEpic:
            if RequestFromEpic.status == 200:
                JSONFromEpicStore = await RequestFromEpic.json()
            else:
                logging.error("Epic Store is not available!")
            if JSONFromEpicStore["data"]["Catalog"]["searchStore"]["elements"]:
                for FreeGame in JSONFromEpicStore["data"]["Catalog"]["searchStore"]["elements"]:
                    if FreeGame["promotions"] is not None and FreeGame["promotions"]["promotionalOffers"] != []:
                        PromotionalStartDate = (
                            parser.parse(FreeGame["promotions"]["promotionalOffers"][0]["promotionalOffers"][0]["startDate"])
                            if FreeGame["promotions"]["promotionalOffers"][0]["promotionalOffers"][0]["startDate"]
                            else parser.parse(FreeGame["promotions"]["promotionalOffers"][0]["promotionalOffers"][1]["startDate"])  # Look at the second property
                        )
                        LaunchingToday = parser.parse(FreeGame["effectiveDate"])

                        if FreeGame["price"]["totalPrice"]["discountPrice"] == 0 and (
                            LaunchingToday.date() <= datetime.datetime.now().date() or PromotionalStartDate.date() <= datetime.datetime.now().date()
                        ):
                            offers = FreeGame["promotions"]["promotionalOffers"]
                            for offer in offers:
                                FreeGameObject = {
                                    f"{FreeGame['title']}": {
                                        "startDate": offer["promotionalOffers"][0]["startDate"],
                                        "endDate": offer["promotionalOffers"][0]["endDate"],
                                    }
                                }

                                try:
                                    if FreeGame["title"] in self.bot.Settings["Settings"]["FreeEpicGames"]:
                                        pass
                                    else:
                                        self.bot.Settings["Settings"]["FreeEpicGames"].update(FreeGameObject)
                                        _write_json("Settings.json", self.bot.Settings)
                                        EndOfOffer = (
                                            offer["promotionalOffers"][0]["endDate"]
                                            if offer["promotionalOffers"][0]["endDate"]
                                            else offer["promotionalOffers"][1]["endDate"]  # Look into the second property for the EndDate
                                        )
                                        EndDateOfOffer = parser.parse(EndOfOffer).date()

                                        for index in range(len(FreeGame["keyImages"])):
                                            if FreeGame["keyImages"][index]["type"] in ["Thumbnail", "DieselStoreFrontWide", "OfferImageWide"]:
                                                EpicImageURL = FreeGame["keyImages"][index]["url"]
                                                async with EpicSession.get(EpicImageURL) as EpicImageReq:
                                                    EpicImage = await EpicImageReq.read()
                                                    break
                                        else:
                                            EpicImageURL = ""
                                            EpicImage = ""

                                        ### Build Embed with chosen vars ###
                                        EpicEmbed = discord.Embed(
                                            title=f"Neues Gratis Epic Game: {FreeGame['title']}!\r\n\nNoch einlösbar bis zum {EndDateOfOffer.day}.{EndDateOfOffer.month}.{EndDateOfOffer.year}!\r\n\n",
                                            colour=discord.Colour(0x1),
                                            timestamp=datetime.datetime.now(),
                                        )
                                        EpicEmbed.set_thumbnail(
                                            url=r"https://cdn2.unrealengine.com/Epic+Games+Node%2Fxlarge_whitetext_blackback_epiclogo_504x512_1529964470588-503x512-ac795e81c54b27aaa2e196456dd307bfe4ca3ca4.jpg"
                                        )
                                        EpicEmbed.set_author(name="Bizeps_Bot", icon_url="https://cdn.discordapp.com/avatars/794273832508588062/9267c06d60098704f652d980caa5a43c.png")
                                        if FreeGame["productSlug"]:
                                            if "collection" in FreeGame["productSlug"] or "bundle" in FreeGame["productSlug"] or "trilogy" in FreeGame["productSlug"]:
                                                EpicEmbed.add_field(
                                                    name="Besuch mich im EGS", value=f"[Epic Games Store](https://store.epicgames.com/de/bundles/{FreeGame['productSlug']})", inline=True
                                                )
                                                EpicEmbed.add_field(name="Hol mich im Launcher", value=f"<com.epicgames.launcher://store/bundles/{FreeGame['productSlug']}>", inline=True)
                                            else:
                                                EpicEmbed.add_field(name="Besuch mich im EGS", value=f"[Epic Games Store](https://store.epicgames.com/de/p/{FreeGame['productSlug']})", inline=True)
                                                EpicEmbed.add_field(name="Hol mich im Launcher", value=f"<com.epicgames.launcher://store/p/{FreeGame['productSlug']}>", inline=True)
                                        elif FreeGame["catalogNs"]["mappings"][0]["pageSlug"]:
                                            if (
                                                "collection" in FreeGame["catalogNs"]["mappings"][0]["pageSlug"]
                                                or "bundle" in FreeGame["catalogNs"]["mappings"][0]["pageSlug"]
                                                or "trilogy" in FreeGame["catalogNs"]["mappings"][0]["pageSlug"]
                                            ):
                                                EpicEmbed.add_field(
                                                    name="Besuch mich im EGS",
                                                    value=f"[Epic Games Store](https://store.epicgames.com/de/bundles/{FreeGame['catalogNs']['mappings'][0]['pageSlug']})",
                                                    inline=True,
                                                )
                                                EpicEmbed.add_field(
                                                    name="Hol mich im Launcher", value=f"<com.epicgames.launcher://store/bundles/{FreeGame['catalogNs']['mappings'][0]['pageSlug']}>", inline=True
                                                )
                                            else:
                                                EpicEmbed.add_field(
                                                    name="Besuch mich im EGS",
                                                    value=f"[Epic Games Store](https://store.epicgames.com/de/p/{FreeGame['catalogNs']['mappings'][0]['pageSlug']})",
                                                    inline=True,
                                                )
                                                EpicEmbed.add_field(
                                                    name="Hol mich im Launcher", value=f"<com.epicgames.launcher://store/p/{FreeGame['catalogNs']['mappings'][0]['pageSlug']}>", inline=True
                                                )
                                        if EpicImageURL != "":
                                            EpicImageURL = quote(EpicImageURL, safe=":/")
                                            EpicEmbed.set_image(url=f"{EpicImageURL}")
                                        EpicEmbed.set_footer(text="Bizeps_Bot")

                                        if EpicImage != "" and EpicImage:
                                            NumberOfEpicFiles = NumberOfEpicFiles + 1
                                            EpicImagePath = f"{NumberOfEpicFiles}_epic.jpg"
                                            with open(f"epic/{EpicImagePath}", "wb") as write_file:
                                                write_file.write(EpicImage)
                                        guild = self.bot.get_guild(self.bot.Server)
                                        EpicRole = discord.utils.get(guild.roles, name="Free Epic Game Alert")
                                        GamingChannel = discord.utils.get(guild.text_channels, name="gaming")
                                        await GamingChannel.send(content=f"{EpicRole.mention}", embed=EpicEmbed)
                                        logging.info(f"{FreeGame['title']} was added to free Epic Games!")
                                        # Send Epic Games to Subscribers via DM
                                        DMRoleEpic = discord.utils.get(guild.roles, name="DM Alert Epic")
                                        for user in DMRoleEpic.members:
                                            UserDM = await self.bot.get_or_fetch_user(user.id)
                                            await UserDM.send(embed=EpicEmbed)
                                            await asyncio.sleep(2)  # for ratelimiting reasons
                                            logging.info(f"Free Epic Games were sent to subscriber [{user}].")

                                except json.decoder.JSONDecodeError:
                                    logging.error("ERROR: Something bad happend with the json decoding! The Free EpicGames list was created again!", exc_info=True)
                                    self.bot.Settings["Settings"]["FreeEpicGames"] = {}
                                    self.bot.Settings["Settings"]["FreeEpicGames"].update(FreeGameObject)
                                    _write_json("Settings.json", self.bot.Settings)


def setup(bot):
    bot.add_cog(Gaming(bot))
