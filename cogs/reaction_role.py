from discord import ApplicationContext, Bot, Cog, Guild, Embed, Message, RawReactionActionEvent, TextChannel, slash_command 
from data.config import REACTION_ROLES_PATH
from typing import Union
from my_utils import log
import json


global reaction_roles
with open(REACTION_ROLES_PATH, encoding="utf-8") as file:
    reaction_roles = json.load(file)


class ReactionRole(Cog):
    """Recevoir un role avec une réaction"""

    def __init__(self, bot):
        self.bot: Bot = bot


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


    @slash_command(name='refresh-rr')
    async def refresh_rr(self, ctx: ApplicationContext, rr: str):
        """Owner seulement. Actualise les reaction-roles."""

        # Check if author is owner
        if ctx.author != ctx.guild.owner:
            ctx.respond("Vous n'avez pas les permissions requises pour effectuer cette commande...", ephemeral=True)
            return

        # Defer because process might take a while
        await ctx.defer(ephemeral=True)

        # Open the file to refresh the values in the variable reaction_roles
        with open('reaction_roles.json', encoding="utf-8") as file:
            global reaction_roles
            reaction_roles = json.load(file)

        # Get the message with the id in the rr data (and handle errors)
        msg: Message = None
        try:
            msg = await ctx.fetch_message(reaction_roles[rr]["msg_id"])
        except:
            await ctx.respond("Une erreur est survenue... Avez-vous utilisé la commande dans le même salon que le réaction-rôle ?", ephemeral=True)
            return

        # Edit the message to refresh the embed
        embed = self.embed_from_rr(rr, msg.guild)
        await msg.edit(embed=embed)

        # Add all the reactions to the rr message
        await self.add_reactions(rr, msg)

        # Log and respond to the command
        log("Reaction-roles have been updated by", ctx.author)
        await ctx.respond("Les reaction-roles ont bien été actualisés.", ephemeral=True)


    @slash_command(name='resend-rr')
    async def resend_rr(self, ctx: ApplicationContext, rr: str, channel: TextChannel):
        """Owner seulement. Ré-envoie un reaction-role."""

        # Check if author is owner
        if ctx.author != ctx.guild.owner:
            ctx.respond("Vous n'avez pas les permissions requises pour effectuer cette commande...", ephemeral=True)
            return

        # Defer because process might take a while
        await ctx.defer(ephemeral=True)

        # Open the file to refresh the values in the variable reaction_roles
        with open('reaction_roles.json', encoding="utf-8") as file:
            global reaction_roles
            reaction_roles = json.load(file)

        try:
            rr = reaction_roles[rr]

            # Get the embed of the rr and send it
            embed = self.embed_from_rr(rr, channel.guild)
            msg = await channel.send(embed=embed)

            # Change the message id associated to the rr in the json data
            with open('reaction_roles.json', 'w') as file:
                rr["msg_id"] = msg.id
                json.dump(reaction_roles, file, indent=4)

            # Add all the reactions to the rr message
            await self.add_reactions(rr, msg)
            
            # Log and respond to the command
            log(f'The reaction-role "{rr}" has been sent in #{channel.name} by', ctx.author)
            await ctx.respond("Le reaction-role a bien été envoyé.", ephemeral=True)

        # If KeyError is raised then the name provided isn't valid
        except KeyError:
            await ctx.respond("Nom du reaction-role invalide...", ephemeral=True)



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



def setup(bot):
    bot.add_cog(ReactionRole(bot))
    print(" - ReactionRole")
