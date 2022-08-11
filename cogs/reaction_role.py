from discord import ApplicationContext, AutocompleteContext, Bot, Cog, Emoji, Guild, Embed, Message, Permissions, RawReactionActionEvent, Role, SlashCommandGroup, TextChannel, option, slash_command
from discord.ext.commands import is_owner
from data.config import REACTION_ROLES_PATH
from typing import Union
from my_utils import log
import json


global reaction_roles
with open(REACTION_ROLES_PATH, encoding="utf-8") as file:
    reaction_roles: dict = json.load(file)


class ReactionRole(Cog):
    """Recevoir un role avec une réaction"""

    def __init__(self, bot):
        self.bot: Bot = bot
    
    
    def embed_from_rr(self, rr: dict, guild: Guild) -> Embed:
        embed = Embed()
        embed.title = rr["embed"]["title"]
        embed.description = ""
        embed.color = rr["embed"]["color"]

        for reaction in rr["reactions"].values():
            role = guild.get_role(reaction["role"])
            emoji = self.emoji_from_rr(reaction)
            embed.description += f"\n{emoji} - {role.mention} "

            if description := reaction.get("description"):
                embed.description += description

        return embed


    def emoji_from_rr(self, reaction: dict) -> Union[int, str]:
        id = reaction["emoji"]
        if type(id) == int:
            emoji = self.bot.get_emoji(id)
            return emoji
        else:
            return id


    async def add_reactions(self, rr: dict, msg: Message) -> None:
        for reaction in rr["reactions"].values():
            emoji = self.emoji_from_rr(reaction)
            await msg.add_reaction(emoji)



    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        # Check if the member is not the bot
        if payload.user_id == self.bot.user.id:
            return

        for rr_name in reaction_roles:
            reaction_role = reaction_roles[rr_name]
            
            # Check if the message id matches with the one in the json data
            if payload.message_id != reaction_role["msg_id"]:
                continue

            # Loop in the emojis of the rr in the json data
            for reaction in reaction_role["reactions"].values():
                # Give the role associated to the emoji
                if reaction["emoji"] == (payload.emoji.id or payload.emoji.name):
                    role = payload.member.guild.get_role(reaction["role"])
                    await payload.member.add_roles(role)
                    log(f'"{role.name}" given to', payload.member, f'by the reaction-role "{rr_name}"')


    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        # Check if the member is not the bot
        if payload.user_id == self.bot.user.id:
            return

        for rr_name in reaction_roles:
            reaction_role = reaction_roles[rr_name]
            
            # Check if the message id matches with the one in the json data
            if payload.message_id != reaction_role["msg_id"]:
                continue

            # Loop in the emojis of the rr in the json data
            for reaction in reaction_role["reactions"].values():
                # Give the role associated to the emoji (longer code because on_raw_reaction_remove() only provides the member id in the payload)
                if reaction["emoji"] == (payload.emoji.id or payload.emoji.name):
                    guild: Guild = self.bot.get_guild(payload.guild_id)
                    member = guild.get_member(payload.user_id)
                    role = guild.get_role(reaction["role"])
                    await member.remove_roles(role)
                    log(f'"{role.name}" removed from', payload.member, f'by the reaction-role "{rr_name}"')

    
    async def rr_autocomplete(ctx: AutocompleteContext):
        return list(reaction_roles.keys())
    
    async def existing_reactions(ctx: AutocompleteContext):
        picked_rr = ctx.options["rr"]
        return list(reaction_roles[picked_rr]["reactions"].keys())
    

    rr_commands = SlashCommandGroup(
        "reaction-role",
        "Commandes pour les réaction-rôles",
        default_member_permissions = Permissions(administrator=True)
    )


    @rr_commands.command(name='refresh')
    @option("rr", description="Le réaction-rôle à rafraîchir", autocomplete=rr_autocomplete)
    @option("from_file", description="Si le fichier doit être ré-ouvert avant de rafraîchir", choices=["yes", "no"], default="yes")
    async def refresh_rr(self, ctx: ApplicationContext, rr: str, from_file: str):
        """Actualise les reaction-roles."""

        # Defer as process might take a while to complete
        await ctx.defer(ephemeral=True)

        if from_file == "yes":
            # Open the file to refresh the values in the variable reaction_roles
            with open(REACTION_ROLES_PATH, encoding="utf-8") as file:
                global reaction_roles
                reaction_roles = json.load(file)

        # Get the message with the id in the rr data (and handle errors)
        msg: Message = None
        try:
            msg = await ctx.fetch_message(reaction_roles[rr]["msg_id"])
        except:
            return await ctx.respond("Une erreur est survenue... Avez-vous utilisé la commande dans le même salon que le réaction-rôle ?", ephemeral=True)

        rr_data = reaction_roles[rr]
        
        # Edit the message to refresh the embed
        embed = self.embed_from_rr(rr_data, msg.guild)
        await msg.edit(embed=embed)

        # Add all the reactions to the rr message
        await self.add_reactions(rr_data, msg)

        # Log and respond to the command
        log("Reaction-roles have been updated by", ctx.author)
        await ctx.respond("Le réaction-rôles a bien été actualisé.", ephemeral=True)


    @rr_commands.command(name='resend')
    @is_owner()
    @option("rr", description="Le réaction-rôle à envoyer", autocomplete=rr_autocomplete)
    async def resend_rr(self, ctx: ApplicationContext, rr: str, channel: TextChannel):
        """Owner seulement. Ré-envoie un reaction-role."""

        # Defer as process might take a while to complete
        await ctx.defer(ephemeral=True)

        # Open the file to refresh the values in the variable reaction_roles
        with open(REACTION_ROLES_PATH, encoding="utf-8") as file:
            global reaction_roles
            reaction_roles = json.load(file)

        try:
            rr_data = reaction_roles[rr]

            # Get the embed of the rr and send it
            embed = self.embed_from_rr(rr_data, channel.guild)
            msg = await channel.send(embed=embed)

            # Change the message id associated to the rr in the json data
            with open(REACTION_ROLES_PATH, 'w') as file:
                rr_data["msg_id"] = msg.id
                json.dump(reaction_roles, file, indent=4)

            # Add all the reactions to the rr message
            await self.add_reactions(rr_data, msg)
            
            # Log and respond to the command
            log(f'The reaction-role "{rr}" has been sent in #{channel.name} by', ctx.author)
            await ctx.respond("Le reaction-role a bien été envoyé.", ephemeral=True)

        # If KeyError is raised then the name provided isn't valid
        except KeyError:
            await ctx.respond("Nom du reaction-role invalide...", ephemeral=True)
    
    
    @rr_commands.command(name='new-role')
    @option("rr", description="Le réaction-rôle à éditer", autocomplete=rr_autocomplete)
    @option("role", description="Le rôle à ajouter au réaction-rôle")
    @option("emoji", description="L'emoji qui sera associé au rôle")
    @option("description", description="Le texte qui sera affiché dans le réaction-rôle", required=False)
    async def new_role_in_rr(self, ctx: ApplicationContext, rr: str, role: Role, emoji: Emoji, description: str):
        """Ajoute un rôle à un réaction-rôle"""
        
        new_reaction = {
            "role": role.id,
            "emoji": emoji.id
        }
        
        if description is not None:
            new_reaction["description"] = description
        
        reaction_roles[rr]["reactions"][role.name] = new_reaction
        
        # Change the message id associated to the rr in the json data
        with open(REACTION_ROLES_PATH, 'w') as file:
            json.dump(reaction_roles, file, indent=4)
        
        await self.refresh_rr(ctx, rr, "no")
        


def setup(bot):
    bot.add_cog(ReactionRole(bot))
    print(" - ReactionRole")
