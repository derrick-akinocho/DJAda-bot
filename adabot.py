import discord
from discord.ext import commands
import os, asyncio
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def load_games():
    for filename in os.listdir("./adacogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"adacogs.{filename[:-3]}")
            print(f"🎮 Loaded: {filename[:-3]}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

async def main():
    async with bot:
        await load_games()
        await bot.start(os.getenv("TOKEN"))

asyncio.run(main())