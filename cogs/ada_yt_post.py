import os
import discord
from discord.ext import commands, tasks
from pymongo import MongoClient
import aiohttp
from datetime import datetime, timezone
import config

class StreamNotifySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enabled_youtube = True
        self.enabled_twitch = True

        # MongoDB
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client[config.DATABASE_NAME_NOTIFICATION]
        self.youtube_col = self.db[config.COLLECTION_YOUTUBE_POSTS]
        self.twitch_col = self.db[config.COLLECTION_TWITCH_STATUS]

        # Start tasks
        self.check_youtube.start()
        self.check_twitch.start()
        print("🔁 StreamNotifySystem loaded")

    # -------------------- YOUTUBE --------------------
    @tasks.loop(minutes=10)
    async def check_youtube(self):
        if not self.enabled_youtube:
            return

        channel_id = os.environ.get("YOUTUBE_CHANNEL_ID")
        api_key = os.environ.get("YOUTUBE_API_KEY")
        announce_channel_id = config.YT_ANNOUNCE_CHANNEL_ID
        announce_channel = self.bot.get_channel(announce_channel_id)
        if not announce_channel:
            return

        url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&order=date&part=snippet&type=video&maxResults=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

        try:
            video_id = data["items"][0]["id"]["videoId"]
            title = data["items"][0]["snippet"]["title"]
        except:
            return

        last_doc = self.youtube_col.find_one({"channel_id": channel_id})
        if last_doc and last_doc.get("last_video") == video_id:
            return

        embed = discord.Embed(
            title="👀 Come to See Thе Good in Me!",
            description=f"**{title}**\nhttps://youtu.be/{video_id}",
            color=0xff5353
        )
        await announce_channel.send("<@&1388172157846028539>", embed=embed)

        self.youtube_col.update_one(
            {"channel_id": channel_id},
            {"$set": {"last_video": video_id}},
            upsert=True
        )

    @commands.command()
    async def yttoggle(self, ctx):
        self.enabled_youtube = not self.enabled_youtube
        await ctx.send(f"YouTube Auto-Post {'🟢 Enabled' if self.enabled_youtube else '🔴 Disabled'}")

    # -------------------- TWITCH --------------------
    @tasks.loop(minutes=5)
    async def check_twitch(self):
        if not self.enabled_twitch:
            return

        client_id = os.environ.get("TWITCH_CLIENT_ID")
        client_secret = os.environ.get("TWITCH_CLIENT_SECRET")
        streamer = os.environ.get("TWITCH_USERNAME")
        announce_channel_id = config.TWITCH_ANNOUNCE_CHANNEL_ID
        announce_channel = self.bot.get_channel(announce_channel_id)
        if not announce_channel:
            return

        # Get token
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"
            ) as resp:
                token_data = await resp.json()
                access_token = token_data.get("access_token")

        if not access_token:
            return

        # Check if live
        headers = {"Client-ID": client_id, "Authorization": f"Bearer {access_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.twitch.tv/helix/streams?user_login={streamer}", headers=headers) as resp:
                data = await resp.json()

        is_live = len(data.get("data", [])) > 0
        status_doc = self.twitch_col.find_one({"streamer": streamer})

        # Nouveau live
        if is_live and (not status_doc or not status_doc.get("live", False)):
            title = data["data"][0]["title"]
            url_stream = f"https://twitch.tv/{streamer}"
            embed = discord.Embed(
                title=" Come to play and bleed🩸",
                description=f"**{streamer}** on Twitch : {title} \n{url_stream}",
                color=0xff5353
            )
            await announce_channel.send("<@&1388172157846028539>", embed=embed)
            self.twitch_col.update_one(
                {"streamer": streamer},
                {"$set": {"live": True, "last_checked": datetime.now(timezone.utc)}},
                upsert=True
            )

        # Fin de stream
        elif not is_live and status_doc and status_doc.get("live", False):
            self.twitch_col.update_one(
                {"streamer": streamer},
                {"$set": {"live": False, "last_checked": datetime.now(timezone.utc)}}
            )

    @commands.command()
    async def twitchtoggle(self, ctx):
        self.enabled_twitch = not self.enabled_twitch
        await ctx.send(f"Twitch Auto-Post {'🟢 Enabled' if self.enabled_twitch else '🔴 Disabled'}")

    @commands.command()
    async def twitchstatus(self, ctx):
        embed = discord.Embed(title="🔁 Twitch Status", color=discord.Color.purple())
        embed.add_field(name="System", value="🟢 ENABLED" if self.enabled_twitch else "🔴 DISABLED")
        embed.add_field(name="Streamer", value=os.environ.get("TWITCH_USERNAME"))
        embed.add_field(name="Interval", value="5 minutes")
        await ctx.send(embed=embed)

    @check_youtube.before_loop
    @check_twitch.before_loop
    async def before_tasks(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(StreamNotifySystem(bot))
