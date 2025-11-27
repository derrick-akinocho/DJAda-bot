import discord
from discord.ext import commands, tasks
from discord import app_commands
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import config

class AutoRoleSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enabled = True
        print("🔁 AutoRoleSystem loaded and automatically activated")

        # MongoDB
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client[config.DATABASE_NAME]
        self.collection = self.db[config.COLLECTION_PENDIND_ROLE]

        # Role IDs
        self.role_7d_id = config.AUTO_ROLE_JUNIOR_ID
        self.role_1y_id = config.AUTO_ROLE_SENIOR_ID

        # Start task
        self.check_pending_roles.start()

    async def add_pending_user(self, member: discord.Member):
        """Store join date for future role checks."""
        if member.bot:
            return False

        existing = self.collection.find_one({
            "user_id": member.id,
            "guild_id": member.guild.id
        })

        if existing:
            self.collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "join_date": datetime.now(timezone.utc),
                    "seven_days_done": False,
                    "one_year_done": False
                }}
            )
            print(f"🔄 Member rejoined, join date reset: {member.name}")
            return True

        self.collection.insert_one({
            "user_id": member.id,
            "guild_id": member.guild.id,
            "join_date": datetime.now(timezone.utc),
            "seven_days_done": False,
            "one_year_done": False
        })

        print(f"🟢 Added member to pending list: {member.name}")
        return True

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return
        if self.enabled:
            await self.add_pending_user(member)

    @commands.Cog.listener()
    async def on_ready(self):
        """Backfill existing members on bot startup."""
        print("🔄 Running backfill for existing members...")
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.bot:
                    continue
                existing = self.collection.find_one({
                    "user_id": member.id,
                    "guild_id": guild.id
                })
                if not existing:
                    await self.add_pending_user(member)
        print("✅ Backfill done: all existing members added to pending roles")

    @tasks.loop(minutes=2)
    async def check_pending_roles(self):
        """Check if a user reached 7 days or 1 year."""
        if not self.enabled:
            return

        now = datetime.now(timezone.utc)
        seven_days = timedelta(minutes=1)
        one_year = timedelta(minutes=2)

        docs = list(self.collection.find({}))
        if not docs:
            return

        for doc in docs:

            join_date = doc["join_date"]
            if join_date.tzinfo is None:
                join_date = join_date.replace(tzinfo=timezone.utc)
            
            guild = self.bot.get_guild(doc["guild_id"])
            if not guild:
                continue

            member = guild.get_member(doc["user_id"])
            if not member or member.bot:
                continue

            # ---------- 7 DAYS ROLE ----------
            if not doc.get("seven_days_done", False):
                if now - join_date >= seven_days:
                    role = guild.get_role(self.role_7d_id)
                    if role:
                        try:
                            await member.add_roles(role)
                            print(f"🎉 7-day role assigned to {member.name}")
                        except Exception as e:
                            print(f"⚠️ Failed to assign 7-day role: {e}")

                    self.collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {"seven_days_done": True}}
                    )

            # ---------- 1 YEAR ROLE ----------
            if not doc.get("one_year_done", False):
                if now - join_date >= one_year:
                    role = guild.get_role(self.role_1y_id)
                    if role:
                        try:
                            await member.add_roles(role)
                            print(f"🏆 1-year role assigned to {member.name}")
                        except Exception as e:
                            print(f"⚠️ Failed to assign 1-year role: {e}")

                    self.collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {"one_year_done": True}}
                    )

    @check_pending_roles.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    # ----- ADMIN COMMANDS -----
    @app_commands.command(name="autoroletoggle", description="Enable or disable the auto role system.")
    async def toggle_cmd(self, interaction):
        self.enabled = not self.enabled
        await interaction.response.send_message( f"Status: {'🟢 Enabled' if self.enabled else '🔴 Disabled'}",ephemeral=True)

    @app_commands.command(name="autorolestatus", description="Show the auto role system status.")
    async def status_cmd(self, interaction):
        embed = discord.Embed(
            title="🔁 Auto Role — Status",
            color=discord.Color.blue()
        )
        embed.add_field(name="System", value=("🟢 ENABLED" if self.enabled else "🔴 DISABLED"), inline=False)
        embed.add_field(name="7-day Role", value=self.role_7d_id, inline=False)
        embed.add_field(name="1-year Role", value=self.role_1y_id, inline=False)
        embed.add_field(name="Interval", value="20 minutes", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AutoRoleSystem(bot))
