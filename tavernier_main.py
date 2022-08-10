import discord
from discord.ext import commands
from dotenv import load_dotenv
from os import getenv
from datetime import datetime
from data.config import BOT_EXTENSIONS, BOT_GUILDS


intents = discord.Intents.all()
client = commands.Bot(intents=intents, debug_guilds=BOT_GUILDS)


print("Loading cogs...")
for extension in BOT_EXTENSIONS:  # Load the extensions
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