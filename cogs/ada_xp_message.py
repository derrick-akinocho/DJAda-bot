import time
import discord
import os
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient
from discord.ui import View, Button
from discord import Embed
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import json
import random
import config
import asyncio

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

# --------- Vérification rôle (serveur uniquement) ---------
def has_admin_role():
    async def predicate(interaction: discord.Interaction):
        # Si c'est un DM, autoriser par défaut
        if isinstance(interaction.channel, discord.DMChannel):
            return True
        required_role_id = 1374667434799136861
        return any(r.id == required_role_id for r in interaction.user.roles)
    return app_commands.check(predicate)

def truncate_username(txt, max_length=10):
    if len(txt) > max_length:
        return txt[:max_length - 3] + "..."
    return txt

async def embedLvlUp(self, channel, user, xp, level, life, cmd, code_lvl=None):

    # --- Image de fond ---
    if os.path.exists(self.bg_image):
        img = Image.open(self.bg_image).convert("RGBA")
    else:
        img = Image.new("RGBA", (720, 900), (44, 47, 51))

    draw = ImageDraw.Draw(img)
    font_title = ImageFont.truetype(self.font_titles, 80)
    font_text = ImageFont.truetype(self.font_number, 50)

    # -------------------------------------------------------------------
    #                 AFFICHAGE MULTIPLICATEUR
    # -------------------------------------------------------------------
    user_boost = self.boost_col.find_one({"_id": str(user.id)}) or {}
    print(f"[DEBUG] user_boost raw: {user_boost}, type: {type(user_boost)}")

    multiplicator_user = 0
    if user_boost:
        start = user_boost.get("multiplicateur_start", 0)
        expire = user_boost.get("multiplicateur_expire", 0)
        boost_value = user_boost.get("multiplicateur", 0)
        print(f"[DEBUG] user boost start: {start}, expire: {expire}, value: {boost_value}")
        if expire > start:
            multiplicator_user = self.MULTIPLICATORS.get(boost_value, 0)
            print(f"[DEBUG] multiplicator_user resolved: {multiplicator_user}")
        else:
            print("[DEBUG] user boost expired or invalid")

    global_boost = self.global_boost_col.find_one({"_id": "global_boost"}) or {}
    print(f"[DEBUG] global_boost raw: {global_boost}, type: {type(global_boost)}")

    multiplicator_global = 0
    if global_boost:
        start = global_boost.get("start", 0)
        expire = global_boost.get("expire", 0)
        boost_value = global_boost.get("multiplicator", None)
        print(f"[DEBUG] global boost start: {start}, expire: {expire}, value: {boost_value}")
        
        if start is not None and expire is not None and expire > start:
            if boost_value in self.MULTIPLICATORS:
                multiplicator_global = self.MULTIPLICATORS[boost_value]
            else:
                print(f"[DEBUG] global boost value {boost_value} not in MULTIPLICATORS, defaulting to 0")
                multiplicator_global = 0
        else:
            print("[DEBUG] global boost expired or invalid")

    print(f"[DEBUG] Final multiplicators => user: {multiplicator_user}, global: {multiplicator_global}")


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

    def draw_yellow_emboss(draw, x, y, text, font):
        draw.text((x + 3, y + 3), text, font=font, fill=(46, 45, 45))
        draw.text((x - 2, y - 2), text, font=font, fill=(224, 187, 0))
        draw.text((x, y), text, font=font, fill=(255, 219, 46))
    
    def draw_active_emboss(draw, x, y, text, font):
        draw.text((x + 3, y + 3), text, font=font, fill=(46, 45, 45))
        draw.text((x - 2, y - 2), text, font=font, fill=(77, 158, 68))
        draw.text((x, y), text, font=font, fill=(74, 245, 86))

    # -------------------------------------------------------------------
    #                 ALIGNEMENT GAUCHE FIXE DES INFOS
    # -------------------------------------------------------------------

    # Affiche multiplicateur si > 1
    if multiplicator_user > 1:
        draw_gold_text(draw, img.width - 180, avatar_y + total_size - 40, f"x{multiplicator_user}", font_text)

    if multiplicator_global > 1:
        draw_yellow_emboss(draw, img.width - 140, avatar_y + total_size - 40, f"x{multiplicator_global}", font_text)

    base_y = text_y + 70
    spacing = 70
    x_title = 150   # Titres à gauche
    x_value = 400   # Valeurs alignées à droite

    # XP
    draw_gold_text(draw, x_title, base_y, "XP", font_title)
    draw_white_emboss(draw, x_value - 140, base_y, f"{xp}", font_text)

    # LEVEL
    draw_gold_text(draw, x_title, base_y + spacing, "Level", font_title)

    if code_lvl is not None and code_lvl > 0:
        draw_active_emboss(draw, x_value, base_y + spacing, f"{code_lvl} / {self.MAX_LEVEL_PER_LIFE}", font_text)
    else:
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

