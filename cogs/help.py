import discord
from discord.ext import commands


class HelpCommand(commands.Cog):
    """Toutes les commandes disponibles"""

    def __init__(self, bot):
        self.bot = bot


    @commands.slash_command(name='help')
    async def help(self, ctx):
        embed = discord.Embed(
            title = "Liste des commandes",
            description = ""
        )
