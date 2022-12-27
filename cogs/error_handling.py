from discord import ApplicationContext, Bot, Cog, Color, DiscordException
from discord.ext.commands import NotOwner, MissingPermissions


class ErrorHandling(Cog):
    """Gère les erreurs"""
    
    def __init__(self, bot):
        self.bot: Bot = bot
    
    
    @Cog.listener()
    async def on_application_command_error(self, ctx: ApplicationContext, error: DiscordException):
        if isinstance(error, NotOwner):
            await ctx.respond("Vous n'êtes pas le propriétaire du bot !", ephemeral=True)
        
        elif isinstance(error, MissingPermissions):
            await ctx.respond("Vous n'avez pas les permissions nécéssaires !", ephemeral=True)


def setup(bot):
    bot.add_cog(ErrorHandling(bot))
    print(" - ErrorHandling")