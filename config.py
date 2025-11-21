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
COLLECTION_STATS = "members"

# ---------------------------
#       SERVER SETTINGS
# ---------------------------

WELCOME_CHANNEL_ID = 1372146725455794206