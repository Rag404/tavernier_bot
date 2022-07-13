import discord
from discord.ext import commands
from dotenv import load_dotenv
from os import getenv
from datetime import datetime


guilds = [807743905121566720, 731083709658169344]
intents = discord.Intents.all()
client = commands.Bot(intents=intents, debug_guilds=guilds)


extensions = [
    "moderation",
    "infochannels",
    "welcome",
    "status",
    "reaction_role",
    "utilities",
    "voice_room",
    "help"
]

print("Loading cogs...")
for extension in extensions:  # Load the extensions
    client.load_extension(f"cogs.{extension}")
print("- - -")


@client.event
async def on_ready():
    print("We have logged in as", client.user, "in", len(client.guilds), "guilds")
    print(datetime.now().strftime('%d/%m/%Y, %H:%M:%S'))  # Print the discord tag of the bot and the date when ready
    print('- - -')


load_dotenv()
token = getenv("TOKEN")
client.run(token)