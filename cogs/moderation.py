from discord import Cog, ApplicationContext, Bot, Member, slash_command, option
from discord.utils import get
from my_utils import log

class Moderation(Cog):
    """Commandes de modération"""

    def __init__(self, bot):
        self.bot: Bot = bot


    @slash_command(name='kick')
    @option("member", description="Le membre à expulser")
    @option("reason", description="La raison de l'expulsion")
    async def kick_command(self, ctx: ApplicationContext, member: Member, reason: str = "Non précisée..."):
        """Expulser un membre"""

        # Check if author can't kick members and target is owner
        if not ctx.author.guild_permissions.kick_members or member == ctx.guild.owner:
            await ctx.respond("Vous n'avez pas les permissions requises pour effectuer cette commande !", ephemeral=True)
            return

        # Check if bot can kick the member
        bot = ctx.guild.get_member(self.bot.user.id)
        if member.top_role >= bot.top_role:
            await ctx.respond("Je ne peux pas expulser ce membre puisqu'il est plus haut gradé que moi...", ephemeral=True)
            return

        await member.kick(reason=reason)
        await ctx.respond(f"`{member}` a été expulsé du serveur par {ctx.author.mention} \nRaison : *{reason}*")
        log(member, "has been kicked by", ctx.author)


    @slash_command(name='ban')
    @option("member", description="Le membre à bannir")
    @option("reason", description="La raison du bannissement")
    async def kick(self, ctx: ApplicationContext, member: Member, reason: str = "Non précisée..."):
        """Bannir un membre"""

        # Check if author can't ban/unban members and target is owner
        if not ctx.author.guild_permissions.ban_members or member == ctx.guild.owner:
            await ctx.respond("Vous n'avez pas les permissions requises pour effectuer cette commande !", ephemeral=True)
            return

        # Check if bot can ban the member
        bot = ctx.guild.get_member(self.bot.user.id)
        if member.top_role >= bot.top_role:
            await ctx.respond("Je ne peux pas bannir ce membre puisqu'il est plus haut gradé que moi...", ephemeral=True)
            return

        await member.ban(reason=reason)
        await ctx.respond(f"`{member}` a été expulsé du serveur par {ctx.author.mention} \nRaison : *{reason}*")
        log(member, "has been banned by", ctx.author)


    @slash_command(name='unban')
    @option("member", description="Le pseudo et le tag du membre que vous voulez dé-bannir. Ex: Michel#3516")
    async def unban(self, ctx: ApplicationContext, member: str):
        """Révoquer le bannissement d'un membre"""

        # Check if author can't ban/unban members
        if not ctx.author.guild_permissions.ban_members:
            await ctx.respond("Vous n'avez pas les permissions requises pour effectuer cette commande !", ephemeral=True)
            return

        try:
            member_name, member_discriminator = member.split('#')
        except ValueError:
            await ctx.respond("Merci d'entrer un tag d'utilisateur valide (ex: Michel#3516)", ephemeral=True)
            return

        banned_users = await ctx.guild.bans()
        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                log(member, "has been unbanned by", ctx.author)
                await ctx.respond(f"{member} a été dé-banni par {ctx.author.mention}")
                return

        await ctx.respond(f"{member} n'est pas banni du serveur ou n'existe pas...", ephemeral=True)


    @slash_command(name='mute-text')
    @option("member", description="Le membre à rendre muet")
    @option("reason", description="La raison du mute")
    async def mute_text(self, ctx: ApplicationContext, member: Member, reason: str = "Non précisée..."):
        """Rendre muet un membre"""

        # Check if author can't manage messages and target is owner
        if not ctx.author.guild_permissions.manage_messages or member == ctx.guild.owner:
            await ctx.respond("Vous n'avez pas les permissions requises pour effectuer cette commande !", ephemeral=True)
            return

        # Check if bot can ban the member
        bot = ctx.guild.get_member(self.bot.user.id)
        if member.top_role >= bot.top_role:
            await ctx.respond("Je ne peux pas expulser ce membre puisqu'il est plus haut gradé que moi...", ephemeral=True)
            return
        
        # Check if guild has Muted role, if not then create it
        async def getMutedRole(guild):
            mutedRole = get(guild.roles, name="Muted")
            if not mutedRole:
                mutedRole = await guild.create_role(name="Muted")
                for channel in guild.channels:
                    await channel.set_permissions(mutedRole, send_messages=False)
            return mutedRole

        mutedRole = getMutedRole(ctx.guild)
        await member.add_roles(mutedRole)
        
        log(member, "has been text-muted by", ctx.author)
        ctx.respond(f"{member.mention} a été rendu muet par {ctx.author.mention} \nRaison : *{reason}*")


    @slash_command(name='clear')
    @option("number", description="Nombre de messages à supprimer entre 1 et 100", min_value=1, max_value=100)
    @option("member", decription="Spécifier un membre")
    async def clear_messages(self, ctx: ApplicationContext, number: int, member: Member = None):
        """Supprimer un certain nombre de messages ou d'un certain membre"""

        # Check if author can't manage messages or target is owner
        if not ctx.author.guild_permissions.manage_messages or member == ctx.guild.owner:
            await ctx.respond("Vous n'avez pas les permissions requises pour effectuer cette commande !", ephemeral=True)
            return

        # Define the check in case member is specified
        def checkMember(message):
            return message.author is member

        # Delete messages
        if member:
            await ctx.channel.purge(limit=number, check=checkMember)
            log(number, "messages from", member, "have been purged by", ctx.author)
            await ctx.respond(f"{number} messages envoyés par {member} ont été supprimé", ephemeral=True)
        else:
            await ctx.channel.purge(limit=number)
            log(number, "messages have been purged by", ctx.author)
            await ctx.respond(f"{number} messages ont été supprimé", ephemeral=True)



def setup(bot):
    bot.add_cog(Moderation(bot))
    print(' - Moderation')
