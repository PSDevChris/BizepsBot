import asyncio
import json
import logging

import aiohttp
import discord
from discord.ext import commands

from Main import _is_banned


class SchnabiWaifu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Async for cog_check, normal for command_check
    async def cog_check(self, ctx):
        return await _is_banned(ctx)


    async def get_waifu_img(self) -> dict[str,str | list] | None:
        waifurl = "https://api.waifu.im/search"

        return_dict = {
            "url": "",
            "name": "",
            "urls": [],
        }

        async with aiohttp.ClientSession(headers={"Content-Type": "application/json"}) as aiosession, aiosession.get(waifurl) as res:
            if res.status != 200:
                logging.error("Waifu API returned status code != 200!")
                return None

            try:
                img_json = (await res.json())["images"][0]
                return_dict["url"] = img_json["url"]
                if (artist := img_json["artist"]) is not None:
                    return_dict["name"] = artist["name"]
                    return_dict["urls"] = [page[1] for page in artist.items() if page[0] in ["patreon", "pixiv", "twitter", "deviant_art"] and page[1] is not None]
                else:
                    pass
            except json.decoder.JSONDecodeError:
                logging.error("Waifu JSON Decode failed!")
                return None
            except KeyError:
                logging.error("Waifu key error: Something is wrong with the JSON file!")
                return None

            return return_dict
        
    # Commands
    @commands.slash_command(name="schnabi", description="Er malt gerne!", brief="Er malt gerne!")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _schnabi(self, ctx: discord.context.ApplicationContext):
        if (waifu_data := asyncio.run(self.get_waifu_img())) is None:
            ctx.respond("Leider ist was ganz schlimmes passiert: De Waifus sin dood! :c")
            return

        embed = discord.Embed(
            title="Hat da jemand Waifu gesagt?"
        ).set_image(
            url=waifu_data["url"]
        )

        if waifu_data["name"]:
            embed.set_author(
                name=waifu_data["name"]
            )

        if waifu_data['urls']:
            embed.description="**Artist Links:**\n" + "\n".join(waifu_data["urls"])

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(SchnabiWaifu(bot))