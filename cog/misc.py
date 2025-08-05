from discord.app_commands.checks import has_permissions
from discord.ext import commands
import discord


class MiscCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=f"/help | bot"))

    @has_permissions(administrator=True)
    @commands.hybrid_command(name="sync", with_app_command=True)
    async def sync(self, ctx):
        synced = await self.bot.tree.sync()
        await ctx.reply(f"synced {synced} commands")

    @commands.hybrid_command(name="help", with_app_command=True)
    async def help(self, ctx: commands.Context):
        await ctx.reply(f"""
Команды :
```
{self.bot.command_prefix}help - это меню
{self.bot.command_prefix}queue - очередь
{self.bot.command_prefix}play <песня> - играть песню
{self.bot.command_prefix}skip - пропустить песню, которая сейчас играет
{self.bot.command_prefix}clear - очистить очередь
{self.bot.command_prefix}stop - выйти из голосового чата
{self.bot.command_prefix}pause - поставить бота на паузу / продолжить
{self.bot.command_prefix}remove <номер> - убирает песню в очереди с выбранным номером 
{self.bot.command_prefix}loop - зацикливает песню, которая сейчас играет
```
""")
