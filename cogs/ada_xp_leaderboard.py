import discord
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
import os
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

        guild = self.bot.get_guild(config.GUILD_ID)
        if top > 20:
            return await interaction.followup.send("<:Emoji_Think_Elvenhollow:1441146944142442567> 20 Brawlers max!")

        data = []
        for user_doc in self.xp_col.find({}):
            user_id = int(user_doc["_id"])
            level = user_doc.get("level", 0)
            xp = user_doc.get("xp", 0)
            life = user_doc.get("life", 0)

            # ID du serveur
            member = guild.get_member(user_id)

            if member:  
                name = member.display_name
            else:
                user_obj = await self.bot.fetch_user(user_id)
                name = user_obj.name

            try:
                user_obj = await self.bot.fetch_user(user_id)
                avatar_url = str(user_obj.display_avatar.url)
            except:
                avatar_url = None

            data.append((name, level, xp, life, avatar_url))

        # Trier par level puis XP
        data.sort(key=lambda x: (x[1], x[2]), reverse=True)
        data = data[:top]

        if not data:
            return await interaction.followup.send("<:Emoji_Think_Elvenhollow:1441146944142442567> No players found.")

        # Pagination : découper en pages de 10 utilisateurs
        page_size = 10
        total_pages = (len(data) - 1) // page_size + 1
        rank_start = 1
        files = []

        for page_num in range(total_pages):
            start_idx = page_num * page_size
            end_idx = start_idx + page_size
            page_data = data[start_idx:end_idx]
            leaderboard_image = await self.generate_leaderboard_image(page_data, page_num + 1, total_pages, rank_start)
            files.append(discord.File(leaderboard_image, filename=f"leaderboard_{page_num + 1}.png"))
            rank_start += len(page_data)

        for f in files:
            await interaction.followup.send(file=f)

    async def generate_leaderboard_image(self, data, page_number, total_pages, rank_start):
        width, height = 720, 900  # Taille fixe
        margin_top, margin_left = 50, 20

        if os.path.exists(self.bg_image_path):
            with Image.open(self.bg_image_path) as img:
                background = Image.open(io.BytesIO("https://i.ibb.co/4nf4bnP8/lboard.png")).convert("RGBA").resize((width, height))
        else:
            with Image.open(self.bg_image_path) as img:
                background = Image.new("RGBA", (width, height), (30, 30, 30, 255))

        draw = ImageDraw.Draw(background)

        # Fonts
        try:
            font_title = ImageFont.truetype("assets/fonts/Baloo-Regular.ttf", 36)
            font = ImageFont.truetype("assets/fonts/Baloo-Regular.ttf", 30)
        except OSError:
            font_title = ImageFont.load_default()
            font = ImageFont.load_default()

        # Titre en haut
        title_text = f"BleedingLegend 💖 XP Leaderboard {page_number}/{total_pages}"
        bbox = font_title.getbbox(title_text)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((width - w) // 2, 10), title_text, font=font_title, fill=(255, 255, 255))

        async with aiohttp.ClientSession() as session:
            for idx, (name, level, xp, life, avatar_url) in enumerate(data):
                y = margin_top + idx * 80

                # Avatar circulaire avec bordure blanche
                if avatar_url:
                    try:
                        async with session.get(avatar_url) as resp:
                            avatar_bytes = await resp.read()
                            avatar_img = Image.open(io.BytesIO(avatar_bytes)).resize((64, 64)).convert("RGBA")

                            mask = Image.new("L", (64, 64), 0)
                            mask_draw = ImageDraw.Draw(mask)
                            mask_draw.ellipse((0, 0, 64, 64), fill=255)
                            circle_avatar = Image.new("RGBA", (64, 64))
                            circle_avatar.paste(avatar_img, (0, 0), mask)

                            border = Image.new("RGBA", (68, 68), (255, 255, 255, 0))
                            border_draw = ImageDraw.Draw(border)
                            border_draw.ellipse((0, 0, 67, 67), outline=(255, 255, 255, 255), width=4)
                            border.paste(circle_avatar, (2, 2), circle_avatar)

                            background.paste(border, (margin_left, y), border)
                    except:
                        pass

                # Texte avec contour noir
                x_name, x_info = margin_left + 80, margin_left + 300
                display_name = f"{rank_start + idx}. {name}" if len(name) <= 10 else f"{rank_start + idx}. {name[:8]}_"
                text_info = f"Lvl: {level} | XP: {xp} | ❤️‍🔥 : {life}"

                def draw_text_with_outline(draw_obj, position, text, font, fill=(255,255,255), outline=(0,0,0)):
                    x, y = position
                    for dx in [-1,0,1]:
                        for dy in [-1,0,1]:
                            if dx != 0 or dy != 0:
                                draw_obj.text((x+dx, y+dy), text, font=font, fill=outline)
                    draw_obj.text((x, y), text, font=font, fill=fill)

                draw_text_with_outline(draw, (x_name, y + 20), display_name, font)
                draw_text_with_outline(draw, (x_info, y + 20), text_info, font)

        buffer = io.BytesIO()
        background.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
