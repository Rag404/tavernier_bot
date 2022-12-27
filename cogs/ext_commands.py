from discord import Bot, Cog, SlashCommandGroup, ApplicationContext, AutocompleteContext, Embed, default_permissions, option
from discord.ext.commands import is_owner
from typing import Union
import os


def extensions() -> list[str]:
    """List of extensions in the 'cogs' folder"""
    return [f[:-3] for f in os.listdir("cogs/") if os.path.isfile("cogs/" + f) and f.endswith(".py")]


def loaded(ctx: Union[ApplicationContext, AutocompleteContext]) -> list[str]:
    """List of loaded extensions"""
    return [e.removeprefix("cogs.") for e in ctx.bot.extensions.keys()]


def unloaded(ctx: Union[ApplicationContext, AutocompleteContext]) -> list[str]:
    """List of unloaded extensions"""
    extensions_, loaded_ = extensions(), loaded(ctx)
    return [e for e in extensions_ if e not in loaded_]


class ExtCommands(Cog):
    def __init__(self, bot):
        self.bot: Bot = bot
    
    
    ext_commands = SlashCommandGroup("extension", "Contrôler les extensions")


    @ext_commands.command(name="load")
    @default_permissions(administrator=True)
    @is_owner()
    @option("extension", str, autocomplete=unloaded)
    async def load_ext(self, ctx: ApplicationContext, extension: str):
        try:
            self.bot.load_extension("cogs." + extension)
        except Exception as e:
            await ctx.respond(f"Error :\n```\n{e}\n```")
        else:
            await ctx.respond(f"`{extension}` is now loaded")


    @ext_commands.command(name="unload")
    @default_permissions(administrator=True)
    @is_owner()
    @option("extension", str, autocomplete=loaded)
    async def unload_ext(self, ctx: ApplicationContext, extension: str):
        try:
            self.bot.unload_extension("cogs." + extension)
        except Exception as e:
            await ctx.respond(f"Error :\n```\n{e}\n```")
        else:
            await ctx.respond(f"`{extension}` is now unloaded")
    
    
    @ext_commands.command(name="reload")
    @default_permissions(administrator=True)
    @is_owner()
    @option("extension", str, autocomplete=extensions)
    async def reload_ext(self, ctx: ApplicationContext, extension: str):
        try:
            self.bot.reload_extension("cogs." + extension)
        except Exception as e:
            await ctx.respond(f"Error :\n```\n{e}\n```")
        else:
            await ctx.respond(f"`{extension}` has been reloaded")
    
    
    @ext_commands.command(name="list")
    @default_permissions(administrator=True)
    @is_owner()
    async def list(self, ctx: ApplicationContext):
        embed = Embed(title="Liste des extensions")
        embed.add_field(
            name = ":green_circle: Chargées",
            value = ", ".join([f"`{e}`" for e in sorted(loaded(ctx))])
        )
        embed.add_field(
            name =":o: Déchargées",
            value = ", ".join([f"`{e}`" for e in sorted(unloaded(ctx))]),
            inline = False
        )
        
        await ctx.respond(embed=embed)
        


def setup(bot):
    bot.add_cog(ExtCommands(bot))
    print(" - ExtCommands")