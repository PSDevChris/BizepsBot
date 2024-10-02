import io
import random

import discord
from discord.ext import commands

from Main import _is_banned, _read_json, _write_json, logging


def _refresh_hanstasks():
    HansTasksJSON = _read_json("Settings.json")
    logging.info("Refreshed the list of Hans Tasks.")
    random.shuffle(HansTasksJSON["Settings"]["HansTasks"]["Tasks"])
    return list(HansTasksJSON["Settings"]["HansTasks"]["Tasks"])


class HansTaskList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.HansTasks = _refresh_hanstasks()

    # Async for cog_check, normal for command_check
    async def cog_check(self, ctx):
        return await _is_banned(ctx)

    # Events

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    # Commands
    @commands.slash_command(name="hans", description="Er hat zu tun!", brief="Er hat zu tun!")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _hanstasks(
        self,
        ctx: discord.context.ApplicationContext,
        option: discord.Option(str, "Zeigt, zählt oder ergänzt Hans Aufgaben", choices=["show", "count"], required=False),
        task: discord.Option(str, "Hans wird diese Aufgabe hinzugefügt", required=False),
    ):
        if option == "show":
            HansOutputBuffer = io.StringIO()
            HansOutputLength = 0
            await ctx.respond("Hans hat folgende Tasks:\n", ephemeral=True)
            for HansTaskEntry in self.bot.Settings["Settings"]["HansTasks"]["Tasks"]:
                HansOutputLength += len(HansTaskEntry)
                if HansOutputLength >= 1994:
                    await ctx.respond(f"```{HansOutputBuffer.getvalue()}```", ephemeral=True)
                    HansOutputBuffer.truncate(0)
                    HansOutputBuffer.seek(0)  # Needs to be done in Python 3
                    HansOutputLength = 0
                HansOutputBuffer.write(HansTaskEntry + "\n")
                HansOutputLength = HansOutputLength + len(HansTaskEntry)
            if HansOutputLength > 0:
                await ctx.respond(f"```{HansOutputBuffer.getvalue()}```", ephemeral=True)
            HansOutputBuffer.close()
            logging.info(f"{ctx.author} requested the list of Hans tasks.")
        elif option == "count":
            HansTaskCount = len(self.bot.Settings["Settings"]["HansTasks"]["Tasks"])
            logging.info(f"{ctx.author} wanted to know how much tasks Hans has.")
            await ctx.respond(f"Hans hat {HansTaskCount} Aufgaben vor sich! So ein vielbeschäftiger Mann!")
        elif task:
            if "```" not in task:
                if task not in self.bot.Settings["Settings"]["HansTasks"]["Tasks"]:
                    self.bot.Settings["Settings"]["HansTasks"]["Tasks"].append(task)
                    _write_json("Settings.json", self.bot.Settings)
                    self.HansTasks.append(task)
                    random.shuffle(self.HansTasks)
                    logging.info(f"{ctx.author} has added {task} to Hans tasks.")
                    await ctx.respond(f"Der Task '{task}' wurde Hans hinzugefügt.")
                else:
                    await ctx.respond("Diese Aufgabe hat Hans bereits. Er macht Dinge ungern doppelt.")
            else:
                await ctx.respond("Das füge ich nicht hinzu.")
        else:
            if not self.HansTasks:
                await ctx.defer()  # only defer if there is a refresh
                self.HansTasks = _refresh_hanstasks()
            HansTask = self.HansTasks.pop()
            await ctx.respond(f"Hans muss {HansTask}...")
            logging.info(f"[{ctx.author}] wanted to know what Hans is doing all day, task chosen was [{HansTask}].")

    @_hanstasks.error
    async def _hanstasks_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam the hanscommand!")
        elif isinstance(error, discord.CheckFailure):
            await ctx.respond("Du bist gebannt und damit von der Verwendung des Bots ausgeschlossen.", ephemeral=True)
        else:
            logging.error(f"ERROR: {error}")


def setup(bot):
    bot.add_cog(HansTaskList(bot))
