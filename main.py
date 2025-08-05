import os

import discord
from discord.ext import commands
import asyncio
import dotenv

import cog.misc
import cog.music


async def main():
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(intents=intents, command_prefix="/", help_command=None)

    await bot.add_cog(cog.misc.MiscCog(bot))
    await bot.add_cog(cog.music.MusicCog(bot))

    dotenv.load_dotenv()
    token = os.getenv("TOKEN")
    if token:
        await bot.start(token=token)
    else:
        raise Exception("token isnt defined. create .env file with discord bot token")

if __name__ == "__main__":
    asyncio.run(main())
