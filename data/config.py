import discord

# Dirty way to get the root directory (removes '\data\config.py' at the end of the str)
root_path = __file__[:-15]


# Global
TAVERN_ID = 807743905121566720
OWNER_ID = 576435921390403623

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
    "error_handling"
]

# Error handling
TRACEBACK_FILE_PATH = root_path + '/data/last_traceback.txt'

# Infochannels
MEMBERS_INFOCHANNEL = 1046480685059280896
ONLINES_INFOCHANNEL = 963536054621716520

# Reaction-roles
REACTION_ROLES_PATH = root_path + '/data/reaction_roles.json'

# Status
ANIMES_PATH = root_path + '/data/status/animes.txt'
MUSIC_GENRES_PATH = root_path + '/data/status/music_genres.txt'
VIDEO_GAMES_PATH = root_path + '/data/status/video_games.txt'
MOVIES_PATH = root_path + '/data/status/movies.txt'

# Voice rooms
REDIRECT_VOICE_CHANNEL = 996160558371979355
ROOMS_CATEGORY = 996159603324768276
ROOMS_SAVE_PATH = root_path + '/data/rooms_save.json'
ROOM_LEADER_OVERWRITES = discord.PermissionOverwrite(manage_channels=True, manage_permissions=True, move_members=True, mute_members=True, deafen_members=True, manage_events=True)

# Welcome
WELCOME_CHANNEL = 807900462794932236