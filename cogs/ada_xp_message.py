import time
import discord
import os
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import json
import random
import config

fun_messages = [
    "<:Emoji_1More_Goldforged:1430608366031474710> 1 More! Keep rising!",
    "<:Emoji_Sweat:1430608404816330842> You're leveling up like a legend!",
    "Another step to greatness, keep pushing <:Emoji_LookinGood_Swanky:1430608386189168840>!",
    "<:Emoji_Heart:1441146930221547600> Your grind is insane, don’t stop!",
    "<:Emoji_Think_Patrick:1430608408188420116> Rising… just like your XP!",
    "You’re unstoppable today <:Emoji_RIP_Interloper:1430608393458159706>!",
    "Your journey keeps getting brighter! <:Emoji_Heart_SpongeBob:1430608380510212287>",
    "<:Emoji_GG_Fenrir:1441146927227080774> A new level? Easy for you.",
    "You’re built different, fr <:Emoji_LookinGood_Fait:1430608383232442428>",
    "<:Emoji_Think_Vivi:1441146957534859376> That’s some REAL progress right there!",
    "You keep climbing… impressive <:Emoji_Shrug_Street_Sovereign:1441146941172875385>.",
    "<:Emoji_WP_Modular_Rift:1441146983992791051> Absolutely cooking the XP today!",
    "<:Emoji_Shrug_Goldforged:1441146940174893329> Another one!",
    "<:Emoji_ThumbsDown_Usurper:1430608419022176316> That XP didn’t stand a chance.",
    "<:Emoji_LookinGood_SpongeBob:1441146935950970920> Your energy is unmatched, keep going!",
    "Raising your level & the vibe <:Emoji_ThumbsUp_Puella_Papilio:1430608422709100695>.",
    "<:Emoji_Laugh_Nix_Nervous:1441146934520713246> You're farming XP like a spammer!",
    "<:Emoji_Wait_Goldforged:1441146976770068541> More XP? Easy work for you.",
    "Grinding mode: ACTIVATED <:Emoji_Rage_Miracle_Magi__Starlit:1430608390572347614>.",
    "<:Emoji_Wow_Metadev:1441146982679843048> The path to legend gets brighter!",
    "<:Emoji_ThumbsUp_King:1441146971724320981> Your progress is too clean 🔥",
    "You're glowing with XP energy! <:Emoji_Think_Santa:1441146954871607366>",
    "<:Emoji_Wow_Imugi:1430608430212714618> A new level dawns for you…",
    "Your next milestone is waiting <:Emoji_Wave_Royal_Warrior:1430608427243274290>.",
    "<:Emoji_Think_First_Day:1441146948383019059> You just keep winning today!",
    "You’re destined for something big <a:adaeatingramen:1430306964184760411>."
]

def truncate_username(txt, max_length=10):
    if len(txt) > max_length:
        return txt[:max_length - 3] + "..."
    return txt

