import os

# ---------------------------
#       BOT SETTINGS
# ---------------------------

TOKEN = os.getenv("TOKEN")

# ---------------------------
#       MONGO SETTINGS
# ---------------------------

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "welcome"
DATABASE_NAME_NOTIFICATION = "notifications"
COLLECTION_STATS = "members"
COLLECTION_PENDIND_ROLE = "pending_roles"
COLLECTION_YOUTUBE_POSTS = "youtube_posts"
COLLECTION_TWITCH_STATUS = "twitch_status"
COLLECTION_XP_MESSAGES_STATUS = "xp_messages"

# ---------------------------
#       SERVER SETTINGS
# ---------------------------

WELCOME_CHANNEL_ID = 1372146725455794206
XP_CHANNEL_ID = 1432356645719248927
YT_ANNOUNCE_CHANNEL_ID = 1426393507722952715
TWITCH_ANNOUNCE_CHANNEL_ID = 1426393507722952715

# ---------------------------
#       SERVER SETTINGS
# ---------------------------

AUTO_ROLE_JUNIOR_ID = 1375091476819869766
AUTO_ROLE_SENIOR_ID = 1375091620680040509

# ---------------------------
#       XP LVL SETTINGS
# ---------------------------

MAX_LEVEL_PER_LIFE = 99
NUM_LIVES = 7
XP_PER_MESSAGE = 100
XP_COOLDOWN = 2