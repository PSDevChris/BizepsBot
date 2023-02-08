import random

import discord
from discord import Option
from discord.ext import commands

from Main import _is_banned, _read_json, _write_json, logging


def _refresh_hanstasks():
    HansTasksJSON = _read_json('Settings.json')
    HansTasks = list(HansTasksJSON['Settings']['HansTasks']['Tasks'])
    return HansTasks


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
    async def _hanstasks(self, ctx: discord.context.ApplicationContext, option: Option(str, "Zeigt, zählt oder ergänzt Hans Aufgaben", choices=["show", "count"], required=False), task: Option(str, "Hans wird diese Aufgabe hinzugefügt", required=False)):
        if option == "show":
            AllHansTasks = _read_json('Settings.json')
            HansOutputString = ""
            HansOutputLength = 0
            await ctx.respond(f"Hans hat folgende Tasks:\n")
            for HansTaskEntry in AllHansTasks['Settings']['HansTasks']['Tasks']:
                HansOutputLength += len(HansTaskEntry)
                if HansOutputLength >= 1994:
                    await ctx.respond(f"```{HansOutputString}```")
                    HansOutputString = ""
                    HansOutputLength = 0
                HansOutputString += HansTaskEntry + "\n"
                HansOutputLength = HansOutputLength + len(HansTaskEntry)
            logging.info(
                f"{ctx.author.name} requested the list of Hans tasks.")
            await ctx.respond(f"```{HansOutputString}```")
        elif option == "count":
            AllHansTasks = _read_json('Settings.json')
            HansTaskCount = len(AllHansTasks['Settings']['HansTasks']['Tasks'])
            logging.info(
                f"{ctx.author} wanted to know how much tasks Hans has.")
            await ctx.respond(f"Hans hat {HansTaskCount} Aufgaben vor sich! So ein vielbeschäftiger Mann!")
        elif task:
            if "```" not in task:
                AllHansTasks = _read_json('Settings.json')
                AllHansTasks['Settings']['HansTasks']['Tasks'].append(task)
                _write_json('Settings.json', AllHansTasks)
                self.HansTasks.append(task)
                logging.info(
                    f"{ctx.author} has added {task} to Hans tasks.")
                await ctx.respond(f"Der Task '{task}' wurde Hans hinzugefügt.")
            else:
                await ctx.respond("Das füge ich nicht hinzu.")
        else:
            if self.HansTasks == []:
                _refresh_hanstasks()
            HansTask = random.SystemRandom().choice(self.HansTasks)
            self.HansTasks.remove(HansTask)
            logging.info(
                f"[{ctx.author}] wanted to know what Hans is doing all day, task chosen was [{HansTask}].")
            await ctx.defer()
            await ctx.followup.send(f"Hans muss {HansTask}...")

    @_hanstasks.error
    async def _hanstasks_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam the hanscommand!")
        elif isinstance(error, discord.CheckFailure):
            await ctx.respond(f"Du bist gebannt und damit von der Verwendung des Bots ausgeschlossen.", ephemeral=True)
        else:
            logging.error(f"ERROR: {error}")


def setup(bot):
    bot.add_cog(HansTaskList(bot))
