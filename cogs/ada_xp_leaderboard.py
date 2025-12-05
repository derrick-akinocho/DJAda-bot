import discord
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient
from discord.ui import View, Button
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
import config

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client[config.DATABASE_NAME]
        self.xp_col = self.db[config.COLLECTION_XP_MESSAGES_STATUS]

    @app_commands.command(name="bl_xp_leaderboard", description="Display the XP leaderboard")
    @app_commands.describe(top="Number of players to display (default 10)")
    async def bl_xp_leaderboard(self, interaction: discord.Interaction, top: int = 10):
        await interaction.response.defer()

        data = []
        for user_doc in self.xp_col.find({}):
            user_id = int(user_doc["_id"])
            level = user_doc.get("level", 0)
            xp = user_doc.get("xp", 0)
            life = user_doc.get("life", 0)
            try:
                user_obj = await self.bot.fetch_user(user_id)
                name = user_obj.name
                avatar_url = str(user_obj.display_avatar.url)
            except:
                name = f"Unknown ({user_id})"
                avatar_url = None
            data.append((name, level, xp, life, avatar_url))

        data.sort(key=lambda x: (x[1], x[2]), reverse=True)
        data = data[:top]

        if not data:
            return await interaction.followup.send("<:Emoji_Think_Elvenhollow:1441146944142442567> No players found.")

        # Découper en pages de 10 utilisateurs
        page_size = 10
        files = []
        for i in range(0, len(data), page_size):
            page_data = data[i:i + page_size]
            leaderboard_image = await self.generate_leaderboard_image(page_data)
            files.append(discord.File(leaderboard_image, filename=f"leaderboard_{i//page_size + 1}.png"))

        # Envoyer toutes les images
        for f in files:
            await interaction.followup.send(file=f)

    async def generate_leaderboard_image(self, data):
        width, height = 600, 80 * len(data)
        # Charger un arrière-plan si disponible, sinon fond gris
        try:
            background = Image.open("assets/background.png").convert("RGBA").resize((width, height))
        except:
            background = Image.new("RGBA", (width, height), (30, 30, 30, 255))

        draw = ImageDraw.Draw(background)
        
        # Charger une font avec fallback
        try:
            font = ImageFont.truetype("assets/fonts/Baloo-Regular.ttf", 24)
        except OSError:
            font = ImageFont.load_default()

        async with aiohttp.ClientSession() as session:
            for idx, (name, level, xp, life, avatar_url) in enumerate(data):
                y = idx * 80
                # Avatar
                if avatar_url:
                    try:
                        async with session.get(avatar_url) as resp:
                            avatar_bytes = await resp.read()
                            avatar_img = Image.open(io.BytesIO(avatar_bytes)).resize((64, 64))
                            background.paste(avatar_img, (10, y + 8), avatar_img.convert("RGBA"))
                    except:
                        pass
                # Texte
                draw.text((90, y + 20), f"{idx+1}. {name}", fill=(255, 255, 255), font=font)
                draw.text((300, y + 20), f"Level: {level} | XP: {xp} | Life: {life}", fill=(255, 255, 255), font=font)

        buffer = io.BytesIO()
        background.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
