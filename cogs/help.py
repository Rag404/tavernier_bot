from typing import Dict
from discord import ApplicationCommand, ApplicationContext, Bot, Cog, Embed, Permissions, SlashCommand, SlashCommandGroup, slash_command


class HelpCommand(Cog):
    """Toutes les commandes disponibles"""

    def __init__(self, bot):
        self.bot: Bot = bot
    

    @slash_command(name='help')
    async def help(self, ctx: ApplicationContext):
        """Affiche la list des commandes"""
        
        commands: Dict[str, ApplicationCommand] = self.bot.all_commands
        embed = Embed(title="List des commandes disponibles pour vous", description="")
        
        def check_default_permissions(command: SlashCommand) -> bool:
            if command.default_member_permissions is not None:
                if not ctx.author.guild_permissions.is_superset(command.default_member_permissions):
                    return False
            return True
        
        for command in commands.values():
            if isinstance(command, SlashCommand):
                if check_default_permissions(command):
                    embed.description += f"`/{command.name}` {command.description}\n"
            
            elif isinstance(command, SlashCommandGroup):
                name = f"{command.description} - `/{command.name}` "
                value = ""
                for subcommand in command.walk_commands():
                    if check_default_permissions(subcommand):
                        value += f"`{subcommand.name}` {subcommand.description}\n"
                if value != "":
                    embed.add_field(name=name, value=value)
        
        await ctx.respond(embed=embed)
            



def setup(bot):
    bot.add_cog(HelpCommand(bot))
    print(" - HelpCommand")