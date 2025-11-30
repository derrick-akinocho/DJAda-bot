import time
import discord
import os
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import json
import config

def truncate_username(txt, max_length=10):
    if len(txt) > max_length:
        return txt[:max_length - 3] + "..."
    return txt

async def embedLvlUp(self, channel, user, xp, level, life):
    # --- Image de fond ---
    if os.path.exists(self.bg_image):
        img = Image.open(self.bg_image).convert("RGBA")
    else:
        img = Image.new("RGBA", (720, 900), (44, 47, 51))

    draw = ImageDraw.Draw(img)
    font_title = ImageFont.truetype(self.font_titles, 80)
    font_text = ImageFont.truetype(self.font_number, 45)

    # -------------------------------------------------------------------
    #                         AVATAR CENTRÉ EN HAUT
    # -------------------------------------------------------------------
    avatar_asset = user.display_avatar.replace(size=256)
    avatar_bytes = await avatar_asset.read()
    avatar_img = Image.open(BytesIO(avatar_bytes)).convert("RGBA")

    avatar_size = 190
    avatar_img = avatar_img.resize((avatar_size, avatar_size))

    # Masque rond
    mask = Image.new("L", (avatar_size, avatar_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)

    border_size = 10
    total_size = avatar_size + border_size * 2

    border = Image.new("RGBA", (total_size, total_size), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)
    border_draw.ellipse(
        (0, 0, total_size, total_size),
        outline=(192, 192, 192, 255),
        width=border_size
    )
    border.paste(avatar_img, (border_size, border_size), mask)

    avatar_y = 170
    img.paste(border, ((img.width - total_size) // 2, avatar_y), border)

    # -------------------------------------------------------------------
    #                         PSEUDO CENTRÉ
    # -------------------------------------------------------------------
    name_text = truncate_username(user.display_name, 10)
    bbox = draw.textbbox((0, 0), name_text, font=font_title)
    name_width = bbox[2] - bbox[0]
    text_y = avatar_y + total_size + 5

    # Ombre
    draw.text(
        ((img.width - name_width) // 2 + 4, text_y + 4),
        name_text, font=font_title, fill=(74, 74, 74)
    )

    # Texte blanc
    draw.text(
        ((img.width - name_width) // 2, text_y),
        name_text, font=font_title, fill=(255, 255, 255)
    )

    # -------------------------------------------------------------------
    #                 FONCTIONS D’EFFETS DE TEXTE
    # -------------------------------------------------------------------
    def draw_gold_text(draw, x, y, text, font):
        top = (212, 155, 39)
        bottom = (240, 173, 38)
        shadow = (46, 45, 45)
        draw.text((x + 4, y + 4), text, font=font, fill=shadow)
        draw.text((x, y), text, font=font, fill=top)
        draw.text((x, y + 2), text, font=font, fill=bottom)

    def draw_white_emboss(draw, x, y, text, font):
        draw.text((x + 3, y + 3), text, font=font, fill=(46, 45, 45))
        draw.text((x - 2, y - 2), text, font=font, fill=(226, 226, 226))
        draw.text((x, y), text, font=font, fill=(255, 255, 255))

    # -------------------------------------------------------------------
    #                 ALIGNEMENT GAUCHE FIXE DES INFOS
    # -------------------------------------------------------------------
    base_y = text_y + 70
    spacing = 70
    x_title = 150   # Titres à gauche
    x_value = 380   # Valeurs alignées à droite

    # XP
    draw_gold_text(draw, x_title, base_y, "XP", font_title)
    draw_white_emboss(draw, x_value - 80, base_y + 15, f"{xp}", font_text)

    # LEVEL
    draw_gold_text(draw, x_title, base_y + spacing, "Level", font_title)
    draw_white_emboss(draw, x_value, base_y + spacing + 15, f"{level}", font_text)

    # LIFE
    draw_gold_text(draw, x_title, base_y + spacing * 2, "Life", font_title)
    draw_white_emboss(draw, x_value, base_y + spacing * 2 + 15, f"{life}", font_text)

    # -------------------------------------------------------------------
    #                          ENVOI DE L'IMAGE
    # -------------------------------------------------------------------
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    await channel.send(file=discord.File(buffer, "xp_card.png"))

class XPSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Load JSON
        json_path = os.path.join(os.path.dirname(__file__), "../res", "xp_lvl.json")
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            self.XP_LEVELS = data["levels"]
            self.MULTIPLICATORS = data["multiplicators"]

        # MongoDB
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client[config.DATABASE_NAME]
        self.xp_col = self.db[config.COLLECTION_XP_MESSAGES_STATUS]

        # XP Config
        self.XP_PER_MESSAGE = config.XP_PER_MESSAGE
        self.XP_COOLDOWN = config.XP_COOLDOWN
        self.MAX_LEVEL_PER_LIFE = config.MAX_LEVEL_PER_LIFE
        self.NUM_LIVES = config.NUM_LIVES

        # Levels to notify
        self.NOTIFY_LEVELS = [1,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,96,97,98,99]

        # Dossier images et police
        self.bg_folder = "assets/img/rank_avatar"
        self.bg_image = os.path.join(self.bg_folder, "lvl1.png")
        self.font_titles = "assets/fonts/NightHuntDemo.ttf"
        self.font_number = "assets/fonts/BreatheFire.otf"

        print("🔁 XPSystem loaded")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        now = int(time.time())

        user = self.xp_col.find_one({"_id": user_id})

        # First time → create document
        if not user:
            print(f"[NEW USER] Created XP profile for {message.author} ({user_id})")
            self.xp_col.insert_one({
                "_id": user_id,
                "xp": self.XP_PER_MESSAGE,
                "level": 1,
                "life": 1,
                "last_message": now,
                "code_lvl": None,
                "code_multiplicateur": 0
            })
            return

        # Anti-spam
        if now - user.get("last_message", 0) < self.XP_COOLDOWN:
            print(f"[COOLDOWN] {message.author} ({user_id}) | Message ignored")
            return

        # Multiplicator (stored key)
        multiplicator_code = str(user.get("code_multiplicateur", 0))
        multiplicator_value = self.MULTIPLICATORS.get(multiplicator_code, 1)

        print(
            f"[XP GAIN] {message.author} | BaseXP={self.XP_PER_MESSAGE} | "
            f"Multi={multiplicator_value} | TotalGain={self.XP_PER_MESSAGE * multiplicator_value}"
        )

        # Add XP
        new_xp = user["xp"] + self.XP_PER_MESSAGE * multiplicator_value
        level = user["level"]
        life = user["life"]

        leveled_up = False
        life_up = False

        while new_xp >= self.XP_LEVELS.get(str(level), self.XP_LEVELS[str(self.MAX_LEVEL_PER_LIFE)]):
            print(f"[LEVEL UP CHECK] XP={new_xp} >= Required={self.XP_LEVELS[str(level)]}")
            new_xp -= self.XP_LEVELS.get(str(level), self.XP_LEVELS[str(self.MAX_LEVEL_PER_LIFE)])
            level += 1
            leveled_up = True

            # Life-up
            if level > self.MAX_LEVEL_PER_LIFE:
                level = 1
                life += 1
                life_up = True
                print(f"🔥 LIFE UP! {message.author} → Life {life}")

                if life > self.NUM_LIVES:
                    life = self.NUM_LIVES
                    new_xp = self.XP_LEVELS[str(self.MAX_LEVEL_PER_LIFE)]
                    print(f"❗ MAX LIFE REACHED — Locking XP at max")
                    break

        # Update DB
        self.xp_col.update_one(
            {"_id": user_id},
            {"$set": {
                "xp": new_xp,
                "level": level,
                "life": life,
                "last_message": now,
                "code_lvl": user.get("code_lvl"),
                "code_multiplicateur": user.get("code_multiplicateur", 0)
            }}
        )

        display_level = user.get("code_lvl") or level

        print(
            f"[UPDATE] {message.author} | XP={new_xp} | Level={level} | Life={life}"
        )

        # Send embed only for key levels or life-up
        if leveled_up and (level in self.NOTIFY_LEVELS or life_up):
            
            announce_channel = self.bot.get_channel(config.XP_CHANNEL_ID)

            await embedLvlUp(self=self,
                channel=announce_channel,
                user=message.author,
                xp={new_xp} / {self.XP_LEVELS.get(str(level), '???')},
                level={display_level}/{self.MAX_LEVEL_PER_LIFE}, life={life}/{self.NUM_LIVES}
            )

async def setup(bot):
    await bot.add_cog(XPSystem(bot))
