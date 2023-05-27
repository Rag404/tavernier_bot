from discord import ApplicationContext, AutocompleteContext, Bot, Cog, Emoji, Guild, Embed, Message, Permissions, RawReactionActionEvent, Role, SlashCommandGroup, TextChannel, option
from discord.ext.commands import is_owner
from data.config import REACTION_ROLES_PATH
from typing import Union, Optional
from resources.utils import log
import json



# - - - - This cog is deprecated since Discord made their own role picker - - - - #



class ReactionChoice:
    def __init__(self, name: str, role: Role, emoji: Union[Emoji, str], label: Optional[str] = None) -> None:
        self.name = name
        self.role = role
        self.emoji = emoji
        self.label = label
    
    
    def dict(self) -> dict:
        final = {
            "role": self.role.id,
            "emoji": (self.emoji if isinstance(self.emoji, str) else self.emoji.id),
        }
        
        if self.label:
            final["label"] = self.label
        
        return final


class ReactionRole:
    def __init__(self, name: str, guild: Guild, channel: TextChannel, message: Message, title: str, color: int, choices: list[ReactionChoice]) -> None:
        self.name = name
        self.guild = guild
        self.channel = channel
        self.message = message
        self.title = title
        self.color = color
        self.choices = choices
    
    
    def __repr__(self) -> str:
        return self.name
    
    
    def dict(self) -> dict:
        return {
            "guild": self.guild.id,
            "channel": self.channel.id,
            "message": self.message.id,
            "title": self.title,
            "color": self.color,
            "choices": {choice.name: choice.dict() for choice in self.choices}
        }
    
    
    def embed(self) -> Embed:
        """Get the reaction-role formatted as a discord embed"""
        
        embed = Embed(
            title = self.title,
            description = "",
            color = self.color
        )
        
        for choice in self.choices:
            embed.description += f"{choice.emoji} - {choice.role.mention} {choice.label or ''}\n"
        
        return embed
    
    
    async def send(self, channel: Optional[TextChannel]):
        """Send as a discord message. Specifying a channel will update the attributes accordingly."""
        
        if channel:
            self.message = await channel.send(embed=self.embed())
            self.guild = channel.guild
        else:
            self.message = await self.channel.send(embed=self.embed())
        
        await self.update_reactions()
    
    
    async def update_message(self):
        """Update the associated discord message"""
        
        await self.message.edit(embed=self.embed())
        await self.update_reactions()
    
    
    async def update_reactions(self):
        """Update the reactions on the associated discord message"""
        
        emojis = [choice.emoji for choice in self.choices]
        
        for emoji in emojis:
            await self.message.add_reaction(emoji)
        
        for reac in self.message.reactions:
            if reac.emoji not in emojis:
                await self.message.clear_reaction(reac.emoji)
    
    
    def add_choice(self, role: Role, emoji: Union[Emoji, str], label: Optional[str]):
        """Add a choice with an associated role, emoji and label"""
        
        self.choices.append(ReactionChoice(role.name, role, emoji, label))
    
    
    def remove_choice(self, name: str):
        """Remove a specified choice"""
        
        for i, choice in enumerate(self.choices):
            if choice.name == name:
                del self.choices[i]
                return


reaction_roles: list[ReactionRole] = []


def save_data(rr_list: list[ReactionRole]):
    with open(REACTION_ROLES_PATH, 'w') as file:
        json.dump(
            {rr.name: rr.dict() for rr in rr_list},
            file,
            indent=4
        )


def get_by_name(rr_list: list[ReactionRole], name: str) -> ReactionRole:
    """Retrieve a ReactionRole from a list using its name"""
    
    for reac_role in rr_list:
        if reac_role.name == name:
            return reac_role


def emoji_id(emoji: Union[Emoji, str]) -> Union[int, str, None]:
    """Return the emoji's ID if it is an :class:`Emoji` object, or the emoji itself if it is an :class:`str` object"""
    
    if isinstance(emoji, Emoji):
        return emoji.id
    
    elif isinstance(emoji, str):
        return emoji
    
    return None



