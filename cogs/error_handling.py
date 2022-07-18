import io
import traceback
from discord import ApplicationContext, Bot, Cog, Color, DiscordException, Embed, EmbedField, File
from discord.ext.commands import NotOwner, MissingPermissions
from data.config import OWNER_ID, TRACEBACK_FILE_PATH
from datetime import datetime


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
        
        else:
            embed = Embed(
                title="⚡ Une erreur est survenue...",
                fields=[
                    EmbedField(
                        name="Infos",
                        value=f"Command: `{ctx.command.qualified_name}`\nAuthor: {ctx.author.mention} (`{ctx.author}`)\nGuild: `{ctx.guild.name}`\nChannel: {ctx.channel.mention} (`{ctx.channel.name}`)"
                    ),
                    EmbedField(
                        name="Error",
                        value= "```\n" + str(error) + "\n```"
                    )
                ],
                color=Color.orange(),
                timestamp=datetime.now()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            
            _traceback = io.StringIO(''.join(traceback.format_exception(type(error), error, error.__traceback__)))
            await self.bot.get_user(OWNER_ID).send(embed=embed, file=File(_traceback, filename="traceback.txt"))


def setup(bot):
    bot.add_cog(ErrorHandling(bot))
    print(" - ErrorHandling")