async def add_temporary_boost(self, user_id: str, multiplicator: str = None, code_lvl: int = None, duration: int = None):
    """
    Ajoute un multiplicateur/code_lvl temporaire pour un utilisateur.
    Crée le document dans xp_boosts si nécessaire et enregistre start/expire pour chaque boost.
    """
    now = int(time.time())
    duration = duration or config.DEFAULT_XP_BOOST_DURATION

    # Vérifie si un document existe déjà
    boost_doc = self.boost_col.find_one({"_id": user_id}) or {"_id": user_id}

    # --- Multiplicateur ---
    if multiplicator:
        boost_doc["multiplicateur"] = multiplicator
        if duration:
            boost_doc["multiplicateur_start"] = now
            boost_doc["multiplicateur_expire"] = now + duration
        else:
            boost_doc["multiplicateur_start"] = None
            boost_doc["multiplicateur_expire"] = None

        # Mise à jour immédiate dans xp_col
        self.xp_col.update_one(
            {"_id": user_id},
            {"$set": {"code_multiplicateur": multiplicator}},
            upsert=True
        )

    # --- Code level ---
    if code_lvl is not None:
        boost_doc["code_lvl"] = code_lvl
        if duration:
            boost_doc["code_lvl_start"] = now
            boost_doc["code_lvl_expire"] = now + duration
        else:
            boost_doc["code_lvl_start"] = None
            boost_doc["code_lvl_expire"] = None

        # Mise à jour immédiate dans xp_col
        self.xp_col.update_one(
            {"_id": user_id},
            {"$set": {"code_lvl": code_lvl}},
            upsert=True
        )

    # --- Enregistrement dans la collection xp_boosts ---
    self.boost_col.update_one(
        {"_id": user_id},
        {"$set": boost_doc},
        upsert=True
    )

    print(f"[BOOST ADDED] User={user_id}, Multiplicator={multiplicator}, CodeLvl={code_lvl}, Duration={duration}")

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
        self.global_boost_col = self.db[config.COLLECTION_XP_GLOBAL_BOOST]
        self.boost_col = self.db[config.COLLECTION_XP_BOOST_USER]
        self.xp_col = self.db[config.COLLECTION_XP_MESSAGES_STATUS]

        # XP Config
        self.XP_PER_MESSAGE = config.XP_PER_MESSAGE
        self.XP_PER_REACT = config.XP_PER_REACT
        self.XP_COOLDOWN = config.XP_COOLDOWN
        self.MAX_LEVEL_PER_LIFE = config.MAX_LEVEL_PER_LIFE
        self.NUM_LIVES = config.NUM_LIVES

        # Levels to notify
        self.NOTIFY_LEVELS = [1,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,96,97,98,99]

        self.bot.loop.create_task(self.check_global_boost_loop())
        self.bot.loop.create_task(self.check_boosts_loop())

        # Dossier images et police
        self.bg_folder = "assets/img/rank_avatar"
        self.bg_image = os.path.join(self.bg_folder, "lvl1.png")
        self.font_titles = "assets/fonts/NightHuntDemo.ttf"
        self.font_number = "assets/fonts/Baloo-Regular.ttf"
        print("🔁 XPSystem loaded")
    
    # --- FUNCTION: CREATE PAGINATION VIEW ---
    def _create_pagination_view(self, pages, current_page):
        view = View()
        max_page = len(pages) - 1

        async def go_prev(interaction2):
            nonlocal current_page
            if current_page > 0:
                current_page -= 1
                await interaction2.response.edit_message(embed=pages[current_page], view=self._create_pagination_view(pages, current_page))

        async def go_next(interaction2):
            nonlocal current_page
            if current_page < max_page:
                current_page += 1
                await interaction2.response.edit_message(embed=pages[current_page], view=self._create_pagination_view(pages, current_page))

        btn_prev = Button(label="◀", style=discord.ButtonStyle.gray)
        btn_prev.callback = go_prev
        btn_next = Button(label="▶", style=discord.ButtonStyle.gray)
        btn_next.callback = go_next

        if max_page > 0:
            view.add_item(btn_prev)
            view.add_item(btn_next)

        return view

    async def activate_global_boost(self, multiplicator: str, duration: int):
        now = time.time()
        duration = duration or config.DEFAULT_XP_BOOST_DURATION
        
        # Ajouter ou mettre à jour le document global dans DB
        self.global_boost_col.update_one(
            {"_id": "global_boost"},
            {"$set": {"multiplicator":  str(multiplicator), "start": now, "expire": now + duration}},
            upsert=True
        )

        print(f"[GLOBAL BOOST] Boost x{multiplicator} activé pour {duration}s")
    
    # --- Loop for checking global boost ---
    async def check_global_boost_loop(self):
        await self.bot.wait_until_ready()
        log_channel = self.bot.get_channel(config.ADA_XP_BOOST_LOG_CHANNEL_ID)
        
        while not self.bot.is_closed():
            doc = self.global_boost_col.find_one({"_id": "global_boost"})
            if doc:
                now = time.time()
                multiplicator = doc["multiplicator"]
                expire = doc["expire"]
                start = doc.get("start", expire - 1)

                duration = int(expire - start)
                if duration < 0:
                    duration = 0  # Sécurité anti bug

                if now >= expire:
                    # Log to Discord
                    if log_channel:
                        await log_channel.send(
                            f"⚡ Global XP Boost **x{multiplicator}** has ended!\n"
                            f"Duration: {duration} seconds\n"
                            f"Start: <t:{int(start)}:F>\n"
                            f"End: <t:{int(expire)}:F>"
                        )
                    # Delete from DB
                    self.global_boost_col.delete_one({"_id": "global_boost"})
                    print(f"[GLOBAL BOOST END] Boost x{multiplicator} expired and removed from DB")

            await asyncio.sleep(config.DURATION_LOOP_BOOST)

    async def check_boosts_loop(self):
        await self.bot.wait_until_ready()
        log_channel = self.bot.get_channel(config.ADA_XP_BOOST_LOG_CHANNEL_ID)

        while not self.bot.is_closed():
            now = int(time.time())

            for boost in self.boost_col.find({}):
                user_id = boost["_id"]

                # Récup du user dans xp_col
                user = self.xp_col.find_one({"_id": user_id})
                if not user:
                    # Si user n'existe pas, on peut supprimer le boost
                    self.boost_col.delete_one({"_id": user_id})
                    continue

                update_needed = False
                update_fields = {}
                log_lines = []

                # --- Vérification multiplicateur ---
                multiplicator = boost.get("multiplicateur")
                expire_multi = boost.get("multiplicateur_expire")
                start_multi = boost.get("multiplicateur_start")

                if multiplicator and expire_multi and now >= expire_multi:
                    update_fields["code_multiplicateur"] = 0
                    boost["multiplicateur"] = None
                    boost["multiplicateur_expire"] = None
                    boost["multiplicateur_start"] = None
                    update_needed = True
                    log_lines.append(f"Multiplicator x{multiplicator} expired (started <t:{start_multi}:F>)")

                    # Log sur Discord
                    if log_channel and log_lines:
                        user_obj = self.bot.get_user(int(user_id))
                        name = user_obj.display_name if user_obj else user_id
                        await log_channel.send(
                            f"<:Emoji_BRB_SpongeBob:1430608368963420291> Temporary XP boost update for **{name}**!\n" +
                            "\n".join(log_lines) +
                            f"\nCheck time: <t:{expire_multi}:F>"
                        )

                # --- Vérification code_lvl ---
                code_lvl = boost.get("code_lvl")
                expire_lvl = boost.get("code_lvl_expire")
                start_lvl = boost.get("code_lvl_start")

                if code_lvl and expire_lvl and now >= expire_lvl:
                    update_fields["code_lvl"] = None
                    boost["code_lvl"] = None
                    boost["code_lvl_expire"] = None
                    boost["code_lvl_start"] = None
                    update_needed = True
                    log_lines.append(f"Cosmetic Level {code_lvl} expired (started <t:{start_lvl}:F>)")

                    # Log sur Discord
                    if log_channel and log_lines:
                        user_obj = self.bot.get_user(int(user_id))
                        name = user_obj.display_name if user_obj else user_id
                        await log_channel.send(
                            f"<a:adaeatingramen:1430306964184760411> Temporary XP boost update for **{name}**!\n" +
                            "\n".join(log_lines) + f"\nCheck time: <t:{expire_lvl}:F>")

                # --- Mettre à jour xp_col si nécessaire ---
                if update_needed:
                    self.xp_col.update_one({"_id": user_id}, {"$set": update_fields})

                # --- Supprimer le document seulement si aucun boost actif ---
                if not boost.get("multiplicateur") and not boost.get("code_lvl"):
                    self.boost_col.delete_one({"_id": user_id})
                    print(f"[BOOST REMOVED] All temporary boosts expired for user {user_id}")

            await asyncio.sleep(config.DURATION_LOOP_BOOST)

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

        # Multiplicateur perso
        multiplicator_value = self.MULTIPLICATORS.get(multiplicator_code, 1)

        global_boost = await self.global_boost_col.find_one({"_id": "global_boost"}) or {}
        global_multiplicator = 0
    
        if global_boost and global_boost.get("expire", 0) > global_boost.get("start", 0):
            global_multiplicator = self.MULTIPLICATORS.get(global_boost.get("multiplicator", 0))
            multiplicator_value *= global_multiplicator

        xp_gain = config.XP_PER_REACT * multiplicator_value
        new_xp = user_data["xp"] + xp_gain
        level = user_data["level"]
        life = user_data["life"]
        code_lvl = user_data["code_lvl"]

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
                cmd=False,
                code_lvl=code_lvl
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
        # Multiplicateur perso
        multiplicator_value = self.MULTIPLICATORS.get(multiplicator_code, 1)

        global_boost = self.global_boost_col.find_one({"_id": "global_boost"}) or {}
        global_multiplicator = 0
    
        if global_boost and global_boost.get("expire", 0) > global_boost.get("start", 0):
            global_multiplicator = self.MULTIPLICATORS.get(global_boost.get("multiplicator", 0))
            multiplicator_value *= global_multiplicator


        print(
            f"[XP GAIN] {message.author} | BaseXP={self.XP_PER_MESSAGE} | "
            f"Multi={multiplicator_value} | TotalGain={self.XP_PER_MESSAGE * multiplicator_value}"
        )

        # Add XP
        new_xp = user["xp"] + self.XP_PER_MESSAGE * multiplicator_value
        level = user["level"]
        life = user["life"]
        code_lvl = user["code_lvl"]

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
                cmd=False,
                code_lvl=code_lvl)

    # --- SLASH COMMAND: DISPLAY XP PROFILE ---
    @app_commands.command(name="bl_xp_card", description="Displays your XP profile.")
    @app_commands.describe(user="Optional: view another user's XP profile (admin only)")
    async def bl_xp_card(self, interaction: discord.Interaction, user: discord.Member = None):

        await interaction.response.defer()

        # Si aucun user spécifié, on prend celui qui exécute la commande
        target_user = user or interaction.user
        user_id = str(target_user.id)

        # Si c'est un autre utilisateur et que le commandant n'est pas admin
        if user and not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send(
                "<a:adaeatingramen:1430306964184760411>", ephemeral=True)

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
        code_lvl = user_data["code_lvl"]

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
            cmd=True,
            code_lvl=code_lvl)

    @app_commands.command(name="bl_edit_card", description="Give XP / multiplicator / cosmetic level to a user")
    @has_admin_role()
    @app_commands.describe(
        user="The user to modify",
        xp="XP to add/subtract (optional)",
        multiplicator="Set the multiplicator code (optional)",
        code_lvl="Set a cosmetic level (optional)",
        duration="Duration of multiplicator/code_lvl in seconds (optional)")
    async def bl_edit_card(self, interaction: discord.Interaction, user: discord.Member, xp: int = None, multiplicator: str = None, code_lvl: int = None, duration: int = None):
        await interaction.response.defer(ephemeral=True)

        user_id = str(user.id)
        user_data = self.xp_col.find_one({"_id": user_id})

        # Création si l'utilisateur n'existe pas
        if not user_data:
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
                {"$set": {"xp": new_xp, "level": level, "life": life}}
            )
        else:
            new_xp = user_data["xp"]
            level = user_data["level"]
            life = user_data["life"]

        # --- Multiplicateur / CodeLvl temporaire ---
        if multiplicator or code_lvl is not None:
            await add_temporary_boost(self, user_id, multiplicator=multiplicator, code_lvl=code_lvl, duration=duration)

        await interaction.followup.send(
            f"✅ Updated {user.mention}: XP={new_xp}, Level={level}, Life={life}, "
            f"Multiplicator={multiplicator or user_data.get('code_multiplicateur')}, "
            f"CodeLvl={code_lvl or user_data.get('code_lvl')}, Duration={duration}",
            ephemeral=True
        )

    # --- Commande slash pour lancer le boost ---
    @app_commands.command(name="bl_global_boost", description="Activate a temporary global XP boost")
    @has_admin_role()
    @app_commands.describe(multiplicator="Value (ex: 2)", duration="Duration in seconds")
    async def global_boost(self, interaction: discord.Interaction, multiplicator: int, duration: int):
        await interaction.response.send_message( f"🚀 Global Boost XP x{multiplicator} activate for {duration}s", ephemeral=True)
        await self.activate_global_boost(multiplicator, duration)

    # --- COMMAND /bl_boost ---
    @app_commands.command(name="bl_show_boost", description="Display temporary XP boosts for a user or all users")
    @has_admin_role()
    @app_commands.describe(user="Optional: specify a user")
    async def bl_show_boost(self, interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer(ephemeral=True)

        boosts = list(self.boost_col.find({}))

        if user:
            user_id = str(user.id)
            boost = next((b for b in boosts if b["_id"] == user_id), None)
            if not boost:
                return await interaction.followup.send(f"No active boost found for {user.mention}", ephemeral=True)

            embed = Embed(title=f"Boosts for {user.display_name}", color=0xFFD700)
            embed.add_field(name="Multiplicator", value=str(boost.get("multiplicateur", "None")), inline=True)
            embed.add_field(name="Cosmetic Level", value=str(boost.get("code_lvl", "None")), inline=True)
            if boost.get("multiplicateur_expire"):
                embed.add_field(name="Multiplicator expires", value=f"<t:{boost['multiplicateur_expire']}:R>", inline=False)
            if boost.get("code_lvl_expire"):
                embed.add_field(name="CodeLvl expires", value=f"<t:{boost['code_lvl_expire']}:R>", inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Si aucun user spécifié → lister tous les boosts
        pages = []
        for boost in boosts:
            user_obj = self.bot.get_user(int(boost["_id"]))
            name = user_obj.display_name if user_obj else boost["_id"]
            embed = Embed(title=f"Boosts for {name}", color=0xFFD700)
            embed.add_field(name="Multiplicator", value=str(boost.get("multiplicateur", "None")), inline=True)
            embed.add_field(name="Cosmetic Level", value=str(boost.get("code_lvl", "None")), inline=True)
            if boost.get("multiplicateur_expire"):
                embed.add_field(name="Multiplicator expires", value=f"<t:{boost['multiplicateur_expire']}:R>", inline=False)
            if boost.get("code_lvl_expire"):
                embed.add_field(name="CodeLvl expires", value=f"<t:{boost['code_lvl_expire']}:R>", inline=False)
            pages.append(embed)

        if not pages:
            return await interaction.followup.send("<:Emoji_Shrug_High_Priestess:1430608398466027682> No active boosts found.", ephemeral=True)

        # Pagination simple
        current_page = 0
        msg = await interaction.followup.send(embed=pages[current_page], ephemeral=True, view=self._create_pagination_view(pages, current_page))

    # --- COMMAND /bl_global_boosts ---
    @app_commands.command(name="bl_show_global_boosts", description="Display all global XP boosts")
    @has_admin_role()
    async def bl_show_global_boosts(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        boosts = list(self.global_boost_col.find({}))
        if not boosts:
            return await interaction.followup.send("<:Emoji_Shrug_High_Priestess:1430608398466027682> No global boosts active.", ephemeral=True)

        pages = []
        for boost in boosts:
            embed = Embed(title="Global Boost", color=0x00FF00)
            embed.add_field(name="Multiplicator", value=str(boost.get("multiplicator", "None")), inline=True)
            embed.add_field(name="Start", value=f"<t:{int(boost.get('start',0))}:F>", inline=True)
            embed.add_field(name="Expire", value=f"<t:{int(boost.get('expire',0))}:F>", inline=True)
            pages.append(embed)

        current_page = 0
        await interaction.followup.send(embed=pages[current_page], ephemeral=True, view=self._create_pagination_view(pages, current_page))

    @global_boost.error
    async def global_boost_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send("<:Emoji_Think_Goldforged:1441146950232571935> You don’t have permission.", ephemeral=True)
            else:
                await interaction.response.send_message("<:Emoji_Think_Goldforged:1441146950232571935> You don’t have permission.", ephemeral=True)
        else:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ An error occurred: {error}", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ An error occurred: {error}", ephemeral=True)

    @bl_edit_card.error
    async def bl_edit_card_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send("<:Emoji_Think_Goldforged:1441146950232571935> You don’t have permission.", ephemeral=True)
            else:
                await interaction.response.send_message("<:Emoji_Think_Goldforged:1441146950232571935> You don’t have permission.", ephemeral=True)
        else:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ An error occurred: {error}", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ An error occurred: {error}", ephemeral=True)
    
    @bl_show_boost.error
    async def bl_show_boost_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send("<:Emoji_Think_Goldforged:1441146950232571935> You don’t have permission.", ephemeral=True)
            else:
                await interaction.response.send_message("<:Emoji_Think_Goldforged:1441146950232571935> You don’t have permission.", ephemeral=True)
        else:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ An error occurred: {error}", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ An error occurred: {error}", ephemeral=True)
    
    @bl_show_global_boosts.error
    async def bl_show_global_boosts_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send("<:Emoji_Think_Goldforged:1441146950232571935> You don’t have permission.", ephemeral=True)
            else:
                await interaction.response.send_message("<:Emoji_Think_Goldforged:1441146950232571935> You don’t have permission.", ephemeral=True)
        else:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ An error occurred: {error}", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ An error occurred: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(XPSystem(bot))
