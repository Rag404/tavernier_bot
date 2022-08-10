import discord

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
TRACEBACK_FILE_PATH = './data/last_traceback.txt'

# Infochannels
MEMBERS_INFOCHANNEL = 925362480430059541
ONLINES_INFOCHANNEL = 963536054621716520

# Reaction-roles
REACTION_ROLES_PATH = './data/reaction_roles_test.json'

# Voice rooms
REDIRECT_VOICE_CHANNEL = 996160558371979355
ROOMS_CATEGORY = 996159603324768276
ROOMS_SAVE_PATH = './data/rooms_save.json'
ROOM_LEADER_OVERWRITES = discord.PermissionOverwrite(manage_channels=True, manage_permissions=True, move_members=True, mute_members=True, deafen_members=True, manage_events=True)

# Welcome
WELCOME_CHANNEL = 807900462794932236