async def embedLvlUp(self, channel, user, xp, level, life, cmd):

    # --- Image de fond ---
    if os.path.exists(self.bg_image):
        img = Image.open(self.bg_image).convert("RGBA")
    else:
        img = Image.new("RGBA", (720, 900), (44, 47, 51))

    draw = ImageDraw.Draw(img)
    font_title = ImageFont.truetype(self.font_titles, 80)
    font_text = ImageFont.truetype(self.font_number, 50)

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
    name_text = truncate_username(user.display_name, 15)
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
    x_value = 400   # Valeurs alignées à droite

    # XP
    draw_gold_text(draw, x_title, base_y, "XP", font_title)
    draw_white_emboss(draw, x_value - 140, base_y, f"{xp}", font_text)

    # LEVEL
    draw_gold_text(draw, x_title, base_y + spacing, "Level", font_title)
    draw_white_emboss(draw, x_value, base_y + spacing, f"{level}", font_text)

    # LIFE
    draw_gold_text(draw, x_title, base_y + spacing * 2, "Lifes", font_title)
    draw_white_emboss(draw, x_value, base_y + spacing * 2, f"{life}", font_text)

    # -------------------------------------------------------------------
    #                          ENVOI DE L'IMAGE
    # -------------------------------------------------------------------
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    random_message = random.choice(fun_messages)

    if cmd :
        await channel.send(content=f"{user.mention}", file=discord.File(buffer, "xp_card.png"))        
    else:
        await channel.send(content=f"{user.mention} {random_message}", file=discord.File(buffer, "xp_card.png"))

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
        self.XP_PER_REACT = config.XP_PER_REACT
        self.XP_COOLDOWN = config.XP_COOLDOWN
        self.MAX_LEVEL_PER_LIFE = config.MAX_LEVEL_PER_LIFE
        self.NUM_LIVES = config.NUM_LIVES

        # Levels to notify
        self.NOTIFY_LEVELS = [1,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,96,97,98,99]

        # Dossier images et police
        self.bg_folder = "assets/img/rank_avatar"
        self.bg_image = os.path.join(self.bg_folder, "lvl1.png")
        self.font_titles = "assets/fonts/NightHuntDemo.ttf"
        self.font_number = "assets/fonts/Baloo-Regular.ttf"

        print("🔁 XPSystem loaded")
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        # Le message où on a réagi
        message = reaction.message
        user_id = str(user.id)
        now = int(time.time())

        # On évite de donner de l'XP si la personne réagit à son propre message
        if message.author.id == user.id:
            return

        # Récupère l'utilisateur dans la DB
        user_data = self.xp_col.find_one({"_id": user_id})

        # Si pas de profil → on le crée avec XP + XP_REACT
        if not user_data:
            self.xp_col.insert_one({
                "_id": user_id,
                "xp": self.XP_PER_REACT,
                "level": 1,
                "life": 1,
                "last_message": now,
                "last_react": now,
                "code_lvl": None,
                "code_multiplicateur": 0
            })
            return

        # --- Cooldown réactions (ex : 10 sec) ---
        last_react = user_data.get("last_react", 0)
        
        if now - last_react < config.REACT_COOLDOWN:
            return

        # Multiplicateur
        multiplicator_code = str(user_data.get("code_multiplicateur", 0))
        multiplicator_value = self.MULTIPLICATORS.get(multiplicator_code, 1)

        xp_gain = config.XP_PER_REACT * multiplicator_value
        new_xp = user_data["xp"] + xp_gain
        level = user_data["level"]
        life = user_data["life"]

        leveled_up = False
        life_up = False

        # --- Vérification level up ---
        while new_xp >= self.XP_LEVELS.get(str(level), self.XP_LEVELS[str(self.MAX_LEVEL_PER_LIFE)]):
            print(f"[LEVEL UP CHECK] XP={new_xp} >= Required={self.XP_LEVELS[str(level)]} AFTER REACT")
            new_xp -= self.XP_LEVELS.get(str(level), self.XP_LEVELS[str(self.MAX_LEVEL_PER_LIFE)])
            level += 1
            leveled_up = True

            if level > self.MAX_LEVEL_PER_LIFE:
                level = 1
                life += 1
                life_up = True
                
                if life > self.NUM_LIVES:
                    life = self.NUM_LIVES
                    new_xp = self.XP_LEVELS[str(self.MAX_LEVEL_PER_LIFE)]
                    print(f"❗ MAX LIFE REACHED — Locking XP at max")
                    break

        # --- MAJ DB ---
        self.xp_col.update_one(
            {"_id": user_id},
            {"$set": {
                "xp": new_xp,
                "level": level,
                "life": life,
                "last_react": now,
                "code_lvl": user_data.get("code_lvl"),
                "code_multiplicateur": user_data.get("code_multiplicateur", 0)
            }}
        )

        print(f"[UPDATE] {message.author} | XP={new_xp} | Level={level} | Life={life}")
              
        # Envoie la carte si level-up (comme pour on_message)
        if leveled_up and (level in self.NOTIFY_LEVELS or life_up):
            announce_channel = self.bot.get_channel(config.XP_CHANNEL_ID)

            await embedLvlUp(
                self=self,
                channel=announce_channel,
                user=user,
                xp=f"{new_xp} / {self.XP_LEVELS.get(str(level), '???')}",
                level=f"{level} / {self.MAX_LEVEL_PER_LIFE}",
                life=f"{life} / {self.NUM_LIVES}",
                cmd=False
            )

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
            print(f"[LEVEL UP CHECK] XP={new_xp} >= Required={self.XP_LEVELS[str(level)]} AFTER MESSAGE")
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

        print(f"[UPDATE] {message.author} | XP={new_xp} | Level={level} | Life={life}")

        # Send embed only for key levels or life-up
        if leveled_up and (level in self.NOTIFY_LEVELS or life_up):

            announce_channel = self.bot.get_channel(config.XP_CHANNEL_ID)

            await embedLvlUp(self=self,
                channel=announce_channel,
                user=message.author,
                xp=f"{new_xp} / {self.XP_LEVELS.get(str(level), '???')}",
                level=f"{display_level} / {self.MAX_LEVEL_PER_LIFE}",
                life=f"{life} / {self.NUM_LIVES}",
                cmd=False
            )

    # --- SLASH COMMAND: DISPLAY XP PROFILE ---
    @app_commands.command(name="bl_xp_card", description="Displays your XP profile.")
    async def bl_xp_card(self, interaction: discord.Interaction):

        await interaction.response.defer()

        user_id = str(interaction.user.id)

        # Fetch from MongoDB
        user_data = self.xp_col.find_one({"_id": user_id})

        if not user_data:
            return await interaction.followup.send(
                "<:Emoji_Sweat:1430608404816330842> Your XP profile doesn't exist, are you a Ghost ???",
                ephemeral=True
            )

        # MongoDB data
        xp = user_data["xp"]
        level = user_data["level"]
        life = user_data["life"]

        # Level override (cosmetic level skin)
        display_level = user_data.get("code_lvl") or level

        # Formatted text
        xp_text = f"{xp} / {self.XP_LEVELS.get(str(level), '???')}"
        level_text = f"{display_level} / {self.MAX_LEVEL_PER_LIFE}"
        life_text = f"{life} / {self.NUM_LIVES}"

        await interaction.followup.send("Generating your XP card...", ephemeral=True)
        
        # Send XP card
        await embedLvlUp(
            self=self,
            channel=interaction.channel,
            user=interaction.user,
            xp=xp_text,
            level=level_text,
            life=life_text,
            cmd=True
        )

    @app_commands.command(name="bl_edit_card", description="Give XP / multiplicator / cosmetic level to a user")
    @app_commands.describe(
        user="The user to modify",
        xp="XP to add/subtract (optional)",
        multiplicator="Set the multiplicator code (optional)",
        code_lvl="Set a cosmetic level (optional)")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_xp(self, interaction: discord.Interaction, user: discord.Member, xp: int = None, multiplicator: str = None, code_lvl: int = None):
        await interaction.response.defer(ephemeral=True)

        user_id = str(user.id)
        user_data = self.xp_col.find_one({"_id": user_id})

        if not user_data:
            # Création si l'utilisateur n'existe pas
            user_data = {
                "_id": user_id,
                "xp": 0,
                "level": 1,
                "life": 1,
                "last_message": 0,
                "last_react": 0,
                "code_lvl": None,
                "code_multiplicateur": 0
            }
            self.xp_col.insert_one(user_data)

        # --- XP ---
        if xp is not None:
            new_xp = user_data["xp"] + xp
            level = user_data["level"]
            life = user_data["life"]
            leveled_up = False
            life_up = False

            while new_xp >= self.XP_LEVELS.get(str(level), self.XP_LEVELS[str(self.MAX_LEVEL_PER_LIFE)]):
                new_xp -= self.XP_LEVELS.get(str(level), self.XP_LEVELS[str(self.MAX_LEVEL_PER_LIFE)])
                level += 1
                leveled_up = True

                if level > self.MAX_LEVEL_PER_LIFE:
                    level = 1
                    life += 1
                    life_up = True
                    if life > self.NUM_LIVES:
                        life = self.NUM_LIVES
                        new_xp = self.XP_LEVELS[str(self.MAX_LEVEL_PER_LIFE)]
                        break

            self.xp_col.update_one(
                {"_id": user_id},
                {"$set": {
                    "xp": new_xp,
                    "level": level,
                    "life": life
                }}
            )
        else:
            new_xp = user_data["xp"]
            level = user_data["level"]
            life = user_data["life"]

        # --- Multiplicateur ---
        if multiplicator:
            if multiplicator in self.MULTIPLICATORS:
                self.xp_col.update_one(
                    {"_id": user_id},
                    {"$set": {"code_multiplicateur": multiplicator}}
                )
            else:
                await interaction.followup.send(f"Multiplicator `{multiplicator}` not found.", ephemeral=True)
                return

        # --- Cosmetic Level ---
        if code_lvl is not None:
            self.xp_col.update_one(
                {"_id": user_id},
                {"$set": {"code_lvl": code_lvl}}
            )

        await interaction.followup.send(
            f"✅ Updated {user.mention}: XP={new_xp}, Level={level}, Life={life}, "
            f"Multiplicator={multiplicator or user_data.get('code_multiplicateur')}, "
            f"CodeLvl={code_lvl or user_data.get('code_lvl')}",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(XPSystem(bot))
