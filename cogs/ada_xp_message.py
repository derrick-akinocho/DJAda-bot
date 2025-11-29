import time
import discord
import os
from discord.ext import commands
from discord import app_commands
from pymongo import MongoClient
import json
import config

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
            return

        # Multiplicator (stored key)
        multiplicator_code = str(user.get("code_multiplicateur", 0))
        multiplicator_value = self.MULTIPLICATORS.get(multiplicator_code, 1)

        # Add XP
        new_xp = user["xp"] + self.XP_PER_MESSAGE * multiplicator_value
        level = user["level"]
        life = user["life"]

        leveled_up = False
        life_up = False

        while new_xp >= self.XP_LEVELS.get(str(level), self.XP_LEVELS[str(self.MAX_LEVEL_PER_LIFE)]):
            new_xp -= self.XP_LEVELS.get(str(level), self.XP_LEVELS[str(self.MAX_LEVEL_PER_LIFE)])
            level += 1
            leveled_up = True

            # Life-up
            if level > self.MAX_LEVEL_PER_LIFE:
                level = 1
                life += 1
                life_up = True
                if life > self.NUM_LIVES:
                    life = self.NUM_LIVES
                    new_xp = self.XP_LEVELS[str(self.MAX_LEVEL_PER_LIFE)]
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

        # Send embed only for key levels or life-up
        if leveled_up and (level in self.NOTIFY_LEVELS or life_up):
            embed = discord.Embed(
                title="🎉 Congratulations!",
                color=discord.Color.green()
            )
            embed.add_field(name="Level", value=f"{display_level}/{self.MAX_LEVEL_PER_LIFE}", inline=True)
            embed.add_field(name="Life", value=f"{life}/{self.NUM_LIVES}", inline=True)
            embed.add_field(name="XP", value=f"{new_xp} / {self.XP_LEVELS.get(str(level), '???')}", inline=False)
            embed.set_footer(text=f"{message.author.display_name}")
            await message.channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(XPSystem(bot))
