import discord
from datetime import timedelta

# Dirty way to get the root directory (removes '\data\config.py' at the end of the str)
root_path = __file__[:-15]


# Global
TAVERN_ID = 807743905121566720
OWNER_ID  = 576435921390403623
BOT_ROLE  = 807795492468949012 # This is the role that ALL BOTS have
DB_NAME   = 'tavernier_bot'
TIMEZONE  = "CET"

# Main
BOT_GUILDS = [807743905121566720, 731083709658169344]
BOT_EXTENSIONS = [
    "ext_commands",
    "moderation",
    "infochannels",
    "welcome",
    "status",
    # "reaction_role",  Deprecated since Discord made their own role picker
    "utilities",
    "voice_room",
    "error_handling",
    "hyperactive"
]

# Error handling
CONSOLE_CHANNEL = 1046825453006106755

# Infochannels
MEMBERS_INFOCHANNEL = 1046480685059280896
ONLINES_INFOCHANNEL = 963536054621716520

# Reaction-roles
REACTION_ROLES_PATH = root_path + '/data/reaction_roles.json'

# Status
STATUS_TIMER      = timedelta(seconds=20)
ANIMES_PATH       = root_path + '/data/status/animes.txt'
MUSIC_GENRES_PATH = root_path + '/data/status/music_genres.txt'
VIDEO_GAMES_PATH  = root_path + '/data/status/video_games.txt'
MOVIES_PATH       = root_path + '/data/status/movies.txt'

# Voice rooms
REDIRECT_VOICE_CHANNEL = 996160558371979355
ROOMS_CATEGORY         = 996159603324768276
ROOMS_DB_COLLECTION    = 'rooms'
ROOM_LEADER_OVERWRITES = discord.PermissionOverwrite(manage_channels=True, manage_permissions=True, move_members=True, mute_members=True, deafen_members=True, manage_events=True)
ROOM_ALONE_TIMER       = timedelta(minutes=5)

# Welcome
WELCOME_CHANNEL = 807900462794932236

# Hyperactive role & leaderboard
HYPERACTIVE_DB_COLLECTION = 'hyperactive'
HYPERACTIVE_WEEK_DAY      = 0  # 0 Monday, 1 Tuesday ... 6 Sunday
HYPERACTIVE_LEVELS = [
    timedelta(0),        # Level 0
    timedelta(hours=1),  # Level 1
    timedelta(hours=2),  # etc...
    timedelta(hours=3),
    timedelta(hours=4),
    timedelta(hours=5)
]
HYPERACTIVE_ROLES = [
    None,                 # Level 0
    1058360019952877648,  # Level 1
    1058360464687513630,  # etc...
    1058360586947276850,
    1058360693507751966,
    1058360811946516502
]
LEADERBOARD_CHANNEL = 1088766395585675284
LEADERBOARD_LIMIT = 10