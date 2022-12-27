import discord, datetime, traceback, sys, io, dotenv, os
from discord.ext import commands
from data.config import BOT_EXTENSIONS, BOT_GUILDS, CONSOLE_CHANNEL, OWNER_ID


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
    print(datetime.datetime.now().strftime('%d/%m/%Y, %H:%M:%S'))
    print("Currently running with version", discord.__version__, "of py-cord")
    print('- - -')


@bot.event
async def on_error(source, *args, **kwargs):
    output = bot.get_channel(CONSOLE_CHANNEL) or bot.get_user(OWNER_ID)
    tb = traceback.TracebackException(*sys.exc_info())
    file = io.StringIO("\n".join(tb.format()))
    await output.send(file=discord.File(file, "traceback.txt"))


# Private .env file
dotenv.load_dotenv()
bot_token = os.getenv("TOKEN")

# Discord connection
bot.run(bot_token)