class ReactionRoleCog(Cog):
    """Recevoir un role avec une réaction"""

    def __init__(self, bot):
        self.bot: Bot = bot
        self.bot.loop.create_task(self.load_reaction_roles())
    
    
    async def load_reaction_roles(self):
        """Read the data file and initialize the main ReactionRole list"""
        
        await self.bot.wait_until_ready()
        global reaction_roles
        reaction_roles = []
        
        with open(REACTION_ROLES_PATH, encoding="utf-8") as file:
            data: dict = json.load(file)
            
        for rr_name, rr_data in data.items():
            guild = self.bot.get_guild(rr_data["guild"])
            channel = guild.get_channel(rr_data["channel"])
            message = await channel.fetch_message(rr_data["message"])
            
            title = rr_data["title"]
            color = rr_data["color"]
            
            choices = []
            
            for choice_name, choice_data in rr_data["choices"].items():
                choices.append(ReactionChoice(
                    choice_name,
                    guild.get_role(choice_data["role"]),
                    self.get_emoji(choice_data["emoji"]),
                    choice_data.get("label")
                ))
            
            reaction_roles.append(ReactionRole(rr_name, guild, channel, message, title, color, choices))


    def get_emoji(self, id: Union[int, str]) -> Union[int, str]:
        """Return either a discord or a standart Emoji depending on the type of the given id"""
        
        if isinstance(id, int):
            return self.bot.get_emoji(id)
        else:
            return id


    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        # Check if the member is the bot
        if payload.user_id == self.bot.user.id:
            return
        
        global reaction_roles

        for reac_role in reaction_roles:
            # Check if the message id matches with the one in the json data
            if payload.message_id != reac_role.message.id:
                continue

            # Loop in the emojis of the rr in the json data
            for choice in reac_role.choices:
                # Give the role associated to the emoji
                if emoji_id(choice.emoji) in (payload.emoji.id, payload.emoji.name):
                    await payload.member.add_roles(choice.role)
                    log(f'"{choice.role.name}" given to {payload.member} by the reaction-role "{reac_role.name}"')
                    break


    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        # Check if the member is the bot
        if payload.user_id == self.bot.user.id:
            return
        
        global reaction_roles

        for reac_role in reaction_roles:
            # Check if the message id matches with the one in the json data
            if payload.message_id != reac_role.message.id:
                continue

            for choice in reac_role.choices:
                # Remove the role associated to the emoji (longer code because on_raw_reaction_remove() only provides the member id in the payload)
                if emoji_id(choice.emoji) in (payload.emoji.id, payload.emoji.name):
                    guild = self.bot.get_guild(payload.guild_id)
                    member = guild.get_member(payload.user_id)
                    await member.remove_roles(choice.role)
                    log(f'"{choice.role.name}" removed from {member} by the reaction-role "{reac_role.name}"')
                    break

    
    async def name_autocomplete(ctx: AutocompleteContext) -> list[str]:
        return [rr.name for rr in reaction_roles]
    
    async def choices_autocomplete(ctx: AutocompleteContext) -> list[str]:
        picked_rr = get_by_name(reaction_roles, ctx.options["name"])
        return [choice.role.name for choice in picked_rr.choices]
    

    rr_commands = SlashCommandGroup(
        "reaction-role",
        "Commandes pour les réaction-rôles",
        default_member_permissions = Permissions(administrator=True)
    )


    @rr_commands.command(name='refresh')
    @option("name", description="Le réaction-rôle à rafraîchir", autocomplete=name_autocomplete)
    @option("from_file", description="Si le fichier doit être ré-ouvert avant de rafraîchir", choices=["yes", "no"], default="yes")
    async def refresh_rr(self, ctx: ApplicationContext, name: str, from_file: str):
        """Actualise les reaction-roles."""

        await ctx.defer()
        global reaction_roles
        
        if from_file == "yes":
            await self.load_reaction_roles()
        
        reac_role = get_by_name(reaction_roles, name)
        
        if not reac_role:
            return await ctx.respond("Nom du réaction-rôle invalide...")
        
        await reac_role.update_message()
        log(f'The reaction-role "{reac_role}" have been refreshed by', ctx.author)
        await ctx.respond(f"Le réaction-rôle **{reac_role}** a bien été actualisé.")


    @rr_commands.command(name='send')
    @is_owner()
    @option("name", description="Le réaction-rôle à envoyer", autocomplete=name_autocomplete)
    @option("channel", description="Le salon où le réaction-rôle doit être envoyé")
    @option("from_file", description="Si le fichier doit être ré-ouvert avant d'envoyer", choices=["yes", "no"], default="yes")
    async def resend_rr(self, ctx: ApplicationContext, name: str, channel: TextChannel, from_file: str):
        """Owner seulement. Ré-envoie un reaction-role."""

        await ctx.defer()
        global reaction_roles
        
        if from_file == "yes":
            await self.load_reaction_roles()
        
        reac_role = get_by_name(reaction_roles, name)
        
        if not reac_role:
            return await ctx.respond("Nom du réaction-rôle invalide...")
        
        await reac_role.send(channel)
        save_data(reaction_roles)
        log(f'The reaction-role "{reac_role}" has been sent in #{channel.name} by', ctx.author)
        await ctx.respond(f"Le reaction-role **{reac_role}** a bien été envoyé.")
    
    
    @rr_commands.command(name='new-role')
    @option("name", description="Le réaction-rôle à éditer", autocomplete=name_autocomplete)
    @option("role", description="Le rôle à ajouter au réaction-rôle")
    @option("emoji", description="L'emoji qui sera associé au rôle. DOIT ÊTRE UN EMOJI CUSTOM !")
    @option("description", description="Le texte qui sera affiché dans le réaction-rôle", required=False)
    async def new_role_in_rr(self, ctx: ApplicationContext, name: str, role: Role, emoji: Emoji, description: str):
        """Ajoute un rôle à un réaction-rôle"""
        
        # For the Emoji type to work as an option type, a little change has been made to the library
        # Line 851 in ./bot-env/Lib/site-packages/discord/commands/core.py
        # arg = await converter().convert(ctx, arg)
        # Instead of
        # arg = await converter.convert(ctx, arg)
        
        await ctx.defer()
        global reaction_roles
        reac_role = get_by_name(reaction_roles, name)
        
        if not reac_role:
            return await ctx.respond("Nom du réaction-rôle invalide...")
        
        reac_role.add_choice(role, emoji, description)
        await reac_role.update_message()
        save_data(reaction_roles)
        log(f'The role "{role.name}" has been added to the reaction-role "{reac_role}" by', ctx.author)
        await ctx.respond(f"Le choix {role.mention} a bien été ajouté au réaction-rôle **{reac_role}**")
    
    
    @rr_commands.command(name='remove-role')
    @option("name", description="Le réaction-rôle à éditer", autocomplete=name_autocomplete)
    @option("choice", description="Le choix à retirer au réaction-rôle", autocomplete=choices_autocomplete)
    async def remove_role_in_rr(self, ctx: ApplicationContext, name: str, choice: str):
        """Retire un rôle à un réaction-rôle"""
        
        await ctx.defer()
        global reaction_roles
        reac_role = get_by_name(reaction_roles, name)
        
        if not reac_role:
            return await ctx.respond("Nom du réaction-rôle invalide...")
        
        reac_role.remove_choice(choice)
        await reac_role.update_message()
        save_data(reaction_roles)
        log(f'The role "{name}" has been removed from the reaction-role "{reac_role}" by', ctx.author)
        await ctx.respond(f"Le choix **{choice}** a bien été supprimé du réaction-rôle **{reac_role}**")
        


def setup(bot):
    bot.add_cog(ReactionRoleCog(bot))
    print(" - ReactionRole")
