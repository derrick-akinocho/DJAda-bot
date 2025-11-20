import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
from pymongo import MongoClient
import io
import os
import asyncio
from datetime import datetime, timezone
        
class WelcomeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enabled = True
        self.channel_id = 1372146725455794206
        print("✅ WelcomeSystem loaded and activated automatically")

        # Bd Mongo
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["welcome"]
        self.stats_collection = self.db["members"]

    async def add_member_to_db(self, member: discord.Member):
        """Enregistre un membre dans MongoDB et renvoie True si nouveau membre"""

        # Vérifier si déjà dans la BD
        existing = self.stats_collection.find_one({
            "user_id": member.id,
            "guild_id": member.guild.id
        })

        # Si déjà dans la base → ancien membre
        if existing:
            return False

        # Nouveau membre → insérer
        member_data = {
            "user_id": member.id,
            "username": member.name,
            "discriminator": member.discriminator,
            "joined_at": datetime.now(timezone.utc),
            "guild_id": member.guild.id
        }

        self.stats_collection.insert_one(member_data)
        print(f"🟢 Nouveau membre ajouté : {member.name}")
        return True


    async def generate_welcome_image(self, user: discord.User):
        bg = Image.open("assets/img/welcome.png").convert("RGBA")
        W, H = bg.size

        # ----- Avatar -----
        avatar_bytes = await user.display_avatar.read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")

        avatar_size = 240
        avatar = avatar.resize((avatar_size, avatar_size))

        # ----- Créer un masque circulaire -----
        mask = Image.new('L', (avatar_size, avatar_size), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)

        # ----- Bordure blanche -----
        border_size = 6
        border = Image.new('RGBA', (avatar_size + border_size*2, avatar_size + border_size*2), (255, 255, 255, 255))
        border_mask = Image.new('L', (avatar_size + border_size*2, avatar_size + border_size*2), 0)
        draw_border = ImageDraw.Draw(border_mask)
        draw_border.ellipse((0, 0, avatar_size + border_size*2, avatar_size + border_size*2), fill=255)

        # Poser la bordure sur le background
        avatar_x = (W - avatar_size) // 2
        avatar_y = 40
        bg.paste(border, (avatar_x - border_size, avatar_y - border_size), border_mask)

        # Poser l’avatar avec masque circulaire
        bg.paste(avatar, (avatar_x, avatar_y), mask)

        # ----- Texte -----
        draw = ImageDraw.Draw(bg)
        font_white = ImageFont.truetype("assets/fonts/Baloo-Regular.ttf", 65)
        font_shadow = ImageFont.truetype("assets/fonts/Baloo-Regular.ttf", 66)

        text = f"WELCOME {user.mention}!"
        bbox = draw.textbbox((0, 0), text, font=font_white)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = (W - text_w) // 2
        text_y = avatar_y + avatar_size + 35

        # Shadow noir
        draw.text((text_x + 2, text_y + 2), text, font=font_shadow, fill=(0, 0, 0, 255))
        # Outline rose
        outline_color = (210, 57, 157, 255)
        for dx in (-2, 2):
            for dy in (-2, 2):
                draw.text((text_x + dx, text_y + dy), text, font=font_white, fill=outline_color)
        # Texte principal blanc
        draw.text((text_x, text_y), text, font=font_white, fill=(255, 255, 255, 255))

        # Convertir en bytes
        buffer = io.BytesIO()
        bg.save(buffer, "PNG")
        buffer.seek(0)
        return buffer

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        is_new = await self.add_member_to_db(member)

        # Si ce n’est PAS un nouveau membre
        if not is_new:
            try:
                dm = await member.create_dm()
                await dm.send(f"Hey <:Emoji_Wow_Imugi:1430608430212714618> Welcome back to the adventure !")
            except discord.Forbidden:
                print(f"DM impossible à {member}.")
            return

        if not self.enabled:
            return  # système OFF

        channel = member.guild.get_channel(self.channel_id)
        if channel is None:
            print("❌ Channel not found")
            return

        # création de l’image
        img = await self.generate_welcome_image(member)
        file = discord.File(img, filename="welcome.png")

        embed = discord.Embed(
            title=f"<:Emoji_Wow_Imugi:1430608430212714618> Welcome {member.mention}!",
            description="Glad to have you here!",
            color=0xef87ff
        )
        embed.set_image(url="attachment://welcome.png")

        # Envoi dans le salon
        await channel.send(file=file, embed=embed)
        
        try:
            # 1️⃣ Envoi de l'emoji en DM
            dm = await member.create_dm()
            #await dm.send("<:Emoji_Wow_The_Honorable:1430608433924673576>")
            await dm.send("<:Emoji_Wow_The_Honorable:1430608433924673576>")
            await asyncio.sleep(2)

            # 2️⃣ Partie principale du message
            message_part1 = (
             f"Finally, a new member! Hello {member.mention}!\n\n"
             "My name is **DJ Ada**, yes, just like the legend in Brawlhalla <:Brawlhalla_Logo_100M_Full:1441146295908696185>.\n"
             "<:Emoji_Sweat_SpongeBob:1430608405843935293> If you're lazy to pick your roles so contact <:Emoji_LookinGood_SpongeBob:1441146935950970920> Bikker Thatch."
             " He will guide you and help you choose your roles.\n"
             "I can’t help you with that <:Emoji_Shrug_High_Priestess:1430608398466027682>, but if you have any issues with the server or need information, "
             "feel free to message me...\n"
            )
            await dm.send(message_part1)
            await asyncio.sleep(2)

            # 3️⃣ Dernière partie du message : bonne arrivée
            message_part2 = "**Welcome to the Bleeding Legend adventure!** <:Emoji_Heart_Nix:1430608379457437819>"
            await dm.send(message_part2)
            await asyncio.sleep(15)  # Pause plus longue avant le bouton

            # 4️⃣ Bouton avec texte fun
            view = discord.ui.View()

            # Créer le bouton lien
            button = discord.ui.Button(
                label="Bikker Thatch, Himself!",
                style=discord.ButtonStyle.link,  # bouton lien
                url="https://discord.com/users/1430352990564389026"
            )
            view.add_item(button)

            await dm.send("Ahh, I almost forgot! Here’s Bikker Thatch’s Discord… I’ve got so much to do...", view=view)
            await asyncio.sleep(2)
            await dm.send("<:Emoji_Cry_Headmaster:1441146922948624616>")

        except discord.Forbidden:
            print(f"Impossible d'envoyer un DM à {member} (DM fermé)")

    @app_commands.command(name="adastartwelcome", description="Start the welcome system.")
    async def start_cmd(self, interaction: discord.Interaction):
        self.enabled = True
        await interaction.response.send_message("✅ Welcome system **activated**.", ephemeral=True)

    @app_commands.command(name="adastopwelcome", description="Stop the welcome system.")
    async def stop_cmd(self, interaction: discord.Interaction):
        self.enabled = False
        await interaction.response.send_message("🛑 Welcome system **deactivated**.", ephemeral=True)

    @app_commands.command(name="adastatuswelcome", description="Check the welcome system status.")
    async def status_cmd(self, interaction: discord.Interaction):

        status = "🟢 **ACTIVE**" if self.enabled else "🔴 **INACTIVE**"

        embed = discord.Embed(
            title="👁️ Welcome System Status",
            color=discord.Color.gold()
        )
        embed.add_field(name="System", value=status, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(WelcomeSystem(bot))
