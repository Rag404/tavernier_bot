import discord
from discord.ext import commands
from dotenv import load_dotenv
from os import getenv
from datetime import datetime
from data.config import BOT_EXTENSIONS, BOT_GUILDS


intents = discord.Intents.all()
bot = commands.Bot(intents=intents, debug_guilds=BOT_GUILDS)


print("Loading cogs...")
for extension in BOT_EXTENSIONS:
    # Load the extensions
    bot.load_extension(f"cogs.{extension}")
print("- - -")


@bot.event
async def on_ready():
    # Print the discord tag of the bot, the date and the current py-cord version when ready
    print("We have logged in as", bot.user, "in", len(bot.guilds), "guilds")
    print(datetime.now().strftime('%d/%m/%Y, %H:%M:%S'))
    print("Currently running with version", discord.__version__, "of py-cord")
    print('- - -')


# Private .env file
load_dotenv()
bot_token = getenv("TOKEN")

# Discord connection
bot.run(bot_token)