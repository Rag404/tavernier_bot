from typing import List, Union
from discord import ApplicationContext, Bot, Cog, Color, Embed, EmbedField, InputTextStyle, Interaction, Member, SlashCommandGroup, option, slash_command
from discord.ui import Modal, InputText
from datetime import datetime
from db import db
import uuid


TAVERN_ID = 731083709658169344


def new_id() -> int:
    id = uuid.uuid1().int>>64
    print(id)
    return id


class Team(Cog):
    """Groupes pour les membres"""
    
    def __init__(self, bot):
        self.bot: Bot = bot
    
    
    team_commands = SlashCommandGroup("team", "Cherchez, créez et gérez vos teams (BETA)")
    
    
    @team_commands.command(name="create")
    async def new_team(self, ctx: ApplicationContext):
        """Créer une nouvelle team (BETA)"""
        
        modal = self.NewTeamModal(self.bot, creator=ctx.author)
        await ctx.send_modal(modal)
    
    
    @team_commands.command(name="list")
    async def list_teams(self, ctx: ApplicationContext):
        """Rechercher des teams (BETA)"""
        
        embed = self.TeamListEmbed(self.bot)
        await ctx.respond(embed=embed)
    
    
    class NewTeamModal(Modal):
        def __init__(self, bot, creator: Member, *args, **kwargs):
            super().__init__(
                InputText(
                    label="Nom de votre team :",
                    placeholder="ex: Pommier",
                    min_length=3,
                    max_length=20
                ),
                InputText(
                    label="Description de votre team (facultatif) :",
                    placeholder="On est pas méchant :)",
                    required=False,
                    max_length=100
                ),
                title="Créer une nouvelle team (BETA)",
                *args,
                **kwargs
            )
            self.bot: Bot = bot
            self.creator: Member = creator
        
        async def register_team(self, id: int, name: str, creator: Member, description: str = None) -> None:
            guild = self.bot.get_guild(TAVERN_ID)
            role = await guild.create_role(name=name, color=Color.blurple(), mentionable=True)
            db.execute("INSERT INTO teams (TeamID, LeaderID, RoleID, Description) VALUES (?,?,?,?)", id, str(creator.id), str(role.id), description)
            await creator.add_roles(role)
        
        async def callback(self, interaction: Interaction):
            id = new_id()
            name = self.children[0].value
            description = self.children[1].value
            
            await self.register_team(id, name, self.creator, description)
            await interaction.response.send_message(f"Nouvelle team créée : **{name}** !")
    
    
    class TeamListEmbed(Embed):
        def __init__(self, bot):
            self.bot: Bot = bot
            super().__init__(
                title = "Liste des teams (BETA)",
                color = Color.embed_background(),
                description = None,
                fields = self.generate_fields()
            )
        
        def get_role(self, id: int) -> Member:
            return self.bot.get_guild(TAVERN_ID).get_role(id)
        
        def generate_fields(self) -> List[EmbedField]:
            teams = db.records("SELECT * FROM teams")
            page = teams[0:25]
            fields = []
            for team in page:
                fields.append(EmbedField(
                    name = self.get_role(id=int(team[2])).name,
                    value = team[3] or "*Pas de description*"
                ))
            return fields



def setup(bot):
    bot.add_cog(Team(bot))
    print(" - Team")