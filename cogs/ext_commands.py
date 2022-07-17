from discord import ApplicationContext, Bot, Cog, SlashCommandGroup
from discord.ext.commands import NotOwner, is_owner


class ExtCommands(Cog):
    def __init__(self, bot):
        self.bot: Bot = bot
    
    
    ext_commands = SlashCommandGroup("extension", "Contrôler les extensions")


    @ext_commands.command(name="load")
    @is_owner()
    async def load_ext(self, ctx: ApplicationContext, extension: str):
        try:
            self.bot.load_extension("cogs." + extension)
        except Exception as e:
            await ctx.respond(f"Error :\n```\n{e}\n```", ephemeral=True)
        else:
            await ctx.respond(f"`{extension}` is now loaded", ephemeral=True)


    @ext_commands.command(name="unload")
    @is_owner()
    async def load_ext(self, ctx: ApplicationContext, extension: str):
        try:
            self.bot.unload_extension("cogs." + extension)
        except Exception as e:
            await ctx.respond(f"Error :\n```\n{e}\n```", ephemeral=True)
        else:
            await ctx.respond(f"`{extension}` is now unloaded", ephemeral=True)
    
    
    @ext_commands.command(name="reload")
    @is_owner()
    async def load_ext(self, ctx: ApplicationContext, extension: str):
        try:
            self.bot.reload_extension("cogs." + extension)
        except Exception as e:
            await ctx.respond(f"Error :\n```\n{e}\n```", ephemeral=True)
        else:
            await ctx.respond(f"`{extension}` has been reloaded", ephemeral=True)


def setup(bot):
    bot.add_cog(ExtCommands(bot))
    print(" - ExtCommands")