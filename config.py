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
COLLECTION_PENDIND_ROLE = "pending_roles"

# ---------------------------
#       SERVER SETTINGS
# ---------------------------

WELCOME_CHANNEL_ID = 1372146725455794206
XP_CHANNEL_ID = 1432356645719248927

# ---------------------------
#       SERVER SETTINGS
# ---------------------------

AUTO_ROLE_JUNIOR_ID = 1375091476819869766
AUTO_ROLE_SENIOR_ID = 1375091620680040509