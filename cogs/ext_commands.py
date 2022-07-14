from discord import ApplicationContext, Bot, Cog, SlashCommandGroup
from discord.ext.commands import NotOwner, is_owner


class ExtCommands(Cog):
    def __init__(self, bot):
        self.bot: Bot = bot
    
    
    ext_commands = SlashCommandGroup("extension")


    @ext_commands.command(name="load")
    @is_owner()
    async def load_ext(self, ctx: ApplicationContext, extension: str):
        try:
            self.bot.load_extension(extension)
        except Exception as e:
            await ctx.respond(f"```\n{e}\n```", ephemeral=True)
        else:
            await ctx.res(f"`{extension}` is now loaded", ephemeral=True)


    @ext_commands.command(name="unload")
    @is_owner()
    async def load_ext(self, ctx: ApplicationContext, extension: str):
        try:
            self.bot.unload_extension(extension)
        except Exception as e:
            await ctx.respond(f"```\n{e}\n```", ephemeral=True)
        else:
            await ctx.res(f"`{extension}` is now unloaded", ephemeral=True)
    
    
    @ext_commands.command(name="reload")
    @is_owner()
    async def load_ext(self, ctx: ApplicationContext, extension: str):
        try:
            self.bot.reload_extension(extension)
        except Exception as e:
            await ctx.respond(f"```\n{e}\n```", ephemeral=True)
        else:
            await ctx.res(f"`{extension}` has been reloaded", ephemeral=True)
    
    
    @Cog.listener()
    async def on_command_error(ctx: ApplicationContext, error):
        if isinstance(error, NotOwner):
            await ctx.respond("Vous n'êtes pas le propriétaire du bot !", ephemeral=True)
        else:
            raise error


def setup(bot):
    bot.add_cog(ExtCommands(bot))
    print(" - ExtCommands")