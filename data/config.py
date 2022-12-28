import discord
import datetime as dt

# Dirty way to get the root directory (removes '\data\config.py' at the end of the str)
root_path = __file__[:-15]


# Global
TAVERN_ID = 807743905121566720
OWNER_ID  = 576435921390403623
DB_NAME   = 'tavernier_bot'

# Main
BOT_GUILDS = [807743905121566720, 731083709658169344]
BOT_EXTENSIONS = [
    "ext_commands",
    "moderation",
    "infochannels",
    "welcome",
    "status",
    "reaction_role",
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
ANIMES_PATH       = root_path + '/data/status/animes.txt'
MUSIC_GENRES_PATH = root_path + '/data/status/music_genres.txt'
VIDEO_GAMES_PATH  = root_path + '/data/status/video_games.txt'
MOVIES_PATH       = root_path + '/data/status/movies.txt'

# Voice rooms
REDIRECT_VOICE_CHANNEL = 996160558371979355
ROOMS_CATEGORY         = 996159603324768276
ROOMS_SAVE_PATH        = root_path + '/data/rooms_save.json'
ROOM_LEADER_OVERWRITES = discord.PermissionOverwrite(manage_channels=True, manage_permissions=True, move_members=True, mute_members=True, deafen_members=True, manage_events=True)

# Welcome
WELCOME_CHANNEL = 807900462794932236

# Hyperactive role
HYPERACTIVE_ROLE     = 939867561284227102
STREAK_DB_COLLECTION = 'hyperactive'
STREAK_WEEK_DAY      = 0  # 0 Monday, 1 Tuesday, etc...
STREAK_HYPERACTIVE   = 2  # Streak required to get the hyperactive role
STREAK_TIME_MIN      = dt.timedelta(hours=1)