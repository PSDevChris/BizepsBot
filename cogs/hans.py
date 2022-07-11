from discord import Option
from discord.ext import commands
from Main import _is_banned
from Main import _get_banned_users
from Main import _read_json
from Main import logging
from Main import random
from Main import _write_json

def RefreshHansTasks():
    HansTasksJSON = _read_json('Settings.json')
    HansTasks = list(HansTasksJSON['Settings']['HansTasks']['Tasks'])
    return HansTasks

class HansTaskList(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.BannedUsers = _get_banned_users()
        self.HansTasks = RefreshHansTasks()
    

    async def cog_check(self, ctx):
        return _is_banned(ctx, self.BannedUsers)


    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    # Commands
    @commands.slash_command(name="hans", aliases=["hans", "HANS"], description="Er hat zu tun!", brief="Er hat zu tun!")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def _hanstasks(self, ctx, option: Option(str, "Zeigt, zählt oder ergänzt Hans Aufgaben", choices=["show", "count", "add"], required=False), task: Option(str, "Hans wird diese Aufgabe hinzugefügt", required=False)):
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
            await ctx.respond(f"```{HansOutputString}```")
            logging.info(f"{ctx.author.name} requested the numbers of tasks Hans has.")
        elif option == "count":
            AllHansTasks = _read_json('Settings.json')
            HansTaskCount = len(AllHansTasks['Settings']['HansTasks']['Tasks'])
            await ctx.respond(f"Hans hat {HansTaskCount} Aufgaben vor sich! So ein vielbeschäftiger Mann!")
            logging.info(f"{ctx.author} wanted to know how busy Hans is.")
        elif (option == "add" and task) or task:
            if "```" not in task:
                AllHansTasks = _read_json('Settings.json')
                AllHansTasks['Settings']['HansTasks']['Tasks'].append(task)
                _write_json('Settings.json', AllHansTasks)
                self.HansTasks.append(task)
                await ctx.respond(f"Der Task '{task}' wurde Hans hinzugefügt.")
                logging.info(f"{ctx.author.name} has added {task} to Hans tasks.")
            else:
                await ctx.respond("Das füge ich nicht hinzu.")
        elif option == "add" and not task:
            ctx.respond("Hier fehlte der Task, bitte beim hinzufügen angeben.")
        else:
            if self.HansTasks == []:
                RefreshHansTasks()
            HansTask = random.SystemRandom().choice(self.HansTasks)
            self.HansTasks.remove(HansTask)
            await ctx.respond(f"Hans muss {HansTask}...")
            logging.info(f"{ctx.author.name} wanted to know what Hans is doing all day.")

    @_hanstasks.error
    async def _hanstasks_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Dieser Befehl ist noch im Cooldown. Versuch es in {int(error.retry_after)} Sekunden nochmal.")
            logging.warning(f"{ctx.author} wanted to spam the hanscommand!")

def setup(bot):
    bot.add_cog(HansTaskList(bot))
