# adabot.py

from discord.ext import commands
import os

class Ada(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping2(self, ctx):
        await ctx.send("Pong depuis Ada !")

async def setup(bot):
    # Ajouter le cog principal
    await bot.add_cog(Ada(bot))

    # Charger tous les cogs du dossier adacogs
    if os.path.isdir("./adacogs"):
        for filename in os.listdir("./adacogs"):
            if filename.endswith(".py") and filename != "__init__.py":
                await bot.load_extension(f"adacogs.{filename[:-3]}")
